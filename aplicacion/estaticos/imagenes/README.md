# Imágenes y Assets

## 📁 Estructura de Carpetas

```
aplicacion/estaticos/imagenes/
├── logo-evolve.png          # Logo principal de Evolve Soluciones
├── favicon.ico              # Icono del navegador
├── logo-light.png           # Logo versión clara (opcional)
├── logo-dark.png            # Logo versión oscura (opcional)
└── README.md                # Este archivo
```

## 🖼️ Logo Principal

### Especificaciones Recomendadas

**Para `logo-evolve.png`:**
- **Formato**: PNG con transparencia
- **Dimensiones**: 400x150 px (o proporcional)
- **Peso**: Máximo 200 KB
- **Fondo**: Transparente
- **Uso**: Página de inicio de sesión

### ¿Cómo Agregar el Logo?

1. **Preparar el logo**:
   - Guarda tu logo en formato PNG con fondo transparente
   - Renómbralo como `logo-evolve.png`

2. **Copiar a la carpeta**:
   ```powershell
   # Desde PowerShell
   Copy-Item "C:\ruta\a\tu\logo.png" "aplicacion\estaticos\imagenes\logo-evolve.png"
   ```

3. **Verificar**:
   - Abre tu navegador y ve a la página de login
   - El logo debería aparecer automáticamente
   - Si no aparece, refresca con `Ctrl+F5`

### Sin Logo

Si no tienes un logo todavía, la página mostrará un ícono placeholder automáticamente.

## 🎨 Crear un Logo Temporal

Si necesitas un logo temporal, puedes:

### Opción 1: Generador Online
- Usa [Canva](https://www.canva.com) (gratis)
- Usa [LogoMakr](https://logomakr.com) (gratis)
- Usa [Hatchful de Shopify](https://www.shopify.com/tools/logo-maker) (gratis)

### Opción 2: Usar un Ícono
- Descarga íconos de [Font Awesome](https://fontawesome.com)
- Descarga íconos de [Flaticon](https://www.flaticon.com)
- Descarga íconos de [Icons8](https://icons8.com)

### Opción 3: Logo de Texto Simple
Puedes crear un logo simple con texto usando:
- [Photopea](https://www.photopea.com) (editor online gratis tipo Photoshop)
- GIMP (software gratuito)

## 🔧 Configuración Adicional

### Favicon

Para agregar un favicon (ícono del navegador):

1. Convierte tu logo a formato ICO (usa [favicon.io](https://favicon.io))
2. Guarda como `favicon.ico` en esta carpeta
3. Actualiza el archivo `aplicacion/plantillas/diseños/base.html`:

```html
<link rel="icon" href="{{ url_for('static', filename='imagenes/favicon.ico') }}" type="image/x-icon">
```

### Versiones del Logo

Si tienes múltiples versiones:

```
logo-light.png  → Para fondos oscuros
logo-dark.png   → Para fondos claros
logo-square.png → Versión cuadrada
logo-icon.png   → Solo ícono
```

Actualiza en `iniciar_sesion.html`:

```html
<img src="{{ url_for('static', filename='imagenes/logo-light.png') }}" alt="Logo">
```

## 📐 Optimización de Imágenes

Para mejor rendimiento, optimiza tus imágenes:

### Herramientas Online
- [TinyPNG](https://tinypng.com) - Compresión PNG/JPG
- [Squoosh](https://squoosh.app) - Compresión avanzada
- [ImageOptim](https://imageoptim.com) - Mac/Windows

### Comandos PowerShell
```powershell
# Convertir JPG a PNG
# (Requiere ImageMagick instalado)
magick convert logo.jpg logo-evolve.png

# Redimensionar
magick convert logo.png -resize 400x150 logo-evolve.png

# Optimizar PNG
# (Requiere pngquant)
pngquant --quality=80-90 logo-evolve.png
```

## 🎨 Paleta de Colores del Proyecto

Si estás diseñando tu logo, estos son los colores del proyecto:

```
Primario:   #667eea (Azul violeta)
Secundario: #764ba2 (Púrpura)
Acento:     #48bb78 (Verde)
Texto:      #2d3748 (Gris oscuro)
Fondo:      #f7fafc (Gris muy claro)
```

##  Checklist

- [ ] Logo en formato PNG con transparencia
- [ ] Dimensiones adecuadas (400x150 px recomendado)
- [ ] Peso optimizado (< 200 KB)
- [ ] Archivo renombrado como `logo-evolve.png`
- [ ] Copiado a `aplicacion/estaticos/imagenes/`
- [ ] Verificado en la página de login
- [ ] (Opcional) Favicon agregado

## 🆘 Soporte

Si tienes problemas:
1. Verifica que el archivo se llame exactamente `logo-evolve.png`
2. Verifica que esté en la ruta correcta
3. Limpia el caché del navegador con `Ctrl+F5`
4. Revisa la consola del navegador (F12) para errores

## 📝 Ejemplo Rápido

```powershell
# Desde la raíz del proyecto
cd aplicacion\estaticos\imagenes

# Copiar tu logo
Copy-Item "C:\Downloads\mi-logo.png" "logo-evolve.png"

# Verificar que existe
Get-ChildItem logo-evolve.png
```

¡Listo! Tu logo aparecerá en la página de inicio de sesión 🚀
