# 💎 Evolve Soluciones - Plataforma SaaS

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Flask](https://img.shields.io/badge/flask-3.0+-red.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)

**Sistema SaaS de gestión empresarial para consultorías y estudios contables**

[🚀 Demo](#) | [📖 Documentación](documentacion/CONVERSION_SAAS.md) | [💬 Soporte](#soporte)

</div>

---

## ✨ Características Principales

### 🎯 Modelo SaaS Completo

- ✅ **4 Planes de Suscripción**: Desde gratuito hasta empresarial
- ✅ **Facturación Automática**: Mensual o anual con descuentos
- ✅ **Período de Prueba**: 14 días sin tarjeta de crédito
- ✅ **Upgrade/Downgrade**: Cambio de plan en cualquier momento
- ✅ **Multi-Tenant**: Aislamiento completo de datos por cliente

### 💳 Pagos Integrados

- 🌍 **Stripe**: Pagos internacionales
- 🇨🇱 **MercadoPago**: Popular en Chile y LATAM
- 🔜 **Webpay**: Transbank Chile (próximamente)
- ✅ **Webhooks**: Procesamiento automático de pagos
- ✅ **Seguridad PCI**: Sin manejo directo de tarjetas

### 📊 Métricas de Negocio

- 💰 **MRR**: Monthly Recurring Revenue
- 📈 **ARR**: Annual Recurring Revenue
- 👥 **Clientes Activos**: En tiempo real
- 🔄 **Tasa de Conversión**: Trial → Pago
- 📉 **Churn**: Cancelaciones

### 🎨 Portal de Cliente

- 📱 **Dashboard Personal**: Gestión de suscripción
- 💳 **Métodos de Pago**: Administrar tarjetas
- 📄 **Historial de Pagos**: Facturas descargables
- 🔔 **Notificaciones**: Recordatorios de vencimiento
- 🆙 **Cambio de Plan**: Self-service

### 👨‍💼 Panel de Administración

- 📊 **Dashboard Ejecutivo**: KPIs en tiempo real
- 👥 **Gestión de Clientes**: Todos los tenants
- 💰 **Reportes Financieros**: Ingresos, proyecciones
- 🔍 **Analytics**: Segmentación por plan
- 🛠️ **Herramientas Admin**: Soporte y mantenimiento

---

## 💰 Planes y Precios

### 🆓 Plan Gratuito
**Gratis para siempre**

- 1 usuario
- 5 empresas
- 100 transacciones/mes
- Módulos básicos
- Sin soporte

### 📦 Plan Básico
**$29.990/mes** o **$299.900/año** (ahorra 17%)

- 3 usuarios
- 15 empresas
- 500 transacciones/mes
- 5 módulos
- Soporte email
- ✨ 14 días de prueba gratis

### ⭐ Plan Profesional (Recomendado)
**$59.990/mes** o **$599.900/año** (ahorra 17%)

- 10 usuarios
- 50 empresas
- 2.000 transacciones/mes
- 8 módulos
- Soporte prioritario
- Integraciones avanzadas
- ✨ 14 días de prueba gratis

### 🏢 Plan Empresarial
**$119.990/mes** o **$1.199.900/año** (ahorra 17%)

- Usuarios ilimitados
- Empresas ilimitadas
- Sin límite de transacciones
- Todos los módulos
- Soporte 24/7
- Gestor de cuenta dedicado
- SLA 99.9%
- ✨ 14 días de prueba gratis

---

## 🚀 Inicio Rápido

### Prerrequisitos

```bash
# Versiones requeridas
Python 3.8+
PostgreSQL 12+
MySQL 5.7+
```

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/evolve-soluciones.git
cd evolve-soluciones

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
pip install stripe mercadopago  # Pasarelas de pago

# 4. Configurar entorno
cp env.saas.ejemplo .env
# Editar .env con tus claves

# 5. Ejecutar migración
psql -U postgres -d evolve -f migraciones/010_sistema_suscripciones_saas.sql

# 6. Iniciar aplicación
python aplicacion.py
```

### Acceder al Sistema

- **Sitio público**: http://127.0.0.1:5000
- **Planes**: http://127.0.0.1:5000/suscripciones/planes
- **Dashboard admin**: http://127.0.0.1:5000/suscripciones/admin/dashboard

---

## 📖 Documentación

### Guías Principales

- 📘 [**Conversión a SaaS**](documentacion/CONVERSION_SAAS.md): Arquitectura completa
- ⚡ [**Guía Rápida**](documentacion/GUIA_RAPIDA_SAAS.md): Setup en 10 minutos
- 🔧 [**README Principal**](README.md): Sistema base

### Documentación Técnica

- [Modelos de Datos](aplicacion/modelos/)
- [Servicios](aplicacion/servicios/)
- [Controladores](aplicacion/controladores/)
- [Migraciones SQL](migraciones/)

---

## 🔧 Configuración

### Variables de Entorno Clave

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# MercadoPago
MERCADOPAGO_ACCESS_TOKEN=TEST-xxxxx
MERCADOPAGO_PUBLIC_KEY=TEST-xxxxx

# SaaS
SAAS_TRIAL_DAYS=14
SAAS_DEFAULT_PLAN=basico
SAAS_BASE_URL=https://tu-dominio.com
```

Ver archivo completo: [`env.saas.ejemplo`](env.saas.ejemplo)

### Webhooks

**Stripe:**
- URL: `https://tudominio.com/suscripciones/webhook/stripe`
- Eventos: checkout.session.completed, invoice.payment_succeeded

**MercadoPago:**
- URL: `https://tudominio.com/suscripciones/webhook/mercadopago`
- Eventos: payment

---

## 🧪 Testing

### Tarjetas de Prueba

**Stripe:**
```
Éxito:  4242 4242 4242 4242
Fallo:  4000 0000 0000 0002
CVV:    Cualquier 3 dígitos
Fecha:  Cualquier fecha futura
```

**MercadoPago:**
Ver [tarjetas oficiales de prueba](https://www.mercadopago.cl/developers/es/guides/online-payments/checkout-api/testing)

### Comandos de Test

```bash
# Tests unitarios (cuando estén disponibles)
pytest tests/

# Verificar migración
psql -U postgres -d evolve -c "SELECT * FROM auth.planes_suscripcion;"

# Calcular MRR
psql -U postgres -d evolve -c "SELECT auth.calcular_mrr();"
```

---

## 📊 Métricas y KPIs

### Consultas SQL Útiles

```sql
-- MRR total
SELECT auth.calcular_mrr();

-- Suscripciones activas
SELECT * FROM auth.vista_suscripciones_activas;

-- Distribución por plan
SELECT p.nombre, COUNT(s.id) as clientes
FROM auth.suscripciones s
JOIN auth.planes_suscripcion p ON s.id_plan = p.id
WHERE s.estado IN ('activa', 'periodo_prueba')
GROUP BY p.nombre;

-- Suscripciones por vencer (próximos 7 días)
SELECT * FROM auth.suscripciones
WHERE estado = 'activa'
  AND fecha_vencimiento BETWEEN NOW() AND NOW() + INTERVAL '7 days'
ORDER BY fecha_vencimiento;
```

---

## 🛠️ Stack Tecnológico

### Backend
- **Flask 3.0+**: Framework web
- **Python 3.8+**: Lenguaje principal
- **PostgreSQL 12+**: BD autenticación y suscripciones
- **MySQL 5.7+**: BD multi-tenant por cliente

### Frontend
- **Jinja2**: Template engine
- **Bootstrap 5**: UI framework
- **JavaScript ES6+**: Interactividad

### Integraciones
- **Stripe**: Pagos internacionales
- **MercadoPago**: Pagos LATAM
- **SendGrid/Mailgun**: Emails transaccionales

### DevOps
- **Gunicorn/Waitress**: WSGI server
- **Nginx**: Reverse proxy
- **Docker**: Containerización (opcional)

---

## 🚢 Despliegue

### Producción con Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 aplicacion:app
```

### Docker

```bash
docker build -t evolve-saas .
docker run -p 5000:5000 evolve-saas
```

### Nginx

```nginx
server {
    listen 80;
    server_name evolve-soluciones.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🗺️ Roadmap

### Q1 2025
- [ ] Landing page pública
- [ ] Onboarding automatizado
- [ ] Emails transaccionales
- [ ] Facturación electrónica (SII)
- [ ] Tests automatizados

### Q2 2025
- [ ] Programa de referidos
- [ ] Descuentos y cupones
- [ ] Multi-moneda
- [ ] API pública
- [ ] Mobile app

### Q3-Q4 2025
- [ ] IA para predicción de churn
- [ ] Marketplace de extensiones
- [ ] White label
- [ ] Expansión internacional
- [ ] Certificaciones (SOC 2, ISO)

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## 🆘 Soporte

### Canales de Soporte

- 📧 **Email**: soporte@evolve-soluciones.com
- 💬 **Chat**: [Slack Community](#)
- 📖 **Docs**: [Documentación completa](documentacion/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/tu-usuario/evolve-soluciones/issues)

### Horarios de Atención

- **Plan Básico**: Lun-Vie 9:00-18:00 (email)
- **Plan Profesional**: Lun-Vie 8:00-20:00 (email + chat)
- **Plan Empresarial**: 24/7 (email + chat + teléfono)

---

## 🙏 Agradecimientos

- Stripe por su excelente documentación
- MercadoPago por facilitar pagos en LATAM
- Comunidad Flask por el framework
- Todos los contribuidores del proyecto

---

## 📈 Estadísticas

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/tu-usuario/evolve-soluciones?style=social)
![GitHub forks](https://img.shields.io/github/forks/tu-usuario/evolve-soluciones?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/tu-usuario/evolve-soluciones?style=social)

</div>

---

<div align="center">

**Construido con ❤️ por el equipo de Evolve Soluciones**

[Website](#) • [Twitter](#) • [LinkedIn](#) • [YouTube](#)

</div>
