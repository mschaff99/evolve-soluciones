# Módulo de Gestión de Empresas

## 📁 Estructura de Archivos

### Backend
```
aplicacion/
├── controladores/
│   └── empresas.py              # 8 rutas HTTP (CRUD + credenciales)
├── servicios/
│   ├── servicio_empresas.py     # Lógica de negocio
│   └── servicio_encriptacion.py # Encriptación Fernet (reversible)
└── modelos/
    └── base_datos.py            # Conexiones MySQL
```

### Frontend
```
aplicacion/
├── plantillas/paginas/empresas/
│   ├── listar.html              # Vista listado con modal credenciales
│   └── formulario.html          # Formulario crear/editar
├── estaticos/
│   ├── css/
│   │   └── empresas.css         # Estilos profesionales (420 líneas)
│   └── js/
│       ├── empresas-listado.js  # Lógica del listado (189 líneas)
│       └── empresas-formulario.js # Lógica del formulario (215 líneas)
```

### Migraciones
```
migraciones/
└── 004_agregar_modulo_empresas.sql  # Registro en modulos_sistema
```

### Scripts de Utilidad
```
scripts/
├── insertar_credencial_simple.py    # Insertar 1 credencial (modo interactivo)
├── insertar_credenciales_lote.py    # Insertar 130+ credenciales
└── leer_credencial_ejemplo.py       # Ejemplo de lectura para scripts externos
```

## 🎯 Funcionalidades

### Vista Listado (`listar.html` + `empresas-listado.js`)
-  Tabla de empresas con búsqueda
-  Estadísticas rápidas (3 cards)
-  Modal para gestionar credenciales SII
-  Toggle de visibilidad de contraseña
-  Validaciones frontend
-  Indicadores de credencial configurada/no configurada

**Funciones JavaScript:**
- `editarEmpresa(rut)` - Redirige a edición
- `gestionarCredencial(rut, empresa, tieneCredencial)` - Abre modal
- `togglePassword()` - Muestra/oculta contraseña
- `guardarCredencial()` - Guarda con encriptación Fernet
- `eliminarCredencial(rut)` - Elimina credencial con confirmación

### Vista Formulario (`formulario.html` + `empresas-formulario.js`)
-  Crear/editar empresa
-  Validación de RUT (formato y obligatoriedad)
-  Formateo automático de RUT (XXXXXXXX-X)
-  RUT readonly en modo edición
-  Advertencia de cambios sin guardar
-  Indicadores de carga

**Funciones JavaScript:**
- `manejarEnvioFormulario(e)` - Envío asíncrono
- `formatearRUT(e)` - Auto-formato mientras escribe
- `validarFormatoRUT(rut)` - Validación de formato
- `confirmarCancelacion(e)` - Previene pérdida de datos

## 🔐 Encriptación de Credenciales

### Proceso (igual en web y scripts)
1. **Encriptar**: `servicio_encriptacion.encriptar(clave)`
2. **Guardar**: INSERT/UPDATE en `credenciales_sii`
3. **Verificar**: Desencriptar y comparar con original
4. **Confirmar**: Solo commit si verificación exitosa

### Características de Fernet
-  **Reversible** (se puede desencriptar)
-  **Segura** (AES-128 CBC + HMAC)
-  **Compatible** con automatización
-  Clave en `.encryption_key` (git-ignored)

### Lectura para Scripts Externos
```python
from aplicacion.servicios.servicio_empresas import ServicioEmpresas

servicio = ServicioEmpresas('stratex')
password = servicio.obtener_credencial_sii_desencriptada('77235170-4')
# Usar password para login automático SII
```

## 🎨 Arquitectura de Estilos

### Archivo: `empresas.css`
- Variables CSS para theme-aware colors
- Componentes: stat-card, table-empresas, badge-credencial
- Animaciones: hover, focus, transitions
- Responsive design (mobile-first)
- Consistente con diseño general del sistema

## 🚀 Uso

### Desde la Web
1. Ir a `http://localhost:5000/stratex/empresas`
2. Click en "Nueva Empresa"
3. Llenar formulario (RUT y nombre obligatorios)
4. Guardar
5. Click en icono de llave 🔑 para agregar credencial SII
6. Ingresar contraseña (se encripta con Fernet automáticamente)

### Desde Scripts
```powershell
# Insertar una credencial (interactivo)
python scripts/insertar_credencial_simple.py

# Insertar con argumentos
python scripts/insertar_credencial_simple.py --rut 77235170-4 --password abc123

# Insertar 130+ credenciales
python scripts/insertar_credenciales_lote.py

# Leer credencial (para debugging)
python scripts/leer_credencial_ejemplo.py 77235170-4
```

## 📊 Base de Datos

### Tabla: `empresas` (MySQL)
```sql
CREATE TABLE empresas (
    orden INT PRIMARY KEY,
    run_rut VARCHAR(20) UNIQUE,
    empresa VARCHAR(255),
    auditor VARCHAR(100),
    grupo VARCHAR(100)
);
```

### Tabla: `credenciales_sii` (MySQL)
```sql
CREATE TABLE credenciales_sii (
    rut VARCHAR(20) PRIMARY KEY,
    clave TEXT,  -- Encriptada con Fernet
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 🔄 Flujo de Datos

### Crear Empresa
```
Frontend (formulario.html)
    ↓ POST /empresas/api/crear
Backend (empresas.py::api_crear_empresa)
    ↓ servicio.crear_empresa(datos)
Servicio (servicio_empresas.py)
    ↓ INSERT INTO empresas
Base de Datos (MySQL)
```

### Guardar Credencial
```
Frontend (modal en listar.html)
    ↓ POST /empresas/api/credencial/{rut}
Backend (empresas.py::api_guardar_credencial)
    ↓ servicio.guardar_credencial_sii(rut, clave)
Servicio (servicio_empresas.py)
    ↓ servicio_encriptacion.encriptar(clave)
Encriptación (servicio_encriptacion.py)
    ↓ Fernet.encrypt() + base64
    ↓ INSERT/UPDATE credenciales_sii
Base de Datos (MySQL)
    ↓ Verificar desencriptación
    ↓ COMMIT si coincide
```

## 🛡️ Seguridad

### Validaciones
-  Frontend: JavaScript en tiempo real
-  Backend: Python en controladores
-  Base de Datos: Restricciones SQL

### Protecciones
-  CSRF tokens en todos los formularios
-  SQL parametrizado (sin concatenación)
-  Escape automático en templates (Jinja2)
-  Encriptación Fernet para passwords
-  HTTPS recomendado en producción

## 📝 Logs Esperados

### Al guardar credencial desde web:
```
🔐 Encriptando credencial para 77235170-4 con Fernet...
💾 Credencial SII para 77235170-4 actualizada en base de datos
 Verificando que se puede desencriptar...
 Verificación exitosa - La contraseña se puede recuperar correctamente
 Credencial SII para 77235170-4 lista para automatización (Fernet reversible)
127.0.0.1 - - [15/Oct/2025 10:45:26] "POST /stratex/empresas/api/credencial/77235170-4 HTTP/1.1" 200 -
```

## 🎯 Próximos Pasos

1.  Separación de JS en archivos externos (COMPLETADO)
2. ⏳ Migración: Ejecutar `004_agregar_modulo_empresas.sql`
3. ⏳ Habilitar módulo para usuarios específicos
4. ⏳ Insertar credenciales masivas con script
5. ⏳ Integrar con módulo de automatización SII

## 📚 Referencias

- **Fernet**: https://cryptography.io/en/latest/fernet/
- **Bootstrap 5**: https://getbootstrap.com/docs/5.3/
- **Flask Blueprints**: https://flask.palletsprojects.com/en/3.0.x/blueprints/
- **PEP 8**: https://peps.python.org/pep-0008/

---
**Última actualización**: 15 de octubre de 2025
