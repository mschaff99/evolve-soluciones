# Analisis Arquitectonico: Migracion a React + FastAPI con Pasarela de Pago

## Fecha: 2026-02-16
## Proyecto: Evolve Soluciones - Plataforma de Inteligencia Tributaria

---

## 1. DIAGNOSTICO DE LA ARQUITECTURA ACTUAL

### 1.1 Estado Actual

| Aspecto | Detalle |
|---------|---------|
| **Framework** | Flask 2.3.3 (Python) |
| **Patron** | MVC Monolitico con capa de servicios |
| **Frontend** | Jinja2 + Bootstrap 5 + Vanilla JS (SSR) |
| **Bases de datos** | PostgreSQL (auth) + MySQL local (operacional) + MySQL remoto (consolidaciones) + MongoDB (archivos) |
| **Lineas de codigo Python** | ~17,500 |
| **Templates HTML** | 16 archivos (~4,400 lineas) |
| **Archivos JS** | 11 archivos |
| **Controladores** | 8 blueprints |
| **Servicios** | 10+ servicios de logica de negocio |
| **Modelos** | 5 modelos principales |
| **Migraciones SQL** | 10 archivos |
| **Scripts utilitarios** | 30 archivos |

### 1.2 Fortalezas del Sistema Actual

1. **Separacion de capas clara**: Controladores -> Servicios -> Modelos bien definidos
2. **Multi-tenancy robusto**: Sistema de bases de datos MySQL por cliente
3. **Sistema de permisos granular**: Modulos habilitados por BD + roles por usuario
4. **Seguridad solida**: Sesiones unicas, CSRF, bcrypt, logging de IPs
5. **Integracion IA funcional**: Gemini AI para analisis de balances
6. **Decoradores reutilizables**: 10+ decoradores para auth, validacion, errores

### 1.3 Debilidades y Deuda Tecnica

1. **Frontend acoplado al backend**: Jinja2 impide reutilizar UI independientemente
2. **Sin API REST formal**: Las rutas mezclan renderizado HTML con respuestas JSON
3. **JS vanilla fragmentado**: 11 archivos sin bundling ni estado compartido
4. **Sin pasarela de pago**: No hay monetizacion integrada
5. **Sin tests automatizados**: No se encontraron archivos de test
6. **Commits sin estructura**: Mensajes como "new", "cambios" dificultan trazabilidad
7. **Sin CI/CD formal**: No hay pipeline de integracion continua
8. **Sin documentacion de API**: No hay OpenAPI/Swagger
9. **Flask sincrono**: Limitado para operaciones I/O intensivas (consultas IA, scraping SII)

---

## 2. ANALISIS DE ARQUITECTURAS CANDIDATAS

### 2.1 Opcion A: Microservicios Puros

```
                    [API Gateway / Nginx]
                           |
    +-----------+----------+----------+-----------+
    |           |          |          |           |
[Auth Svc]  [Empresas] [Tributario] [IA Svc]  [Pagos]
 (FastAPI)  (FastAPI)   (FastAPI)   (FastAPI)  (FastAPI)
    |           |          |          |           |
[PostgreSQL] [MySQL]   [MySQL]    [Gemini]   [Stripe]
                                  [MongoDB]
```

**Ventajas:**
- Escalado independiente por servicio
- Deploy independiente
- Aislamiento de fallos
- Tecnologia heterogenea posible

**Desventajas:**
- Complejidad operacional ALTA para un equipo pequeno
- Necesita: service discovery, circuit breakers, distributed tracing
- Comunicacion inter-servicio anade latencia
- Consistencia eventual entre bases de datos
- Requiere Kubernetes o similar para orquestacion
- Overhead de infraestructura: cada servicio necesita su propio CI/CD, monitoreo, logging

**Evaluacion: NO RECOMENDADO como punto de partida.**
Con ~17,500 lineas de codigo y un equipo presumiblemente pequeno, los microservicios puros introducirian mas complejidad de la que resolverian.

### 2.2 Opcion B: Monolito Modular (Recomendado como Fase 1)

```
                [Nginx / Reverse Proxy]
                    |              |
            [React SPA]      [FastAPI Backend]
            (puerto 3000)    (puerto 8000)
                                  |
                    +-------------+-------------+
                    |             |             |
              [Modulo Auth] [Modulo Core] [Modulo Pagos]
                    |             |             |
              [PostgreSQL]    [MySQL]      [Stripe/MP]
                            [MongoDB]
```

**Ventajas:**
- Simplicidad operacional: un solo deploy de backend
- Separacion clara frontend/backend via API REST
- Facilidad para agregar modulos (como pasarela de pago)
- FastAPI genera OpenAPI/Swagger automaticamente
- Soporte nativo async para operaciones I/O (Gemini, SII, DBs)
- Un solo repositorio, un solo pipeline CI/CD
- Facil evolucion futura hacia microservicios si es necesario

**Desventajas:**
- Menos aislamiento de fallos que microservicios
- Escalado es todo-o-nada (pero suficiente para el volumen actual)

**Evaluacion: RECOMENDADO. Mejor relacion costo-beneficio.**

### 2.3 Opcion C: Microservicios Ligeros (Fase 2 - Futuro)

```
                    [API Gateway / Nginx]
                           |
            +--------------+--------------+
            |              |              |
     [Core API]      [IA Service]   [Payment Service]
      (FastAPI)       (FastAPI)       (FastAPI)
         |                |              |
   [PostgreSQL]     [Gemini API]    [Stripe/MP]
   [MySQL x N]      [MongoDB]
```

Extraer SOLO los servicios que justifican separacion:
- **Servicio IA**: Procesamiento pesado, timeouts largos, escalado independiente
- **Servicio Pagos**: Aislamiento de seguridad PCI-DSS, disponibilidad critica

**Evaluacion: IDEAL como evolucion futura (6-12 meses despues de Fase 1)**

---

## 3. RECOMENDACION: ARQUITECTURA EVOLUTIVA EN 3 FASES

### FASE 1: Monolito Modular (React + FastAPI) - Meses 1-3

#### 3.1 Estructura Propuesta del Backend (FastAPI)

```
evolve-backend/
|-- app/
|   |-- main.py                    # FastAPI app factory
|   |-- core/
|   |   |-- config.py              # Pydantic Settings
|   |   |-- security.py            # JWT + bcrypt
|   |   |-- database.py            # Conexiones async (asyncpg, aiomysql)
|   |   |-- dependencies.py        # Dependency injection
|   |   |-- middleware.py           # CORS, logging, rate limiting
|   |   +-- exceptions.py          # Excepciones personalizadas
|   |
|   |-- modules/
|   |   |-- auth/
|   |   |   |-- router.py          # Endpoints de autenticacion
|   |   |   |-- schemas.py         # Pydantic models (request/response)
|   |   |   |-- service.py         # Logica de negocio
|   |   |   |-- models.py          # SQLAlchemy models
|   |   |   +-- dependencies.py    # Auth dependencies
|   |   |
|   |   |-- empresas/
|   |   |   |-- router.py
|   |   |   |-- schemas.py
|   |   |   |-- service.py
|   |   |   +-- models.py
|   |   |
|   |   |-- tributario/
|   |   |   |-- f29/
|   |   |   |   |-- router.py
|   |   |   |   |-- schemas.py
|   |   |   |   +-- service.py
|   |   |   |-- dj/
|   |   |   |   |-- router.py
|   |   |   |   |-- schemas.py
|   |   |   |   +-- service.py
|   |   |   +-- situacion/
|   |   |       |-- router.py
|   |   |       |-- schemas.py
|   |   |       +-- service.py
|   |   |
|   |   |-- ia/
|   |   |   |-- router.py
|   |   |   |-- schemas.py
|   |   |   |-- service.py         # Gemini integration
|   |   |   +-- prompts/           # AI prompts
|   |   |
|   |   |-- pagos/                 # NUEVO: Pasarela de pago
|   |   |   |-- router.py
|   |   |   |-- schemas.py
|   |   |   |-- service.py
|   |   |   |-- models.py
|   |   |   +-- webhooks.py        # Stripe/MP webhooks
|   |   |
|   |   +-- erp/
|   |       |-- router.py
|   |       |-- schemas.py
|   |       +-- service.py
|   |
|   |-- migrations/                # Alembic migrations
|   +-- tests/                     # Pytest tests
|
|-- requirements.txt
|-- Dockerfile
|-- docker-compose.yml
+-- alembic.ini
```

#### 3.2 Estructura Propuesta del Frontend (React)

```
evolve-frontend/
|-- src/
|   |-- main.tsx                   # Entry point
|   |-- App.tsx                    # Router principal
|   |
|   |-- api/
|   |   |-- client.ts              # Axios/fetch configurado
|   |   |-- auth.ts                # API calls de auth
|   |   |-- empresas.ts            # API calls de empresas
|   |   |-- tributario.ts          # API calls tributarias
|   |   |-- ia.ts                  # API calls de IA
|   |   +-- pagos.ts               # API calls de pagos
|   |
|   |-- components/
|   |   |-- layout/
|   |   |   |-- Navbar.tsx
|   |   |   |-- Sidebar.tsx
|   |   |   +-- Footer.tsx
|   |   |-- ui/                    # Componentes reutilizables
|   |   |   |-- Button.tsx
|   |   |   |-- Modal.tsx
|   |   |   |-- DataTable.tsx
|   |   |   +-- LoadingSpinner.tsx
|   |   +-- shared/
|   |       |-- ProtectedRoute.tsx
|   |       +-- ErrorBoundary.tsx
|   |
|   |-- pages/
|   |   |-- Login.tsx
|   |   |-- Dashboard.tsx
|   |   |-- empresas/
|   |   |   |-- EmpresasList.tsx
|   |   |   +-- EmpresasForm.tsx
|   |   |-- tributario/
|   |   |   |-- F29Dashboard.tsx
|   |   |   |-- DJIntegral.tsx
|   |   |   +-- SituacionTributaria.tsx
|   |   |-- ia/
|   |   |   +-- IADashboard.tsx
|   |   +-- pagos/
|   |       |-- Planes.tsx
|   |       |-- Checkout.tsx
|   |       +-- Historial.tsx
|   |
|   |-- hooks/
|   |   |-- useAuth.ts
|   |   |-- useEmpresas.ts
|   |   +-- usePagos.ts
|   |
|   |-- store/                     # Zustand o Redux Toolkit
|   |   |-- authStore.ts
|   |   |-- empresasStore.ts
|   |   +-- uiStore.ts
|   |
|   |-- types/                     # TypeScript interfaces
|   |   |-- auth.ts
|   |   |-- empresa.ts
|   |   |-- tributario.ts
|   |   +-- pago.ts
|   |
|   +-- utils/
|       |-- formatters.ts
|       |-- validators.ts
|       +-- constants.ts
|
|-- package.json
|-- tsconfig.json
|-- vite.config.ts
|-- Dockerfile
+-- .env.example
```

#### 3.3 Stack Tecnologico Recomendado

| Capa | Tecnologia | Justificacion |
|------|-----------|---------------|
| **Frontend** | React 18 + TypeScript | Ecosistema maduro, tipado fuerte, componentes reutilizables |
| **Build tool** | Vite | Build rapido, HMR instantaneo |
| **UI Library** | Shadcn/UI + Tailwind CSS | Componentes accesibles, personalizable, reemplaza Bootstrap |
| **Estado** | Zustand o TanStack Query | Zustand para estado global, TanStack para cache de servidor |
| **Routing** | React Router v6 | Estandar de la industria, lazy loading nativo |
| **Backend** | FastAPI 0.110+ | Async nativo, validacion automatica, OpenAPI, alta performance |
| **ORM** | SQLAlchemy 2.0 + async | Ya lo usan, version async para FastAPI |
| **Auth** | JWT (access + refresh tokens) | Stateless, escalable, compatible con SPA |
| **Validacion** | Pydantic v2 | Integrado con FastAPI, ya lo usan parcialmente |
| **DB Driver** | asyncpg (PG) + aiomysql (MySQL) | Drivers async para maximo rendimiento |
| **Testing** | Pytest + React Testing Library | Cobertura backend + frontend |
| **Pasarela de pago** | Stripe o MercadoPago | Ver seccion 4 |
| **Deploy** | Docker + Docker Compose | Simplifica deploy multi-contenedor |

#### 3.4 Autenticacion: Migracion de Sesiones a JWT

**Actual:** Flask-Login con sesiones server-side + token en BD
**Propuesto:** JWT con access token (15 min) + refresh token (7 dias)

```
[Login] --> [FastAPI valida credenciales]
                    |
            [Genera JWT access + refresh]
                    |
            [React almacena en httpOnly cookie]
                    |
[Cada request] --> [Middleware valida JWT]
                    |
            [Si expiro] --> [Refresh endpoint]
                    |
            [Si refresh expiro] --> [Re-login]
```

Ventajas sobre el sistema actual:
- Stateless: no necesita consultar BD en cada request
- Escalable: funciona con multiples instancias de backend
- Mantiene la seguridad: httpOnly cookies previenen XSS

---

## 4. PASARELA DE PAGO: ANALISIS Y RECOMENDACION

### 4.1 Comparativa

| Criterio | Stripe | MercadoPago | Transbank (WebPay) |
|----------|--------|-------------|-------------------|
| **Presencia Chile** | Si (via intl) | Si (fuerte en LATAM) | Si (dominante local) |
| **Facilidad integracion** | Excelente | Buena | Regular |
| **Documentacion** | Excelente | Buena | Regular |
| **SDK Python** | Oficial, robusto | Oficial | Oficial (limitado) |
| **Webhooks** | Si, confiables | Si | Si (mas complejo) |
| **Suscripciones** | Nativo | Nativo | No nativo |
| **Comision** | 2.9% + 30c USD | 3.49% + IVA | 2.49% + IVA |
| **Moneda local CLP** | Si | Si | Si (nativo) |
| **PCI Compliance** | Nivel 1 (hosted) | Nivel 1 (hosted) | Nivel 1 |
| **Soporte recurrente** | Excelente | Bueno | Limitado |

### 4.2 Recomendacion: Stripe (Principal) + MercadoPago (Alternativa)

**Stripe** es la mejor opcion por:
1. API mas limpia y mejor documentada
2. Soporte nativo de suscripciones (ideal para SaaS tributario)
3. Webhooks robustos para manejar estados de pago
4. Dashboard completo para administracion
5. Stripe Checkout: formulario hosted que reduce scope PCI
6. Customer Portal: gestion de suscripciones self-service

**MercadoPago** como alternativa para clientes que prefieran medios locales.

### 4.3 Modelo de Monetizacion Sugerido

```
Plan Basico        Plan Profesional     Plan Enterprise
$29.990 CLP/mes    $59.990 CLP/mes      $149.990 CLP/mes
|                   |                     |
|- 1 BD MySQL       |- 3 BDs MySQL       |- BDs ilimitadas
|- F29 + DJ         |- Todo Basico        |- Todo Profesional
|- 5 empresas       |- Sit. Tributaria    |- IA ilimitada
|- Sin IA           |- IA (50 analisis)   |- API access
|                   |- Soporte email      |- Soporte prioritario
|                   |                     |- Integracion ERP
```

### 4.4 Esquema de Base de Datos para Pagos

```sql
-- Nuevas tablas en PostgreSQL (schema: pagos)

CREATE SCHEMA IF NOT EXISTS pagos;

CREATE TABLE pagos.planes (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,        -- 'basico', 'profesional', 'enterprise'
    nombre VARCHAR(100) NOT NULL,
    precio_mensual INTEGER NOT NULL,            -- en CLP (centavos)
    precio_anual INTEGER,                       -- descuento anual
    max_bases_datos INTEGER DEFAULT 1,
    max_empresas INTEGER DEFAULT 5,
    max_analisis_ia INTEGER DEFAULT 0,
    modulos_incluidos JSONB NOT NULL,           -- ['f29', 'dj', 'situacion', 'ia', 'erp']
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pagos.suscripciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES auth.usuarios(id),
    plan_id INTEGER REFERENCES pagos.planes(id),
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    estado VARCHAR(30) NOT NULL,                -- 'active', 'past_due', 'canceled', 'trialing'
    periodo VARCHAR(10) DEFAULT 'mensual',      -- 'mensual', 'anual'
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP,
    fecha_proximo_cobro TIMESTAMP,
    fecha_cancelacion TIMESTAMP,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pagos.transacciones (
    id SERIAL PRIMARY KEY,
    suscripcion_id INTEGER REFERENCES pagos.suscripciones(id),
    stripe_payment_intent_id VARCHAR(255),
    monto INTEGER NOT NULL,                     -- en CLP
    moneda VARCHAR(3) DEFAULT 'CLP',
    estado VARCHAR(30) NOT NULL,                -- 'succeeded', 'pending', 'failed', 'refunded'
    metodo_pago VARCHAR(50),                    -- 'card', 'bank_transfer'
    descripcion TEXT,
    metadata JSONB,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pagos.facturas (
    id SERIAL PRIMARY KEY,
    transaccion_id INTEGER REFERENCES pagos.transacciones(id),
    numero_factura VARCHAR(50) UNIQUE,
    url_pdf VARCHAR(500),                       -- Stripe hosted invoice URL
    fecha_emision TIMESTAMP NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);
```

---

## 5. PLAN DE MIGRACION POR FASES

### FASE 1: Fundacion (Semanas 1-4)

**Objetivo:** Backend FastAPI funcional + Frontend React base

| Semana | Backend | Frontend |
|--------|---------|----------|
| 1 | Estructura FastAPI, config, DB async, JWT auth | Proyecto React + Vite, routing, auth flow |
| 2 | Migrar modulo auth completo, middleware | Login page, protected routes, Navbar |
| 3 | Migrar modulo empresas (CRUD completo) | Listado empresas, formulario CRUD |
| 4 | Tests auth + empresas, documentacion API | Integracion completa auth + empresas |

**Entregable:** Sistema de login + gestion de empresas funcionando en React + FastAPI

### FASE 2: Modulos Core (Semanas 5-8)

| Semana | Backend | Frontend |
|--------|---------|----------|
| 5 | Migrar F29, endpoints REST | Dashboard F29, tablas, exportacion |
| 6 | Migrar DJ Integral | Dashboard DJ, graficos |
| 7 | Migrar Situacion Tributaria | Vista situacion tributaria |
| 8 | Migrar ERP Audisoft, tests | Vista ERP, tests E2E |

**Entregable:** Todos los modulos tributarios funcionando

### FASE 3: IA + Pagos (Semanas 9-12)

| Semana | Backend | Frontend |
|--------|---------|----------|
| 9 | Migrar modulo IA (Gemini), WebSockets para progreso | IA Dashboard con streaming |
| 10 | Integracion Stripe: planes, checkout, webhooks | Pagina de planes, checkout flow |
| 11 | Suscripciones, facturacion, portal cliente | Historial pagos, gestion suscripcion |
| 12 | Tests completos, seguridad, optimizacion | Polish UI, responsive, performance |

**Entregable:** Plataforma completa con IA y pagos

### FASE 4: Produccion (Semanas 13-14)

- Docker Compose para deploy completo
- CI/CD con GitHub Actions
- Monitoreo (Prometheus + Grafana o similar)
- Migracion de datos de usuarios existentes
- Periodo de prueba paralelo (Flask + FastAPI)
- Cutover a produccion

---

## 6. COMPARATIVA: ESTADO ACTUAL vs PROPUESTO

| Aspecto | Flask Actual | React + FastAPI Propuesto |
|---------|-------------|--------------------------|
| **Rendimiento** | Sincrono, ~100 req/s | Async, ~1000+ req/s |
| **Frontend** | SSR (Jinja2), recarga completa | SPA, navegacion instantanea |
| **UX** | Paginas completas reload | Transiciones fluidas, loading states |
| **API** | Mixta (HTML + JSON) | REST pura con OpenAPI docs |
| **Auth** | Sesiones server-side | JWT stateless, escalable |
| **Pagos** | No existe | Stripe integrado nativamente |
| **Mobile** | Responsive basico | PWA potencial, API reutilizable para app |
| **Testing** | Sin tests | Pytest + RTL + E2E |
| **Deploy** | Manual/scripts PS | Docker + CI/CD automatizado |
| **Documentacion API** | No existe | Auto-generada (Swagger/ReDoc) |
| **Escalabilidad** | Vertical (un proceso) | Horizontal (multiples workers async) |
| **DX (Dev Experience)** | Buena | Excelente (hot reload, tipado, linting) |

---

## 7. RIESGOS Y MITIGACION

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Retraso en migracion | Alta | Alto | Migrar modulo por modulo, no big bang |
| Perdida de funcionalidad | Media | Alto | Tests antes de migrar, QA por modulo |
| Curva aprendizaje React | Media | Medio | Usar templates, componentes pre-hechos |
| Incompatibilidad DB async | Baja | Alto | aiomysql probado, fallback a sync si necesario |
| Downtime en cutover | Media | Alto | Deploy paralelo, switch DNS gradual |
| Complejidad JWT | Baja | Medio | Librerias maduras (python-jose), refresh tokens |

---

## 8. VEREDICTO FINAL

### Microservicios: NO (todavia)

Los microservicios son una **solucion a problemas de escala organizacional y tecnica** que tu proyecto aun no tiene. Con ~17,500 lineas de Python y presumiblemente un equipo pequeno:

- El overhead operacional superaria los beneficios
- No hay necesidad de escalar servicios independientemente (aun)
- La complejidad de comunicacion inter-servicio no se justifica
- Un solo deploy es mas facil de mantener y debuggear

### Monolito Modular con React + FastAPI: SI

Esta arquitectura te da:
1. **Separacion frontend/backend** sin la complejidad de microservicios
2. **Async nativo** para las operaciones pesadas (IA, SII, multi-DB)
3. **API documentada automaticamente** con OpenAPI/Swagger
4. **Pasarela de pago** integrada de forma limpia
5. **Camino claro hacia microservicios** si en el futuro lo necesitas (extraer IA y Pagos)
6. **Mejor experiencia de usuario** con SPA React
7. **Mejor experiencia de desarrollo** con TypeScript, hot reload, testing

### Cuando SI pasar a microservicios:
- Cuando el equipo crezca a 5+ desarrolladores trabajando simultaneamente
- Cuando el modulo IA necesite GPU dedicada o escalado independiente
- Cuando el volumen de transacciones de pago justifique aislamiento PCI
- Cuando necesites deployar modulos con frecuencias diferentes

> **Principio clave:** Comienza con la arquitectura mas simple que resuelva tus problemas actuales, y disenala para que pueda evolucionar. Un monolito bien modularizado se puede dividir en microservicios; un sistema de microservicios mal disenado es muy dificil de unificar.

---

## 9. PROXIMOS PASOS RECOMENDADOS

1. **Aprobar este analisis** y definir prioridades
2. **Configurar repositorio**: monorepo o repos separados (frontend/backend)
3. **Iniciar Fase 1**: Estructura FastAPI + React con auth
4. **Definir contrato API**: OpenAPI specs antes de implementar
5. **Seleccionar pasarela de pago**: Crear cuenta Stripe y configurar test mode
6. **Establecer CI/CD**: GitHub Actions basico desde el dia 1
