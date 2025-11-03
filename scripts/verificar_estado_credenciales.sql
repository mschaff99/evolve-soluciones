-- Script para verificar y actualizar estados de credenciales en la BD
-- 1. Ver todas las credenciales y sus estados
SELECT id,
    rut,
    estado,
    fecha_creacion,
    fecha_actualizacion
FROM credenciales_sii
ORDER BY rut;
-- 2. Contar credenciales por estado
SELECT estado,
    COUNT(*) as total
FROM credenciales_sii
GROUP BY estado;
-- 3. Para PRUEBAS: Actualizar una credencial a estado 'F' (cambiar RUT según necesites)
-- UNCOMMENT para usar:
-- UPDATE credenciales_sii
-- SET estado = 'F', fecha_actualizacion = NOW()
-- WHERE rut = '76804890-8';
-- 4. Verificar que se actualizó
-- SELECT rut, estado, fecha_actualizacion FROM credenciales_sii WHERE rut = '76804890-8';
-- 5. Para revertir a 'V' (Vigente):
-- UPDATE credenciales_sii
-- SET estado = 'V', fecha_actualizacion = NOW()
-- WHERE rut = '76804890-8';
