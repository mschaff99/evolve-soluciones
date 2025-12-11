# 🚀 Guía Rápida - Configuración SaaS

## ⏱️ Configuración en 10 Minutos

Esta guía te ayudará a poner en funcionamiento el sistema SaaS de Evolve Soluciones rápidamente.

---

## 📋 Prerrequisitos

- Python 3.8+
- PostgreSQL 12+
- MySQL 5.7+
- Cuenta en Stripe o MercadoPago (modo test)

---

## 🔧 Paso 1: Instalar Dependencias

```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias de pago
pip install stripe mercadopago
```

---

## 🗄️ Paso 2: Ejecutar Migración de Base de Datos

```bash
# Conectar a PostgreSQL
psql -U postgres -d evolve

# Ejecutar migración
\i migraciones/010_sistema_suscripciones_saas.sql

# Verificar creación de tablas
\dt auth.*
```

**Tablas creadas:**
- `auth.planes_suscripcion`
- `auth.modulos_plan`
- `auth.suscripciones`
- `auth.transacciones`
- `auth.metodos_pago`

---

## 🔑 Paso 3: Configurar Claves de API

### Opción A: Stripe (Recomendado para Internacional)

1. Crear cuenta en [Stripe](https://dashboard.stripe.com/register)
2. Obtener claves de API (modo test):
   - Dashboard → Developers → API keys
3. Agregar al archivo `.env`:

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_51xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_51xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

### Opción B: MercadoPago (Para Chile/LATAM)

1. Crear cuenta en [MercadoPago Developers](https://www.mercadopago.cl/developers)
2. Obtener credenciales de test:
   - Tus integraciones → Credenciales
3. Agregar al archivo `.env`:

```env
# MercadoPago
MERCADOPAGO_ACCESS_TOKEN=TEST-xxxxx
MERCADOPAGO_PUBLIC_KEY=TEST-xxxxx
```

---

## 🎬 Paso 4: Iniciar Aplicación

```bash
python aplicacion.py
```

**URLs importantes:**
- Principal: `http://127.0.0.1:5000`
- Planes: `http://127.0.0.1:5000/suscripciones/planes`
- Mi Suscripción: `http://127.0.0.1:5000/suscripciones/mi-suscripcion`
- Admin Dashboard: `http://127.0.0.1:5000/suscripciones/admin/dashboard`

---

## 🧪 Paso 5: Probar el Sistema

### Verificar Planes

```python
# En Python shell
from aplicacion.modelos.plan import Plan

# Listar planes
planes = Plan.obtener_planes_activos()
for plan in planes:
    print(f"{plan.nombre}: ${plan.precio_mensual}")
```

### Crear Checkout de Prueba

1. Navegar a `/suscripciones/planes`
2. Seleccionar un plan
3. Hacer clic en "Comenzar Ahora"
4. Usar tarjetas de prueba:

**Stripe:**
- Éxito: `4242 4242 4242 4242`
- Fallo: `4000 0000 0000 0002`
- CVV: cualquier 3 dígitos
- Fecha: cualquier fecha futura

**MercadoPago:**
- Ver [tarjetas de prueba](https://www.mercadopago.cl/developers/es/guides/online-payments/checkout-api/testing)

---

## 🔗 Paso 6: Configurar Webhooks (Modo Test)

### Usar Ngrok para Desarrollo Local

```bash
# Instalar ngrok
npm install -g ngrok
# o descargar de https://ngrok.com

# Exponer puerto local
ngrok http 5000
```

**Copiar URL pública** (ej: `https://abc123.ngrok.io`)

### Stripe Webhooks

1. Dashboard → Developers → Webhooks
2. Add endpoint: `https://abc123.ngrok.io/suscripciones/webhook/stripe`
3. Seleccionar eventos:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
4. Copiar **Signing secret** al `.env`

### MercadoPago Webhooks

1. Dashboard → Webhooks
2. URL: `https://abc123.ngrok.io/suscripciones/webhook/mercadopago`
3. Eventos: Pagos

---

## 📊 Paso 7: Verificar Funcionamiento

### Consultar MRR

```sql
-- En PostgreSQL
SELECT auth.calcular_mrr() as mrr_total;
```

### Ver Suscripciones Activas

```sql
SELECT * FROM auth.vista_suscripciones_activas;
```

### Acceder al Panel Admin

1. Iniciar sesión como administrador
2. Ir a `/suscripciones/admin/dashboard`
3. Ver métricas:
   - MRR total
   - Suscripciones activas
   - Distribución por plan

---

## 🐛 Solución de Problemas

### Error: "Stripe no está configurado"

**Causa**: No se instaló la librería o no están las claves en `.env`

**Solución**:
```bash
pip install stripe
# Verificar .env tiene STRIPE_SECRET_KEY
```

### Error: "Plan no encontrado"

**Causa**: No se ejecutó la migración correctamente

**Solución**:
```sql
-- Verificar planes
SELECT * FROM auth.planes_suscripcion;

-- Si está vacío, ejecutar migración nuevamente
\i migraciones/010_sistema_suscripciones_saas.sql
```

### Webhooks no funcionan

**Causa**: URL no es accesible públicamente o webhook secret incorrecto

**Solución**:
1. Usar ngrok para desarrollo local
2. Verificar que el webhook secret en `.env` sea correcto
3. Ver logs de Flask para errores

---

## 📝 Siguientes Pasos

Una vez funcionando:

1. **Personalizar Planes**: Editar precios y características en la BD
2. **Configurar Emails**: Setup SendGrid/Mailgun para notificaciones
3. **Crear Landing Page**: Página pública de marketing
4. **Configurar DNS**: Dominio propio para producción
5. **SSL/HTTPS**: Certificado para producción (Let's Encrypt)
6. **Monitoring**: Configurar Sentry para errores

---

## 🆘 ¿Necesitas Ayuda?

- **Documentación Completa**: `/documentacion/CONVERSION_SAAS.md`
- **Email**: soporte@evolve-soluciones.com
- **Issues**: GitHub Issues del repositorio

---

## ✅ Checklist de Configuración

- [ ] Dependencias instaladas (stripe/mercadopago)
- [ ] Migración ejecutada
- [ ] Variables de entorno configuradas
- [ ] Aplicación iniciada
- [ ] Planes visibles en `/suscripciones/planes`
- [ ] Checkout funcionando (modo test)
- [ ] Webhooks configurados
- [ ] MRR calculándose correctamente
- [ ] Panel admin accesible

---

**¡Listo!** 🎉 Ahora tienes un sistema SaaS funcional.

Para pasar a producción, revisa la sección de **Deployment** en `CONVERSION_SAAS.md`.
