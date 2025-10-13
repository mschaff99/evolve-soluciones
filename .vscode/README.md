# Configuración de VS Code para Evolve Soluciones

##  Archivos de Configuración

Este directorio contiene toda la configuración de VS Code para el proyecto:

### Archivos Principales

- **`settings.json`**: Configuración del editor, linting, formateo, Python, etc.
- **`extensions.json`**: Extensiones recomendadas (incluyendo GitHub Copilot)
- **`launch.json`**: Configuraciones de debug para Flask
- **`tasks.json`**: Tareas automatizadas (ejecutar Flask, tests, linting, etc.)
- **`snippets.code-snippets`**: Snippets de código personalizados para el proyecto

### Otros Archivos

- **`.editorconfig`**: Configuración de formato de archivos (en raíz del proyecto)

##  Primeros Pasos

### 1. Instalar Extensiones Recomendadas

Al abrir el proyecto, VS Code te preguntará si quieres instalar las extensiones recomendadas. Acepta para instalar:

- GitHub Copilot
- GitHub Copilot Chat
- Python
- Pylance
- Jinja templates
- Y muchas más...

O instálalas manualmente desde la paleta de comandos:
```
Ctrl+Shift+P → Extensions: Show Recommended Extensions
```

### 2. Configurar Python

El proyecto usa un entorno virtual en `.venv/`. VS Code lo detectará automáticamente.

Si necesitas seleccionarlo manualmente:
```
Ctrl+Shift+P → Python: Select Interpreter → .venv/Scripts/python.exe
```

### 3. Usar las Tareas

Presiona `Ctrl+Shift+B` para ver las tareas disponibles:

- **Ejecutar Flask (Desarrollo)** - Inicia el servidor Flask
- **Ejecutar Tests** - Ejecuta pytest
- **Linting (Flake8)** - Verifica el código
- **Formatear con Black** - Formatea el código

### 4. Debug

Presiona `F5` para iniciar el debug. Configuraciones disponibles:

- **Flask: Desarrollo** - Debug de Flask con recarga automática
- **Flask: Producción (Waitress)** - Debug con Waitress
- **Python: Tests con pytest** - Debug de tests

##  Snippets Personalizados

Escribe estos prefijos y presiona `Tab` para usar snippets:

### Python/Flask
- `flask-bp` → Blueprint completo
- `flask-route-get` → Ruta GET
- `flask-route-post` → Ruta POST con JSON
- `servicio-clase` → Clase de servicio
- `sql-query` → Consulta SQL parametrizada
- `try-log` → Try-except con logging
- `docstring` → Docstring completo

### HTML/Jinja2
- `jinja-base` → Template con herencia
- `jinja-for` → Loop for

### JavaScript
- `fetch-get` → Fetch GET
- `fetch-post` → Fetch POST con CSRF

## ⚙️ Configuraciones Destacadas

### Formateo Automático
- Se formatea al guardar con Black (Python)
- Línea máxima: 120 caracteres
- Se organizan imports automáticamente

### Linting
- Flake8 habilitado
- Ignora E203, W503 (compatibilidad con Black)

### Testing
- Pytest integrado
- Tests en carpeta `pruebas/`

## 🔧 Personalización

Puedes modificar cualquier archivo de configuración según tus preferencias. Los cambios se aplicarán solo a tu workspace local.

## 📚 Referencias

- [VS Code Python](https://code.visualstudio.com/docs/python/python-tutorial)
- [GitHub Copilot Docs](https://docs.github.com/en/copilot)
- [Flask Debug](https://flask.palletsprojects.com/en/latest/debugging/)
