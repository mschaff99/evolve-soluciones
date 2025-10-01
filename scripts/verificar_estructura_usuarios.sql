-- Verificar estructura de la tabla usuarios
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'auth' 
AND table_name = 'usuarios'
ORDER BY ordinal_position;
