# Configuración de IIS para Preservar IP Real del Cliente

## 🎯 Problema

Flask/Waitress recibe `127.0.0.1` como IP del cliente en `request.remote_addr`, a pesar de que IIS está recibiendo correctamente la IP real (ej: `181.161.88.222`).

**Causa:** IIS no está enviando el header `X-Forwarded-For` a Waitress con la IP del cliente original.

**Solución:** Configurar IIS Application Request Routing (ARR) o URL Rewrite para agregar el header.

---

##  Prerequisitos

- IIS instalado con rol **Application Request Routing (ARR)**
- Si ARR no está instalado:
  1. Descargar desde: https://www.iis.net/downloads/microsoft/application-request-routing
  2. Ejecutar instalador `requestRouter_amd64.msi`
  3. Reiniciar IIS: `iisreset /restart`

---

##  Método 1: Configurar ARR Server Proxy (Recomendado)

### Paso 1: Habilitar Proxy en ARR

1. Abrir **IIS Manager** (Internet Information Services)
2. Seleccionar el **servidor** (nodo raíz, no un sitio específico)
3. Doble clic en **Application Request Routing Cache**
4. En el panel derecho, clic en **Server Proxy Settings...**
5. Marcar la casilla:
   ```
   ☑ Enable proxy
   ```
6. Más abajo, marcar:
   ```
   ☑ Preserve client IP in the following header: X-Forwarded-For
   ```
7. Click **Apply** y **OK**

### Paso 2: Verificar web.config del Sitio

En `C:\inetpub\wwwroot\portal.evolveasesores.cl\web.config`, asegurarse que existe la regla de rewrite:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="ReverseProxyInboundRule" stopProcessing="true">
                    <match url="(.*)" />
                    <action type="Rewrite" url="http://127.0.0.1:8080/{R:1}" />
                    <!-- ARR agregará automáticamente X-Forwarded-For -->
                </rule>
            </rules>
        </rewrite>
    </system.webServer>
</configuration>
```

### Paso 3: Reiniciar IIS

```powershell
iisreset /restart
```

---

##  Método 2: Agregar Header Manualmente con URL Rewrite

Si ARR no está disponible o el método 1 no funciona, agregar header manualmente:

### Modificar web.config

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="ReverseProxyInboundRule" stopProcessing="true">
                    <match url="(.*)" />
                    <serverVariables>
                        <!-- Agregar variable de servidor para X-Forwarded-For -->
                        <set name="HTTP_X_FORWARDED_FOR" value="{REMOTE_ADDR}" />
                    </serverVariables>
                    <action type="Rewrite" url="http://127.0.0.1:8080/{R:1}" />
                </rule>
            </rules>
        </rewrite>
    </system.webServer>
</configuration>
```

### Habilitar modificación de Server Variables

1. Abrir **IIS Manager**
2. Seleccionar el **servidor** (nodo raíz)
3. Doble clic en **URL Rewrite**
4. En panel derecho, click **View Server Variables...**
5. Click **Add...**
6. Agregar variable: `HTTP_X_FORWARDED_FOR`
7. Click **OK**
8. Reiniciar IIS: `iisreset /restart`

---

##  Verificación

### 1. Verificar en Logs de Waitress

Después de configurar IIS, hacer login en la aplicación y revisar la consola de Waitress (o logs).

Deberías ver:

```
============================================================
  DEBUG - Headers de IP recibidos:
   request.remote_addr: 127.0.0.1

  TODOS los headers HTTP recibidos:
   HTTP_HOST: portal.evolveasesores.cl
   HTTP_X_FORWARDED_FOR: 181.161.88.222      ← ESTE DEBE APARECER
   HTTP_X_ORIGINAL_URL: /autenticacion/iniciar-sesion
   ...
============================================================

[OK] Header encontrado: HTTP_X_FORWARDED_FOR = 181.161.88.222
   [OK] IP publica encontrada: 181.161.88.222
```

### 2. Verificar en Base de Datos

Consultar la tabla `auth.sesiones_usuario`:

```sql
SELECT
    id_usuario,
    ip_cliente,
    fecha_creacion,
    activa
FROM auth.sesiones_usuario
ORDER BY fecha_creacion DESC
LIMIT 5;
```

La columna `ip_cliente` **NO** debe ser `127.0.0.1`, debe mostrar la IP real del cliente.

### 3. Verificar desde Celular/Externo

1. Conectarse desde celular (red móvil, no WiFi local)
2. Iniciar sesión en https://portal.evolveasesores.cl
3. Revisar IP registrada en base de datos

---

## 🚨 Solución de Problemas

### Problema: Aún recibo 127.0.0.1

**Posibles causas:**

1. **ARR no está habilitado correctamente**
   - Verificar en IIS Manager → Server Proxy Settings
   - Debe estar marcado "Preserve client IP in the following header: X-Forwarded-For"

2. **web.config tiene problemas de sintaxis**
   - Validar XML con editor
   - No debe haber reglas conflictivas

3. **IIS no reinició correctamente**
   - Ejecutar: `iisreset /restart`
   - Verificar que servicio NSSM también reinició: `nssm restart evolve-soluciones`

4. **Múltiples proxies en cadena**
   - Si hay load balancer o CDN antes de IIS, ajustar `ProxyFix`:
   ```python
   # En wsgi_waitress.py y aplicacion.py
   from werkzeug.middleware.proxy_fix import ProxyFix
   app.wsgi_app = ProxyFix(
       app.wsgi_app,
       x_for=2,      # Cambiar a 2 o más si hay múltiples proxies
       x_proto=1,
       x_host=1,
       x_prefix=1
   )
   ```

### Problema: Headers HTTP_X_FORWARDED_FOR no aparecen en logs

- IIS no está enviando el header
- Revisar configuración ARR Server Proxy Settings
- Probar método 2 (agregar header manualmente con serverVariables)

### Problema: Error 500 después de modificar web.config

- Sintaxis XML incorrecta
- Falta habilitar server variable `HTTP_X_FORWARDED_FOR` en IIS URL Rewrite
- Restaurar backup de web.config y probar método 1 primero

---

## 📝 Checklist Final

- [ ] ARR instalado en IIS
- [ ] Server Proxy Settings → "Preserve client IP" habilitado
- [ ] web.config tiene regla de rewrite correcta
- [ ] Server variable HTTP_X_FORWARDED_FOR agregada (si método 2)
- [ ] IIS reiniciado (`iisreset /restart`)
- [ ] Servicio NSSM reiniciado (`nssm restart evolve-soluciones`)
- [ ] Logs de Waitress muestran header HTTP_X_FORWARDED_FOR
- [ ] Base de datos registra IP real, no 127.0.0.1
- [ ] Prueba desde celular/red externa exitosa

---

## 🔗 Referencias

- [IIS ARR Documentation](https://learn.microsoft.com/en-us/iis/extensions/planning-for-arr/application-request-routing-version-2-overview)
- [Werkzeug ProxyFix](https://werkzeug.palletsprojects.com/en/3.0.x/middleware/proxy_fix/)
- [Flask Behind Proxy](https://flask.palletsprojects.com/en/3.0.x/deploying/proxy_fix/)

---

**Última actualización:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
