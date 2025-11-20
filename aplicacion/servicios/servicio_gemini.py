"""
Servicio para integración con Google Gemini AI
Maneja la comunicación con la API de Gemini para análisis de balances
"""

import requests
import json
from typing import Dict, List, Any, Optional
from configuracion.configuracion import ConfiguracionBase as Config


class GeminiService:
    """Servicio para interactuar con Google Gemini AI"""

    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model = Config.GEMINI_MODEL
        self.base_url = Config.GEMINI_API_URL
        self.headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': self.api_key
        }

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno")

    def test_connection(self) -> Dict[str, Any]:
        """Probar la conexión con Gemini AI"""
        try:
            response = self._generate_content("Responde solo con 'OK' si puedes leerme")

            if response.get('success'):
                return {
                    'success': True,
                    'message': 'Conexión exitosa con Gemini AI',
                    'response': response.get('content', '')
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Error desconocido')
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error al conectar con Gemini: {str(e)}'
            }

    def analyze_balance(self, balance_data: Dict[str, Any], analysis_type: str = 'complete') -> Dict[str, Any]:
        """
        Analizar balance de 8 columnas usando Gemini AI

        Args:
            balance_data: Datos del balance en formato estructurado
            analysis_type: Tipo de análisis ('basic', 'complete', 'ratios')

        Returns:
            Dict con el análisis de Gemini
        """
        try:
            # Construir prompt específico para análisis de balance
            prompt = self._build_balance_prompt(balance_data, analysis_type)

            # Enviar a Gemini
            response = self._generate_content(prompt)

            if response.get('success'):
                return {
                    'success': True,
                    'analysis': response.get('content'),
                    'balance_data': balance_data,
                    'analysis_type': analysis_type
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Error en análisis')
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error al analizar balance: {str(e)}'
            }

    def _build_balance_prompt(self, balance_data: Dict[str, Any], analysis_type: str) -> str:
        """Construir prompt específico para análisis de balance"""

        # Información básica del balance
        empresa_info = balance_data.get('empresa_info', {})
        periodo = balance_data.get('periodo', 'No especificado')
        cuentas = balance_data.get('cuentas', [])

        # Prompt profesional mejorado
        prompt = f"""
Actúa como un analista contable profesional con experiencia en balances de 8 columnas bajo normativa contable chilena (PCGA y NIIF PYMEs). A continuación, recibirás un balance en formato JSON. Tu tarea es realizar un análisis contable completo, con las siguientes indicaciones:

INFORMACIÓN DE LA EMPRESA:
- Empresa: {empresa_info.get('nombre', 'No especificado')}
- RUT: {empresa_info.get('rut', 'No especificado')}
- Período: {periodo}

DATOS DEL BALANCE EN JSON:
"""

        # Agregar datos de las cuentas en formato estructurado
        if cuentas:
            prompt += "\n```json\n{\n  \"cuentas\": [\n"
            for i, cuenta in enumerate(cuentas):
                prompt += f"    {{\n"
                prompt += f"      \"codigo\": \"{cuenta.get('codigo', '')}\",\n"
                prompt += f"      \"nombre\": \"{cuenta.get('nombre', '')}\",\n"
                prompt += f"      \"tipo\": \"{cuenta.get('tipo', '')}\",\n"
                prompt += f"      \"saldo_inicial_deudor\": {cuenta.get('saldo_inicial_deudor', 0)},\n"
                prompt += f"      \"saldo_inicial_acreedor\": {cuenta.get('saldo_inicial_acreedor', 0)},\n"
                prompt += f"      \"movimiento_debitos\": {cuenta.get('movimiento_debitos', 0)},\n"
                prompt += f"      \"movimiento_creditos\": {cuenta.get('movimiento_creditos', 0)},\n"
                prompt += f"      \"saldo_final_activos\": {cuenta.get('saldo_final_activos', 0)},\n"
                prompt += f"      \"saldo_final_pasivos\": {cuenta.get('saldo_final_pasivos', 0)},\n"
                prompt += f"      \"pg_perdida\": {cuenta.get('pg_perdida', 0)},\n"
                prompt += f"      \"pg_ganancia\": {cuenta.get('pg_ganancia', 0)}\n"
                prompt += f"    }}"
                if i < len(cuentas) - 1:
                    prompt += ","
                prompt += "\n"
            prompt += "  ]\n}\n```\n"

        # Instrucciones detalladas de análisis
        prompt += """
---

🔹 **1. Análisis cuenta por cuenta (orden contable)**

Analiza **cada cuenta individualmente**, en el siguiente orden:

- Activos
- Pasivos
- Patrimonio
- Ingresos
- Gastos

Para cada cuenta, entrega la siguiente información:

### Cuenta: [Nombre de la cuenta]
- **Código:** [Número de cuenta]
- **Tipo:** Activo / Pasivo / Patrimonio / Ingreso / Gasto
- **Saldos Iniciales:** Deudor: $ / Acreedor: $
- **Movimientos:** Débitos: $ / Créditos: $
- **Saldo Final:** $
- **Análisis Técnico:** Comenta si los movimientos son coherentes, si hay inactividad, desbalance, acumulación o comportamiento irregular según el tipo de cuenta.
- **Observación Profesional:** Normal / Inactiva / Destacable / Inconsistente / Requiere revisión

---

🔹 **2. Análisis por áreas funcionales del negocio**

Agrupa luego las cuentas en **sectores funcionales clave del negocio**, e incluye un resumen técnico para cada uno:

- **Ventas** (Ingresos, clientes, cuentas por cobrar)
- **Compras** (Proveedores, IVA crédito, cuentas por pagar)
- **Remuneraciones** (Sueldos, leyes sociales, honorarios)
- **Gastos operacionales** (Fletes, combustibles, asesorías, generales)
- **Inversiones** (Activos fijos, empresas relacionadas, obras en construcción)
- **Financiamiento y patrimonio** (Capital, aportes, cuentas por pagar largo plazo)
- **Resultado del ejercicio**

Para cada sector, incluye:
- Cuentas incluidas
- Comentario sobre su comportamiento conjunto
- Coherencia entre cuentas relacionadas
- Riesgos contables detectados
- Recomendación general

---

🔹 **3. Resumen ejecutivo final**

Incluye una conclusión final con:
- Principales puntos fuertes del balance
- Riesgos contables o inconsistencias detectadas
- Recomendaciones para el equipo contable o gerencia
- Opinión profesional general sobre la estructura del balance

---

**Formato de salida**: Usa subtítulos y secciones claramente identificadas para facilitar su lectura. Respeta el orden contable: primero activos, luego pasivos, y así sucesivamente.

Por favor proporciona un análisis profesional, preciso y útil para la toma de decisiones empresariales.
"""

        return prompt

    def _generate_content(self, prompt: str) -> Dict[str, Any]:
        """Enviar prompt a Gemini y obtener respuesta"""
        try:
            url = f"{self.base_url}/{self.model}:generateContent"

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }

            print(f"🤖 Enviando request a Gemini: {url}")

            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=Config.GEMINI_TIMEOUT  # Usar timeout configurable
            )

            print(f"📡 Response status: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()

                # Extraer contenido de la respuesta de Gemini
                content = ""
                if 'candidates' in response_data and len(response_data['candidates']) > 0:
                    candidate = response_data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        if len(parts) > 0 and 'text' in parts[0]:
                            content = parts[0]['text']

                return {
                    'success': True,
                    'content': content,
                    'raw_response': response_data
                }
            else:
                error_msg = f"Error HTTP {response.status_code}: {response.text}"
                print(f"Error en Gemini: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': f'Timeout al conectar con Gemini AI (límite: {Config.GEMINI_TIMEOUT}s). La empresa puede tener muchas cuentas para analizar.'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Error de conexión con Gemini AI'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error inesperado: {str(e)}'
            }


# Crear instancia singleton del servicio
gemini_service = GeminiService()
# Instancia global del servicio
gemini_service = GeminiService()
