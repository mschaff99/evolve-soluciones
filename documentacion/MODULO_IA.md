# Módulo de Inteligencia Artificial (IA)

## 📋 Descripción General

El Módulo de IA integra **Google Gemini AI** al sistema Evolve Soluciones para realizar análisis contables automatizados y profesionales de balances de 8 columnas.

**Fecha de integración:** Enero 2025
**Versión:** 1.0.0
**Estado:**  Operacional

---

## 🎯 Funcionalidades Principales

### 1. **Generación de Balances de 8 Columnas**
- Consultas SQL optimizadas para extraer balances completos
- Soporte para múltiples períodos (YYYYMM)
- Saldos iniciales, movimientos y saldos finales
- Clasificación automática por tipo de cuenta (Activo, Pasivo, Patrimonio, Ingreso, Gasto)

### 2. **Análisis Contable con IA**
- Análisis profesional cuenta por cuenta
- Detección de anomalías contables
- Recomendaciones específicas basadas en normativa chilena (PCGA/NIIF PYMES)
- Análisis por sectores funcionales (ventas, compras, remuneraciones, etc.)

### 3. **Memoria Histórica**
- Almacenamiento de análisis anteriores
- Comparación con períodos previos
- Aprendizaje de patrones recurrentes
- Seguimiento de hallazgos resueltos vs pendientes

### 4. **Análisis del Mayor**
- Investigación automática de cuentas con anomalías
- Detección de provisiones no pagadas (ej: F29)
- Análisis de glosas para identificar movimientos problemáticos

### 5. **Exportación a Excel**
- Balance completo en primera hoja
- Mayor de cada cuenta en hojas separadas
- Análisis de IA integrado en cada hoja
- Formato profesional con colores y separadores

---

## 🏗️ Arquitectura del Módulo

### Estructura de Archivos

```
aplicacion/
├── controladores/
│   └── ia.py                    # Blueprint con endpoints API
├── servicios/
│   ├── servicio_balance_ia.py   # Lógica de generación de balances
│   ├── servicio_gemini.py       # Integración con API de Gemini
│   └── servicio_ia_memoria.py   # Gestión de memoria histórica
├── queries/
│   ├── balance_queries.py       # Consultas SQL para balances
│   └── proveedores_queries.py   # Consultas para análisis de proveedores
├── prompts/
│   ├── balance_prompts.py       # Prompts especializados para IA
│   └── proveedores_prompts.py   # Prompts para análisis de proveedores
└── plantillas/
    └── ia_dashboard.html        # Interfaz de usuario
```

### Base de Datos

**Tablas en PostgreSQL (`evolve`):**
- `ia_analisis_historico` - Almacena análisis realizados
- `ia_patrones_aprendidos` - Patrones detectados por la IA

**Migración:** `migraciones/007_modulo_ia_memoria.sql`

---

## 🔌 Endpoints API

### Dashboard
```
GET /ia/dashboard
```
**Descripción:** Interfaz principal del módulo IA
**Acceso:** Todos los usuarios autenticados
**Retorna:** HTML del dashboard interactivo

---

### Test de Conexión
```
GET /ia/test-gemini
```
**Descripción:** Verifica conexión con Google Gemini AI
**Acceso:** Administradores únicamente
**Respuesta:**
```json
{
  "estado": "exitoso",
  "mensaje": "Conexión exitosa con Gemini AI",
  "respuesta": "OK",
  "timestamp": "2025-01-20T10:30:00"
}
```

---

### Generar Balance
```
POST /ia/generar-balance
```
**Descripción:** Genera balance de 8 columnas para una empresa
**Acceso:** Todos los usuarios autenticados
**Body:**
```json
{
  "empresa_rut": "77316565-3",
  "anio_inicio": 2025,
  "mes_inicio": 1,
  "anio_fin": 2025,
  "mes_fin": 8
}
```
**Respuesta:**
```json
{
  "estado": "exitoso",
  "balance": {
    "cuentas_detalle": [...],
    "sumas": {...},
    "resultado_ejercicio": {...},
    "sumas_iguales": {...}
  },
  "metadata": {
    "empresa_rut": "77316565-3",
    "nombre_empresa": "EMPRESA EJEMPLO SPA",
    "total_cuentas": 97
  }
}
```

---

### Analizar Balance con IA
```
POST /ia/analizar-balance-completo
```
**Descripción:** Genera balance y lo analiza con IA en un solo paso
**Acceso:** Todos los usuarios autenticados
**Body:**
```json
{
  "empresa_rut": "77316565-3",
  "anio_inicio": 2025,
  "mes_inicio": 1,
  "anio_fin": 2025,
  "mes_fin": 8
}
```
**Respuesta:**
```json
{
  "success": true,
  "analisis": "...(análisis completo en texto)...",
  "empresa_info": {...},
  "estadisticas": {
    "total_cuentas_analizadas": 97,
    "analisis_id": 42
  },
  "balance_original": {...}
}
```

---

### Exportar a Excel
```
POST /ia/exportar-balance-completo
```
**Descripción:** Genera archivo Excel con balance, mayores y análisis IA
**Acceso:** Todos los usuarios autenticados
**Body:** (igual que analizar-balance-completo)
**Respuesta:** Archivo `.xlsx` descargable

---

### Historial de Análisis
```
GET /ia/historial-analisis/<empresa_rut>
```
**Descripción:** Obtiene análisis anteriores de una empresa
**Parámetros de query:**
- `limite` (int): Número de análisis a retornar (default: 5)
- `incluir_completo` (bool): Incluir análisis completo (default: false)

---

### Listar Empresas
```
GET /ia/api/empresas-lista
```
**Descripción:** Obtiene lista de todas las empresas disponibles
**Acceso:** Todos los usuarios (sin filtro por rol)
**Respuesta:**
```json
{
  "success": true,
  "empresas": [
    {
      "rut": "77316565-3",
      "empresa": "EMPRESA EJEMPLO SPA",
      "usuario": "contador1",
      "grupo": "Grupo A"
    }
  ],
  "total": 1
}
```

---

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# Google Gemini AI
GEMINI_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-2.5-pro
GEMINI_TIMEOUT=120

# Base de datos remota (para balances)
REMOTE_DB_HOST=192.168.0.2
REMOTE_DB_USER=audytax
REMOTE_DB_PASSWORD=****
REMOTE_DB_PORT=3306
```

### Archivo de Configuración (configuracion.py)

Las configuraciones están en `ConfiguracionBase`:

```python
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models'
GEMINI_TIMEOUT = int(os.getenv('GEMINI_TIMEOUT', 120))
```

---

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Dependencias clave:**
- `requests` - Para llamadas HTTP a Gemini API
- `openpyxl` - Para generación de archivos Excel
- `pandas` - Para manipulación de datos
- `Flask-Compress` - Para compresión de respuestas HTTP

### 2. Aplicar Migraciones

```bash
# PostgreSQL
psql -U postgres -d evolve -f migraciones/007_modulo_ia_memoria.sql
```

### 3. Configurar API Key de Gemini

1. Obtener API key en [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Agregar al archivo `.env`:
   ```
   GEMINI_API_KEY=tu_clave_aqui
   ```

### 4. Verificar Conexión

Acceder a: `http://localhost:5000/ia/test-gemini`

---

## 📊 Uso del Módulo

### Desde la Interfaz Web

1. Acceder a `/ia/dashboard`
2. Seleccionar empresa y rango de período
3. Hacer clic en "Generar Balance" o "Analizar con IA"
4. Descargar Excel con resultados

### Desde API/Código

```python
from aplicacion.servicios.servicio_balance_ia import BalanceService

# Generar balance
resultado = BalanceService.generar_balance_8_columnas(
    empresa_rut='77316565-3',
    periodo_inicio=202501,
    periodo_fin=202508
)

# Analizar con IA
if resultado['success']:
    analisis = BalanceService.analizar_balance_con_ia(
        balance_data=resultado['data'],
        metadata=resultado['metadata']
    )
    print(analisis['analisis'])
```

---

## 🧠 Prompts de IA

El sistema usa prompts especializados para análisis contables profesionales:

### Características de los Prompts

1. **Análisis cuenta por cuenta** - Revisa TODAS las cuentas individualmente
2. **Sectores funcionales** - Agrupa por ventas, compras, remuneraciones, etc.
3. **Detección de anomalías** - Identifica problemas automáticamente
4. **Normativa chilena** - Sigue PCGA y NIIF para PYMES
5. **Memoria histórica** - Compara con análisis anteriores

### Ejemplo de Análisis Generado

```markdown
### Cuenta: CAJA (000000111001)
- **Tipo:** Activo
- **Saldo Inicial:** $1.500.000
- **Movimientos:** Débitos: $3.200.000 / Créditos: $2.800.000
- **Saldo Final:** $1.900.000
- **Análisis Técnico:**
  Comportamiento normal de caja chica con movimientos equilibrados.
  Aumento de $400.000 respecto al período anterior es consistente
  con el incremento en ventas del mes.
- **Observación:** Normal
```

---

##  Detección de Anomalías

El sistema detecta automáticamente:

### Cuentas Transitorias con Saldos
- IVA Crédito/Débito Fiscal
- Remuneraciones por Pagar
- Honorarios por Pagar
- Leyes Sociales
- Impuestos por Pagar (F29)

### Provisiones No Pagadas
- Detecta provisiones F29 sin su correspondiente pago
- Identifica rezagos en cuentas por pagar
- Señala descuadres entre provisión y pago

### Movimientos Inusuales
- Saldos simultáneos en columnas opuestas
- Movimientos sin saldo final aparente
- Cuentas con cambios abruptos

---

## 📈 Memoria Histórica

### Tabla: `ia_analisis_historico`

**Campos principales:**
- `empresa_rut` - RUT de la empresa
- `periodo_inicio/fin` - Rango analizado (YYYYMM)
- `analisis_completo` - Texto completo del análisis
- `hallazgos_detectados` - JSON con hallazgos estructurados
- `estado_seguimiento` - Estado: pendiente, en_revision, resuelto, descartado

**Consultas útiles:**

```sql
-- Ver análisis de una empresa
SELECT id, periodo_inicio, periodo_fin, estado_seguimiento, fecha_analisis
FROM ia_analisis_historico
WHERE empresa_rut = '77316565-3'
ORDER BY fecha_analisis DESC;

-- Hallazgos pendientes
SELECT empresa_nombre, hallazgos_detectados
FROM ia_analisis_historico
WHERE estado_seguimiento = 'pendiente'
ORDER BY fecha_analisis DESC;
```

---

## 🛠️ Troubleshooting

### Error: "GEMINI_API_KEY no está configurada"
**Solución:** Agregar la API key al archivo `.env`

### Error: "Timeout al conectar con Gemini AI"
**Solución:** Aumentar `GEMINI_TIMEOUT` en `.env` o reducir el tamaño del balance

### Error: "No se pudieron obtener los datos del balance"
**Solución:** Verificar conexión a `REMOTE_DB_HOST` y credenciales

### Excel no se genera correctamente
**Solución:** Verificar que `openpyxl` esté instalado: `pip install openpyxl`

---

## 🔐 Seguridad

### Consideraciones de Seguridad

1. **API Key protegida** - Nunca exponer en código o logs
2. **Validación de entrada** - Todos los parámetros son validados
3. **Acceso controlado** - Login requerido para todos los endpoints
4. **Datos sensibles** - Los análisis contienen información confidencial
5. **Rate limiting** - Gemini API tiene límites de uso

### Buenas Prácticas

- No compartir análisis fuera del sistema
- Revisar análisis antes de tomar decisiones importantes
- Validar hallazgos con un contador profesional
- Mantener actualizada la memoria histórica

---

## 📚 Referencias

- [Google Gemini AI Documentation](https://ai.google.dev/docs)
- [Normativa Contable Chilena (PCGA)](https://www.colegiodecontadores.cl/)
- [NIIF para las PYMES](https://www.ifrs.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## 🤝 Soporte

Para soporte técnico contactar al equipo de desarrollo:
- Email: soporte@evolve-soluciones.cl
- Issues: [GitHub Repository](https://github.com/evolveSoluciones/evolve-sistema)

---

## 📝 Changelog

### v1.0.0 (Enero 2025)
-  Integración inicial con Google Gemini AI
-  Generación de balances de 8 columnas
-  Análisis contable automatizado
-  Memoria histórica de análisis
-  Exportación a Excel con mayores
-  Dashboard interactivo
-  Detección de anomalías contables
-  Análisis del mayor

---

**Última actualización:** 20 de Enero de 2025
**Mantenedor:** Equipo de Desarrollo Evolve Soluciones
