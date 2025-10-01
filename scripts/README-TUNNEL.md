# 🚇 Tunnelmole - Acceso Público para Evolve Soluciones

## ✅ **Tunnelmole ya está instalado y configurado**

## 🚀 **Opciones para Iniciar con Túnel Público:**

### **Opción 1: Script Automático (Recomendado)**
```bash
# Ejecutar el archivo BAT (doble clic o desde terminal):
scripts\iniciar-con-tunnelmole.bat
```

### **Opción 2: Script PowerShell**
```powershell
# Desde PowerShell:
.\scripts\iniciar-evolve.ps1
```

### **Opción 3: Solo crear túnel (si Flask ya está corriendo)**
```bash
# Si tu app ya está en el puerto 5000:
scripts\solo-tunnel.bat
```

### **Opción 4: Manual**
```bash
# Terminal 1: Iniciar Flask
python aplicacion.py

# Terminal 2: Crear túnel
tunnelmole 5000
```

## 📋 **¿Cómo Funciona?**

1. **Flask se inicia** en el puerto 5000 localmente
2. **Tunnelmole crea un túnel** hacia tu puerto 5000
3. **Obtienes una URL pública** como: `https://abc123.tunnelmole.net`
4. **Cualquier persona** puede acceder usando esa URL

## 🌐 **Ventajas de Tunnelmole:**

- ✅ **100% Gratuito**
- ✅ **Sin registro requerido**
- ✅ **Sin límites de tiempo**
- ✅ **URLs HTTPS automáticas**
- ✅ **Fácil de usar**

## 📱 **Para Compartir:**

1. Ejecuta cualquiera de los scripts
2. Copia la URL que aparece (ej: `https://abc123.tunnelmole.net`)
3. Comparte esa URL con quien necesite acceso
4. ¡Listo! Pueden acceder desde cualquier lugar del mundo

## ❌ **Para Detener:**

- Presiona `Ctrl+C` en las ventanas de terminal
- O cierra las ventanas directamente

## 🔧 **Comandos Útiles:**

```bash
# Crear túnel con subdominio personalizado (si está disponible)
tunnelmole 5000 --subdomain mi-aplicacion

# Ver versión de tunnelmole
tunnelmole --version

# Ver ayuda
tunnelmole --help
```

## 🛡️ **Consideraciones de Seguridad:**

- El túnel está **temporalmente público**
- Ciérralo cuando no lo necesites
- Para producción, considera usar un servidor dedicado
