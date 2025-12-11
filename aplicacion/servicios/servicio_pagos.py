"""
Servicio de Pagos para Evolve Soluciones SaaS
==============================================

Gestiona integraciones con pasarelas de pago (Stripe, MercadoPago, Webpay).
"""

from typing import Optional, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod
import os


class PasarelaPagoBase(ABC):
    """Clase base abstracta para pasarelas de pago"""

    @abstractmethod
    def crear_sesion_checkout(self, datos_pago: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una sesión de checkout/pago"""
        pass

    @abstractmethod
    def procesar_webhook(self, datos_webhook: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa webhooks de la pasarela"""
        pass

    @abstractmethod
    def crear_suscripcion(self, datos_suscripcion: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una suscripción recurrente"""
        pass

    @abstractmethod
    def cancelar_suscripcion(self, id_suscripcion_externa: str) -> bool:
        """Cancela una suscripción"""
        pass

    @abstractmethod
    def obtener_estado_pago(self, id_transaccion_externa: str) -> Dict[str, Any]:
        """Obtiene el estado de un pago"""
        pass


class ServicioPagosStripe(PasarelaPagoBase):
    """Servicio de pagos con Stripe"""

    def __init__(self):
        """Inicializa el servicio de Stripe"""
        self.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.precio_producto_map = {}  # Mapeo de códigos de plan a IDs de precios en Stripe
        
        # Inicializar Stripe si está disponible
        try:
            import stripe
            stripe.api_key = self.api_key
            self.stripe = stripe
        except ImportError:
            print("WARNING: stripe no está instalado. Ejecutar: pip install stripe")
            self.stripe = None

    def crear_sesion_checkout(self, datos_pago: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una sesión de checkout en Stripe

        Args:
            datos_pago: Diccionario con:
                - id_plan: ID del plan
                - codigo_plan: Código del plan
                - periodo: 'mensual' o 'anual'
                - precio: Precio a cobrar
                - email_cliente: Email del cliente
                - id_base_datos: ID de la base de datos
                - success_url: URL de éxito
                - cancel_url: URL de cancelación

        Returns:
            Dict con url de checkout y session_id
        """
        if not self.stripe:
            raise Exception("Stripe no está configurado")

        try:
            session = self.stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'clp',
                        'unit_amount': int(datos_pago['precio'] * 100),  # Stripe usa centavos
                        'product_data': {
                            'name': f"Plan {datos_pago['codigo_plan'].title()}",
                            'description': f"Suscripción {datos_pago['periodo']}",
                        },
                        'recurring': {
                            'interval': 'month' if datos_pago['periodo'] == 'mensual' else 'year',
                        } if datos_pago.get('recurrente', True) else None,
                    },
                    'quantity': 1,
                }],
                mode='subscription' if datos_pago.get('recurrente', True) else 'payment',
                success_url=datos_pago['success_url'],
                cancel_url=datos_pago['cancel_url'],
                customer_email=datos_pago.get('email_cliente'),
                metadata={
                    'id_plan': str(datos_pago['id_plan']),
                    'id_base_datos': str(datos_pago['id_base_datos']),
                    'periodo': datos_pago['periodo'],
                }
            )

            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id,
                'pasarela': 'stripe'
            }

        except Exception as e:
            print(f"Error creando sesión de checkout en Stripe: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def procesar_webhook(self, datos_webhook: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa webhooks de Stripe

        Args:
            datos_webhook: Payload del webhook y headers

        Returns:
            Dict con resultado del procesamiento
        """
        if not self.stripe:
            raise Exception("Stripe no está configurado")

        try:
            payload = datos_webhook.get('payload')
            sig_header = datos_webhook.get('signature')

            # Verificar firma del webhook
            event = self.stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            # Procesar según tipo de evento
            if event['type'] == 'checkout.session.completed':
                return self._procesar_checkout_completado(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_succeeded':
                return self._procesar_pago_exitoso(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_failed':
                return self._procesar_pago_fallido(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.deleted':
                return self._procesar_suscripcion_cancelada(event['data']['object'])

            return {'success': True, 'procesado': False, 'tipo': event['type']}

        except Exception as e:
            print(f"Error procesando webhook de Stripe: {e}")
            return {'success': False, 'error': str(e)}

    def _procesar_checkout_completado(self, session: Any) -> Dict[str, Any]:
        """Procesa checkout completado"""
        from aplicacion.modelos.suscripcion import Suscripcion

        try:
            metadata = session.get('metadata', {})
            id_base_datos = int(metadata.get('id_base_datos'))
            id_plan = int(metadata.get('id_plan'))
            
            # Crear o actualizar suscripción
            suscripcion = Suscripcion.crear_suscripcion(
                id_base_datos=id_base_datos,
                id_plan=id_plan,
                periodo=metadata.get('periodo', 'mensual'),
                metodo_pago='stripe',
                en_periodo_prueba=False
            )

            # Registrar transacción
            self._registrar_transaccion(
                id_suscripcion=suscripcion.id,
                tipo='pago_mensual' if metadata.get('periodo') == 'mensual' else 'pago_anual',
                monto=session.amount_total / 100,
                estado='completada',
                id_externo=session.id
            )

            return {
                'success': True,
                'procesado': True,
                'id_suscripcion': suscripcion.id
            }

        except Exception as e:
            print(f"Error procesando checkout completado: {e}")
            return {'success': False, 'error': str(e)}

    def _procesar_pago_exitoso(self, invoice: Any) -> Dict[str, Any]:
        """Procesa pago exitoso (renovación)"""
        from aplicacion.modelos.suscripcion import Suscripcion

        try:
            # Buscar suscripción por ID de Stripe
            subscription_id = invoice.get('subscription')
            
            # Aquí deberías buscar la suscripción en tu BD que tenga este ID externo
            # Por ahora retornamos éxito
            
            return {
                'success': True,
                'procesado': True,
                'tipo': 'renovacion'
            }

        except Exception as e:
            print(f"Error procesando pago exitoso: {e}")
            return {'success': False, 'error': str(e)}

    def _procesar_pago_fallido(self, invoice: Any) -> Dict[str, Any]:
        """Procesa pago fallido"""
        # Implementar lógica de pago fallido (suspender cuenta, enviar notificación)
        return {'success': True, 'procesado': True, 'tipo': 'pago_fallido'}

    def _procesar_suscripcion_cancelada(self, subscription: Any) -> Dict[str, Any]:
        """Procesa cancelación de suscripción"""
        # Implementar lógica de cancelación
        return {'success': True, 'procesado': True, 'tipo': 'cancelacion'}

    def _registrar_transaccion(self, id_suscripcion: int, tipo: str, monto: float,
                              estado: str, id_externo: str):
        """Registra una transacción en la base de datos"""
        from aplicacion.modelos.base_datos import ejecutar_insercion_postgres

        try:
            consulta = """
                INSERT INTO auth.transacciones
                (id_suscripcion, tipo, estado, monto, moneda, metodo_pago,
                 pasarela_pago, id_externo_transaccion, fecha_transaccion,
                 fecha_completada, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            ejecutar_insercion_postgres(
                consulta,
                (id_suscripcion, tipo, estado, monto, 'CLP', 'stripe',
                 'stripe', id_externo, datetime.now(), datetime.now(), datetime.now())
            )
        except Exception as e:
            print(f"Error registrando transacción: {e}")

    def crear_suscripcion(self, datos_suscripcion: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una suscripción recurrente en Stripe"""
        if not self.stripe:
            raise Exception("Stripe no está configurado")

        try:
            # Crear o recuperar cliente
            customer = self.stripe.Customer.create(
                email=datos_suscripcion['email_cliente'],
                metadata={
                    'id_base_datos': str(datos_suscripcion['id_base_datos'])
                }
            )

            # Crear suscripción
            subscription = self.stripe.Subscription.create(
                customer=customer.id,
                items=[{
                    'price': datos_suscripcion['price_id'],
                }],
                metadata={
                    'id_plan': str(datos_suscripcion['id_plan']),
                    'id_base_datos': str(datos_suscripcion['id_base_datos']),
                }
            )

            return {
                'success': True,
                'subscription_id': subscription.id,
                'customer_id': customer.id
            }

        except Exception as e:
            print(f"Error creando suscripción en Stripe: {e}")
            return {'success': False, 'error': str(e)}

    def cancelar_suscripcion(self, id_suscripcion_externa: str) -> bool:
        """Cancela una suscripción en Stripe"""
        if not self.stripe:
            raise Exception("Stripe no está configurado")

        try:
            self.stripe.Subscription.delete(id_suscripcion_externa)
            return True
        except Exception as e:
            print(f"Error cancelando suscripción en Stripe: {e}")
            return False

    def obtener_estado_pago(self, id_transaccion_externa: str) -> Dict[str, Any]:
        """Obtiene el estado de un pago en Stripe"""
        if not self.stripe:
            raise Exception("Stripe no está configurado")

        try:
            session = self.stripe.checkout.Session.retrieve(id_transaccion_externa)
            return {
                'success': True,
                'estado': session.payment_status,
                'id_pago': session.payment_intent
            }
        except Exception as e:
            print(f"Error obteniendo estado de pago: {e}")
            return {'success': False, 'error': str(e)}


class ServicioPagosMercadoPago(PasarelaPagoBase):
    """Servicio de pagos con MercadoPago (popular en Chile/Latinoamérica)"""

    def __init__(self):
        """Inicializa el servicio de MercadoPago"""
        self.access_token = os.getenv('MERCADOPAGO_ACCESS_TOKEN')
        self.public_key = os.getenv('MERCADOPAGO_PUBLIC_KEY')
        
        # Inicializar SDK de MercadoPago si está disponible
        try:
            import mercadopago
            self.sdk = mercadopago.SDK(self.access_token)
        except ImportError:
            print("WARNING: mercadopago no está instalado. Ejecutar: pip install mercadopago")
            self.sdk = None

    def crear_sesion_checkout(self, datos_pago: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una preferencia de pago en MercadoPago"""
        if not self.sdk:
            raise Exception("MercadoPago no está configurado")

        try:
            preference_data = {
                "items": [
                    {
                        "title": f"Plan {datos_pago['codigo_plan'].title()}",
                        "quantity": 1,
                        "unit_price": float(datos_pago['precio']),
                        "currency_id": "CLP"
                    }
                ],
                "back_urls": {
                    "success": datos_pago['success_url'],
                    "failure": datos_pago['cancel_url'],
                    "pending": datos_pago['cancel_url']
                },
                "auto_return": "approved",
                "external_reference": f"{datos_pago['id_base_datos']}-{datos_pago['id_plan']}",
                "metadata": {
                    "id_plan": datos_pago['id_plan'],
                    "id_base_datos": datos_pago['id_base_datos'],
                    "periodo": datos_pago['periodo']
                }
            }

            preference_response = self.sdk.preference().create(preference_data)
            preference = preference_response["response"]

            return {
                'success': True,
                'checkout_url': preference["init_point"],
                'preference_id': preference["id"],
                'pasarela': 'mercadopago'
            }

        except Exception as e:
            print(f"Error creando preferencia en MercadoPago: {e}")
            return {'success': False, 'error': str(e)}

    def procesar_webhook(self, datos_webhook: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa webhooks de MercadoPago"""
        # Implementar según documentación de MercadoPago
        return {'success': True, 'procesado': False}

    def crear_suscripcion(self, datos_suscripcion: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una suscripción en MercadoPago"""
        # MercadoPago maneja suscripciones de forma diferente
        return {'success': False, 'error': 'No implementado'}

    def cancelar_suscripcion(self, id_suscripcion_externa: str) -> bool:
        """Cancela una suscripción en MercadoPago"""
        return False

    def obtener_estado_pago(self, id_transaccion_externa: str) -> Dict[str, Any]:
        """Obtiene el estado de un pago en MercadoPago"""
        if not self.sdk:
            raise Exception("MercadoPago no está configurado")

        try:
            payment = self.sdk.payment().get(id_transaccion_externa)
            return {
                'success': True,
                'estado': payment["response"]["status"],
                'id_pago': id_transaccion_externa
            }
        except Exception as e:
            print(f"Error obteniendo estado de pago: {e}")
            return {'success': False, 'error': str(e)}


class ServicioPagos:
    """Servicio principal de pagos (fachada)"""

    def __init__(self, pasarela: str = 'stripe'):
        """
        Inicializa el servicio de pagos

        Args:
            pasarela: Nombre de la pasarela ('stripe', 'mercadopago', 'webpay')
        """
        self.pasarela = pasarela.lower()
        
        if self.pasarela == 'stripe':
            self.proveedor = ServicioPagosStripe()
        elif self.pasarela == 'mercadopago':
            self.proveedor = ServicioPagosMercadoPago()
        else:
            raise ValueError(f"Pasarela '{pasarela}' no soportada")

    def crear_checkout(self, id_plan: int, id_base_datos: int, periodo: str = 'mensual',
                      email_cliente: str = None, success_url: str = None,
                      cancel_url: str = None) -> Dict[str, Any]:
        """
        Crea una sesión de checkout

        Args:
            id_plan: ID del plan
            id_base_datos: ID de la base de datos
            periodo: 'mensual' o 'anual'
            email_cliente: Email del cliente
            success_url: URL de éxito
            cancel_url: URL de cancelación

        Returns:
            Dict con URL de checkout
        """
        from aplicacion.modelos.plan import Plan

        try:
            # Obtener información del plan
            plan = Plan.obtener_por_id(id_plan)
            if not plan:
                return {'success': False, 'error': 'Plan no encontrado'}

            # Calcular precio según período
            precio = plan.precio_mensual if periodo == 'mensual' else plan.precio_anual

            # Preparar datos del pago
            datos_pago = {
                'id_plan': id_plan,
                'codigo_plan': plan.codigo,
                'periodo': periodo,
                'precio': precio,
                'email_cliente': email_cliente,
                'id_base_datos': id_base_datos,
                'success_url': success_url,
                'cancel_url': cancel_url,
                'recurrente': True
            }

            return self.proveedor.crear_sesion_checkout(datos_pago)

        except Exception as e:
            print(f"Error creando checkout: {e}")
            return {'success': False, 'error': str(e)}

    def procesar_webhook(self, payload: Any, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Procesa webhooks de la pasarela de pago

        Args:
            payload: Cuerpo del webhook
            headers: Headers del webhook

        Returns:
            Dict con resultado del procesamiento
        """
        datos_webhook = {
            'payload': payload,
            'signature': headers.get('stripe-signature') or headers.get('x-signature')
        }
        return self.proveedor.procesar_webhook(datos_webhook)
