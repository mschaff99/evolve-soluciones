# 🚀 Guía Rápida - Sistema de Permisos Módulo IA

## ⚡ Instalación (Una vez)

```powershell
# 1. Ejecutar migración en PostgreSQL
psql -U postgres -d evolve_auth -f migraciones/008_habilitar_modulo_ia.sql

# 2. Verificar instalación
psql -U postgres -d evolve_auth -c "SELECT * FROM auth.vista_modulos_habilitados WHERE codigo_modulo = 'ia';"
```

## 🎯 Comandos Más Usados

### Ver estado actual
```powershell
python scripts/gestionar_modulo_ia.py listar
```

### Habilitar IA para un cliente
```powershell
python scripts/gestionar_modulo_ia.py habilitar nombre_base_datos
```

### Deshabilitar IA
```powershell
python scripts/gestionar_modulo_ia.py deshabilitar nombre_base_datos
```

## 📋 Consultas SQL Útiles

```sql
-- Ver qué clientes tienen IA
SELECT
    bd.nombre_base_datos,
    bd.nombre_cliente,
    bd.plan,
    mh.habilitado
FROM auth.bases_datos_mysql bd
LEFT JOIN auth.modulos_habilitados_bd mh ON bd.id = mh.id_base_datos
LEFT JOIN auth.modulos_sistema m ON mh.id_modulo = m.id AND m.codigo = 'ia'
WHERE bd.activo = TRUE
ORDER BY bd.nombre_base_datos;

-- Habilitar IA para una BD específica
SELECT auth.toggle_modulo_ia('nombre_bd', TRUE);

-- Deshabilitar IA
SELECT auth.toggle_modulo_ia('nombre_bd', FALSE);

-- Ver usuarios con acceso a IA
SELECT DISTINCT u.nombre_usuario, u.base_datos_mysql, bd.nombre_cliente
FROM auth.usuarios u
INNER JOIN auth.bases_datos_mysql bd ON u.base_datos_mysql = bd.nombre_base_datos
INNER JOIN auth.modulos_habilitados_bd mh ON bd.id = mh.id_base_datos
INNER JOIN auth.modulos_sistema m ON mh.id_modulo = m.id
WHERE m.codigo = 'ia' AND mh.habilitado = TRUE AND u.activo = TRUE;
```

##  Checklist Post-Instalación

- [ ] Migración ejecutada sin errores
- [ ] BDs `stratex` y `evolve` tienen IA habilitado por defecto
- [ ] Script `gestionar_modulo_ia.py` funciona correctamente
- [ ] Interface web muestra/oculta botón IA según permisos
- [ ] Intentar acceder sin permisos redirige correctamente

## 🔍 Troubleshooting

**Problema**: Usuario no ve el módulo IA
```sql
-- Verificar permisos del usuario
SELECT u.nombre_usuario, u.base_datos_mysql,
       auth.modulo_habilitado(u.base_datos_mysql, 'ia') as tiene_ia
FROM auth.usuarios u
WHERE u.nombre_usuario = 'nombre_usuario_aqui';
```

**Problema**: Script de gestión falla
```powershell
# Verificar que la app se puede iniciar
python -c "from aplicacion import crear_aplicacion; app = crear_aplicacion(); print('OK')"
```

**Problema**: Cambios no se reflejan
- Los cambios son inmediatos, NO requiere reiniciar
- Refrescar el navegador (Ctrl+F5)
- Verificar en PostgreSQL que el cambio se guardó

## 📚 Documentación Completa

Ver: `documentacion/MODULO_IA_PERMISOS.md`
