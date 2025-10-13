"""
Utilidades para Filtrar Empresas por Usuario
============================================

Funciones helper para aplicar filtros de acceso basados en el rol
y nombre de usuario (columna auditor en MySQL).
"""

def construir_filtro_auditor(usuario):
    """
    Construye la cláusula WHERE para filtrar empresas según el usuario

    Args:
        usuario: Instancia de Usuario (con nombre_usuario y rol)

    Returns:
        tuple: (where_clause, parametros)

    Ejemplos:
        # Usuario admin:
        ("", ())  # Sin filtro, ve todo

        # Usuario normal:
        ("WHERE auditor = %s", ("ALEXEI",))
    """
    # Si es administrador, puede ver todo
    if usuario.es_administrador():
        return ("", ())

    # Si es usuario normal, solo ve sus empresas
    return ("WHERE auditor = %s", (usuario.nombre_usuario,))


def construir_filtro_and_auditor(usuario):
    """
    Construye la cláusula AND para filtrar empresas (cuando ya hay WHERE)

    Args:
        usuario: Instancia de Usuario

    Returns:
        tuple: (and_clause, parametros)

    Ejemplo:
        # En una query que ya tiene WHERE:
        consulta = "SELECT * FROM empresas WHERE activo = 1"
        and_clause, params = construir_filtro_and_auditor(usuario)
        consulta += and_clause
    """
    # Si es administrador, no agrega filtro
    if usuario.es_administrador():
        return ("", ())

    # Si es usuario normal, agrega filtro AND
    return (" AND auditor = %s", (usuario.nombre_usuario,))


def obtener_empresas_usuario(usuario, conexion=None, campos="*", condiciones_extra=""):
    """
    Obtiene las empresas accesibles por el usuario en SU base de datos MySQL asignada

    Args:
        usuario: Instancia de Usuario (debe tener base_datos_mysql configurada)
        conexion: Conexión MySQL (opcional, si no se pasa se crea una nueva)
        campos: Campos a seleccionar (default: "*")
        condiciones_extra: WHERE adicional (ej: "AND activo = 1")

    Returns:
        list: Lista de empresas

    Ejemplo:
        from flask_login import current_user
        from aplicacion.utilidades.filtros_empresas import obtener_empresas_usuario

        # Si current_user.base_datos_mysql = "stratex"
        # → Busca en MySQL database 'stratex'
        empresas = obtener_empresas_usuario(
            current_user,
            campos="run_rut, empresa, auditor",
            condiciones_extra="AND grupo = 'A'"
        )
    """
    from aplicacion.modelos.base_datos import obtener_conexion_local
    import pymysql

    # Crear conexión si no se proporcionó (usando la BD del usuario)
    cerrar_conexion = False
    if not conexion:
        # Usar la base de datos asignada al usuario
        base_datos = usuario.base_datos_mysql if hasattr(usuario, 'base_datos_mysql') and usuario.base_datos_mysql else 'stratex'
        conexion = obtener_conexion_local(base_datos)
        cerrar_conexion = True

    try:
        # Construir consulta base
        consulta = f"SELECT {campos} FROM empresas"

        # Construir filtro según usuario
        where_clause, params = construir_filtro_auditor(usuario)

        # Agregar condiciones extra si existen
        if condiciones_extra:
            if where_clause:
                consulta += f" {where_clause} {condiciones_extra}"
                # No agregar más parámetros si condiciones_extra no los necesita
            else:
                consulta += f" WHERE {condiciones_extra.replace('AND ', '')}"
        else:
            consulta += f" {where_clause}"

        # Ejecutar consulta
        with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            if params:
                cursor.execute(consulta, params)
            else:
                cursor.execute(consulta)

            return cursor.fetchall()

    finally:
        if cerrar_conexion:
            conexion.close()


def puede_acceder_empresa(usuario, run_rut_empresa, conexion=None):
    """
    Verifica si un usuario puede acceder a una empresa específica en SU base de datos

    Args:
        usuario: Instancia de Usuario (con base_datos_mysql configurada)
        run_rut_empresa: RUT de la empresa a verificar
        conexion: Conexión MySQL (opcional)

    Returns:
        bool: True si puede acceder, False si no

    Ejemplo:
        if not puede_acceder_empresa(current_user, "76244083-0"):
            flash("No tienes permisos para ver esta empresa", "error")
            return redirect(url_for('dashboard'))
    """
    from aplicacion.modelos.base_datos import obtener_conexion_local
    import pymysql

    # Administradores pueden acceder a todo (en su BD)
    if usuario.es_administrador():
        return True

    # Crear conexión si no se proporcionó (usando la BD del usuario)
    cerrar_conexion = False
    if not conexion:
        base_datos = usuario.base_datos_mysql if hasattr(usuario, 'base_datos_mysql') and usuario.base_datos_mysql else 'stratex'
        conexion = obtener_conexion_local(base_datos)
        cerrar_conexion = True

    try:
        consulta = """
            SELECT COUNT(*) as total
            FROM empresas
            WHERE run_rut = %s AND auditor = %s
        """

        with conexion.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(consulta, (run_rut_empresa, usuario.nombre_usuario))
            resultado = cursor.fetchone()

            # Verificar que resultado no sea None
            return resultado['total'] > 0 if resultado else False

    finally:
        if cerrar_conexion:
            conexion.close()
