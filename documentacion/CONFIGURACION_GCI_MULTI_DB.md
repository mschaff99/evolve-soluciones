# Configuración GCI para Múltiples Bases de Datos

## 🎯 Problema

Cuando se ejecuta el proceso GCI desde Evolve Soluciones, el script debe guardar los datos en la **base de datos correcta** (stratex, vicat, etc.) dependiendo de desde dónde se hizo la petición.

Por defecto, el script GCI lee el `.env` y usa `DB_NAME=stratex`, pero esto no es correcto cuando el usuario está trabajando con otra base de datos.

## ✅ Solución Implementada

### 1. **Evolve Soluciones pasa la base de datos al script GCI**

En `aplicacion/servicios/servicio_integracion_gci.py`, cuando se ejecuta el script GCI, ahora se configuran variables de entorno:

```python
env = dict(os.environ)
env["DB_NAME"] = base_datos  # Ej: "stratex", "vicat", etc.
env["EVOLVE_DB_NAME"] = base_datos  # Nombre alternativo
```

Esto sobrescribe la variable `DB_NAME` del `.env` **solo para el proceso hijo** (el script GCI).

### 2. **El script GCI debe leer la variable de entorno**

El script `Gestion-Consulta-Integral/main.py` **debe estar configurado** para leer la base de datos desde variables de entorno.

#### INCORRECTO (hardcodeado):
```python
# NO HACER ESTO:
DB_NAME = "stratex"  # ⛔ Siempre usa stratex
```

#### ✅ CORRECTO (lee variable de entorno):
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Lee DB_NAME del entorno, con stratex como fallback
DB_NAME = os.getenv("DB_NAME", "stratex")
```

O si usa un archivo de configuración:

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_USER = os.getenv("DB_USER", "audytax")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "2904")
    DB_NAME = os.getenv("DB_NAME", "stratex")  # 🔥 ESTO ES CRÍTICO
    DB_PORT = int(os.getenv("DB_PORT", 3306))
```

## 🧪 Cómo Verificar que Funciona

### 1. **Revisar los logs del GCI**

Cuando guardas una credencial, verifica el archivo de log en `logs/gci_opcion5_XXXXXXXX-X_YYYYMMDD-HHMMSS.log`:

```
[20251104-091538] Ejecutando opcion 5 para 76281385-8 en base de datos: stratex
...
[Config] Variable de entorno DB_NAME configurada a: stratex
[Config] Esta base de datos se usará para guardar F29 y DJ
```

### 2. **Verificar la conexión a la BD en GCI**

Dentro del script GCI, agrega logging para verificar:

```python
import logging

logging.info(f" Conectando a base de datos: {DB_NAME}")
logging.info(f" Host: {DB_HOST}, User: {DB_USER}")
```

### 3. **Test con múltiples bases de datos**

1. Accede a `http://localhost:5000/stratex/empresas`
2. Guarda una credencial → Debería guardar en `stratex`
3. Accede a `http://localhost:5000/vicat/empresas` (si existe)
4. Guarda una credencial → Debería guardar en `vicat`

## 🔧 Modificaciones Necesarias en el Script GCI

### Archivo: `Gestion-Consulta-Integral/.env`

```env
# Configuración por defecto (fallback)
DB_HOST=127.0.0.1
DB_USER=audytax
DB_PASSWORD=2904
DB_NAME=stratex  # Valor por defecto si no se sobrescribe
DB_PORT=3306
```

### Archivo: `Gestion-Consulta-Integral/config.py` (o similar)

```python
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env del directorio del script
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class DatabaseConfig:
    """Configuración de base de datos MySQL"""

    HOST = os.getenv("DB_HOST", "127.0.0.1")
    USER = os.getenv("DB_USER", "audytax")
    PASSWORD = os.getenv("DB_PASSWORD", "2904")

    # 🔥 CRÍTICO: Lee de variable de entorno (puede ser sobrescrita por proceso padre)
    NAME = os.getenv("DB_NAME", "stratex")

    PORT = int(os.getenv("DB_PORT", 3306))
    CHARSET = "utf8mb4"

    @classmethod
    def get_connection_params(cls):
        """Retorna diccionario con parámetros de conexión"""
        return {
            "host": cls.HOST,
            "user": cls.USER,
            "password": cls.PASSWORD,
            "database": cls.NAME,  # 👈 Aquí se usa la variable dinámica
            "port": cls.PORT,
            "charset": cls.CHARSET
        }

# Para debugging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"🔧 Configuración de BD cargada:")
logger.info(f"   Database: {DatabaseConfig.NAME}")
logger.info(f"   Host: {DatabaseConfig.HOST}")
logger.info(f"   Port: {DatabaseConfig.PORT}")
```

### Archivo: `Gestion-Consulta-Integral/src/database/connection.py` (o similar)

```python
import pymysql
from config import DatabaseConfig

def get_mysql_connection():
    """
    Obtiene conexión a MySQL usando la configuración dinámica

    La base de datos puede ser sobrescrita por la variable de entorno DB_NAME
    """
    try:
        conn_params = DatabaseConfig.get_connection_params()

        connection = pymysql.connect(**conn_params)

        # Log para debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Conectado a MySQL: {conn_params['database']} @ {conn_params['host']}")

        return connection

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error conectando a BD: {e}")
        logger.error(f"   Parámetros intentados: {DatabaseConfig.get_connection_params()}")
        raise
```

## 📝 Checklist de Implementación

### En Evolve Soluciones (✅ Ya implementado)
- [x] Pasar `base_datos` al servicio de integración
- [x] Configurar variable de entorno `DB_NAME` en el proceso hijo
- [x] Agregar logging de la base de datos configurada

### En Gestion-Consulta-Integral (⚠️ Pendiente)
- [ ] Modificar `config.py` para leer `DB_NAME` de variables de entorno
- [ ] Actualizar función de conexión a BD para usar configuración dinámica
- [ ] Agregar logging para confirmar qué base de datos se está usando
- [ ] Probar con diferentes bases de datos

## 🚨 Troubleshooting

### Problema: "Los datos se guardan siempre en stratex"

**Causa:** El script GCI tiene `DB_NAME` hardcodeado.

**Solución:**
1. Buscar en el código GCI dónde se define `DB_NAME`
2. Cambiarlo a: `DB_NAME = os.getenv("DB_NAME", "stratex")`
3. Reiniciar el proceso

### Problema: "No se puede conectar a la base de datos"

**Causa:** La base de datos especificada no existe.

**Solución:**
1. Verificar que la base de datos existe: `SHOW DATABASES;`
2. Confirmar permisos del usuario
3. Revisar logs del GCI para ver qué base de datos intenta usar

### Problema: "Variable de entorno no se pasa correctamente"

**Causa:** El script GCI carga `.env` DESPUÉS de que se pasan las variables.

**Solución:**
```python
# CORRECTO: Primero leer variables de entorno, luego .env como fallback
DB_NAME = os.getenv("DB_NAME")  # Lee del entorno primero
if not DB_NAME:
    load_dotenv()
    DB_NAME = os.getenv("DB_NAME", "stratex")
```

## 📞 Próximos Pasos

1. **Revisar el código del script GCI** para identificar dónde se configura `DB_NAME`
2. **Modificar** para que lea de variables de entorno
3. **Probar** guardando credenciales desde diferentes bases de datos
4. **Verificar** en MySQL que los datos se guardan en la base correcta:
   ```sql
   -- Verificar en stratex
   USE stratex;
   SELECT COUNT(*) FROM consulta_integral WHERE rut = '76281385-8';

   -- Verificar en vicat (si aplica)
   USE vicat;
   SELECT COUNT(*) FROM consulta_integral WHERE rut = '76281385-8';
   ```

## 💡 Recomendación

Considera agregar al inicio del script GCI un mensaje que confirme la base de datos:

```python
def main():
    print("="*60)
    print("🚀 Gestion-Consulta-Integral")
    print("="*60)
    print(f"📊 Base de datos: {DatabaseConfig.NAME}")
    print(f"🖥️  Host: {DatabaseConfig.HOST}")
    print("="*60)
    # ... resto del código
```

Así el usuario puede confirmar visualmente en qué base de datos se están guardando los datos.
