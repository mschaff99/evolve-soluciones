from fastapi import HTTPException, status


class CredencialesInvalidas(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )


class UsuarioInactivo(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )


class RecursoNoEncontrado(HTTPException):
    def __init__(self, recurso: str = "Recurso"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{recurso} no encontrado",
        )


class ModuloNoHabilitado(HTTPException):
    def __init__(self, modulo: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Modulo '{modulo}' no habilitado",
        )
