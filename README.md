# 🚀 Evolve Soluciones

Sistema integral de gestión empresarial para consultoría y asesoría tributaria, desarrollado con Flask y arquitectura MVC escalable.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Desarrollo](#desarrollo)
- [Contribución](#contribución)
- [Licencia](#licencia)

## ✨ Características

### 🏢 Gestión Empresarial
- **Consolidado de Empresas**: Vista mensual y anual de datos empresariales
- **Consulta Integral F29**: Seguimiento de formularios tributarios mensuales
- **Gestión de Tareas**: Sistema de tareas por empresa con estados y prioridades
- **Observaciones**: Registro y seguimiento de observaciones por período

### 🔐 Seguridad y Autenticación
- **Autenticación robusta** con Flask-Login
- **Gestión de sesiones** con tokens únicos
- **Control de acceso** por roles (usuario/administrador)
- **Protección CSRF** en todos los formularios
- **Validación de datos** tanto en cliente como servidor

### 📊 Funcionalidades Avanzadas
- **Filtros dinámicos** en tiempo real
- **Exportación a Excel** de datos
- **Estadísticas y reportes**
- **API REST** para integraciones
- **Interfaz responsive** con Bootstrap 5

### 🛠️ Arquitectura Técnica
- **Patrón MVC** para organización del código
- **Blueprints de Flask** para modularidad
- **Servicios independientes** para lógica de negocio
- **Decoradores personalizados** para funcionalidades transversales
- **Manejo de errores** centralizado

## 📁 Estructura del Proyecto

```
evolve-soluciones/
├── aplicacion/                    # Código principal de la aplicación
│   ├── controladores/            # Controladores (Blueprints de Flask)
│   │   ├── autenticacion.py      # Rutas de autenticación
│   │   ├── consulta_integral_f29.py  # Consulta F29
│   │   └── ...
│   ├── modelos/                  # Modelos de datos
│   │   ├── base_datos.py         # Conexiones y operaciones DB
│   │   ├── usuario.py            # Modelo de usuario
│   │   ├── sesion.py             # Modelo de sesión
│   │   └── ...
│   ├── servicios/                # Lógica de negocio
│   │   ├── servicio_consulta_integral.py
│   │   └── ...
│   ├── utilidades/               # Herramientas y helpers
│   │   ├── decoradores.py        # Decoradores personalizados
│   │   ├── validadores.py        # Funciones de validación
│   │   ├── herramientas_ip.py    # Manejo de IPs
│   │   └── ...
│   ├── plantillas/               # Templates HTML
│   │   ├── diseños/             # Layouts base
│   │   ├── componentes/         # Componentes reutilizables
│   │   ├── paginas/             # Páginas específicas
│   │   └── ...
│   ├── estaticos/               # Archivos estáticos
│   │   ├── css/                 # Hojas de estilo
│   │   ├── js/                  # JavaScript
│   │   └── imagenes/            # Imágenes
│   └── __init__.py
├── configuracion/               # Configuraciones
│   ├── configuracion.py        # Configuración principal
│   └── __init__.py
├── documentacion/              # Documentación del proyecto
├── pruebas/                   # Tests unitarios y de integración
├── scripts/                   # Scripts de utilidad
├── migraciones/              # Migraciones de base de datos
├── aplicacion.py             # Punto de entrada principal
├── requirements.txt          # Dependencias Python
├── env.ejemplo              # Ejemplo de variables de entorno
└── README.md               # Este archivo
```

## 🔧 Instalación

### Prerrequisitos

- Python 3.8+
- MySQL 5.7+
- MongoDB (opcional)
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/evolve-soluciones.git
   cd evolve-soluciones
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   
   # En Windows
   venv\Scripts\activate
   
   # En Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp env.ejemplo .env
   # Editar .env con tus configuraciones
   ```

5. **Configurar base de datos**
   ```sql
   -- Crear base de datos MySQL
   CREATE DATABASE evolve CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   
   -- Crear usuario (opcional)
   CREATE USER 'evolve_user'@'localhost' IDENTIFIED BY 'tu_password';
   GRANT ALL PRIVILEGES ON evolve.* TO 'evolve_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

6. **Ejecutar migraciones** (cuando estén disponibles)
   ```bash
   python scripts/migrar_base_datos.py
   ```

## ⚙️ Configuración

### Variables de Entorno

Crea un archivo `.env` basado en `env.ejemplo` y configura las siguientes variables:

```env
# Configuración general
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=tu-clave-secreta-super-segura

# Base de datos local
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=tu-password
DB_NAME=evolve
DB_PORT=3306

# Base de datos remota (opcional)
REMOTE_DB_HOST=192.168.0.2
REMOTE_DB_USER=usuario-remoto
REMOTE_DB_PASSWORD=password-remoto

# APIs externas
GEMINI_API_KEY=tu-api-key-de-gemini
GOOGLE_SHEETS_CREDENTIALS_FILE=credenciales.json
```

### Configuración por Entornos

El sistema soporta múltiples entornos de configuración:

- **Desarrollo** (`desarrollo`): Debug activado, configuraciones flexibles
- **Pruebas** (`pruebas`): Base de datos en memoria, CSRF desactivado
- **Producción** (`produccion`): Configuraciones de seguridad estrictas

## 🚀 Uso

### Ejecutar la Aplicación

```bash
# Desarrollo
python aplicacion.py

# Producción con Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 aplicacion:app
```

### Acceso a la Aplicación

- **Local**: http://127.0.0.1:5000
- **Red local**: http://192.168.0.55:5000
- **ZeroTier**: http://172.25.196.7:5000

### Usuarios por Defecto

El sistema incluye usuarios de ejemplo (configurar en migraciones):

- **Administrador**: admin / admin123
- **Usuario**: usuario / usuario123

## 🛠️ Desarrollo

### Estructura de Código

#### Controladores (Controllers)
Los controladores manejan las rutas HTTP y coordinan entre modelos y vistas:

```python
from flask import Blueprint, request, render_template
from aplicacion.servicios.mi_servicio import MiServicio

mi_bp = Blueprint('mi_modulo', __name__, url_prefix='/mi-modulo')

@mi_bp.route('/mi-ruta')
def mi_funcion():
    servicio = MiServicio()
    datos = servicio.obtener_datos()
    return render_template('mi_template.html', datos=datos)
```

#### Modelos (Models)
Los modelos representan entidades de datos y su lógica:

```python
from aplicacion.modelos.base_datos import ejecutar_consulta

class MiModelo:
    def __init__(self, id, nombre):
        self.id = id
        self.nombre = nombre
    
    @staticmethod
    def obtener_por_id(id):
        consulta = "SELECT * FROM mi_tabla WHERE id = %s"
        resultado = ejecutar_consulta(consulta, (id,), obtener_uno=True)
        return MiModelo(**resultado) if resultado else None
```

#### Servicios (Services)
Los servicios contienen la lógica de negocio:

```python
from aplicacion.modelos.mi_modelo import MiModelo

class MiServicio:
    def obtener_datos_procesados(self):
        datos = MiModelo.obtener_todos()
        # Lógica de procesamiento
        return datos_procesados
```

### Decoradores Disponibles

```python
from aplicacion.utilidades.decoradores import (
    acceso_empresa_requerido,
    solo_administradores,
    validar_json,
    manejar_errores
)

@mi_bp.route('/ruta-protegida')
@login_required
@solo_administradores
@manejar_errores
def funcion_protegida():
    # Tu código aquí
    pass
```

### Validaciones

```python
from aplicacion.utilidades.validadores import (
    validar_email,
    validar_rut_chileno,
    validar_contraseña
)

if not validar_email(email):
    raise ValueError("Email inválido")
```

### Testing

```bash
# Ejecutar todos los tests
python -m pytest

# Con coverage
python -m pytest --cov=aplicacion

# Tests específicos
python -m pytest pruebas/test_usuarios.py
```

### Convenciones de Código

- **Nombres en español** para variables, funciones y clases
- **Docstrings** en español para todas las funciones
- **Comentarios** explicativos en español
- **PEP 8** para estilo de código Python
- **Nombres descriptivos** para funciones y variables

### Estructura de Commits

```
tipo: descripción breve

Descripción más detallada si es necesaria

- Cambio específico 1
- Cambio específico 2
```

Tipos de commit:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Documentación
- `style`: Formateo de código
- `refactor`: Refactorización
- `test`: Tests
- `chore`: Tareas de mantenimiento

## 🤝 Contribución

1. **Fork** el proyecto
2. **Crea** una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** tus cambios (`git commit -m 'feat: agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Abre** un Pull Request

### Guías de Contribución

- Seguir las convenciones de código establecidas
- Escribir tests para nuevas funcionalidades
- Actualizar documentación cuando sea necesario
- Usar nombres descriptivos en español
- Mantener compatibilidad hacia atrás

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 🆘 Soporte

Para soporte técnico o preguntas:

- **Email**: soporte@evolve-soluciones.com
- **Issues**: [GitHub Issues](https://github.com/tu-usuario/evolve-soluciones/issues)
- **Documentación**: [Wiki del proyecto](https://github.com/tu-usuario/evolve-soluciones/wiki)

## 🔄 Changelog

### v1.0.0 (2024-XX-XX)
- ✨ Lanzamiento inicial del sistema
- 🏢 Módulo de consulta integral F29
- 🔐 Sistema de autenticación y autorización
- 📊 Exportación a Excel
- 🎨 Interfaz responsive con Bootstrap 5

---

**Desarrollado con ❤️ por el equipo de Evolve Soluciones**
