import secrets

import requests
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from requests.auth import HTTPBasicAuth

from modelos.api_bd.modelos_bd import PrizeUpdate, Prize

# Define una variable global para la URL base
BASE_URL = "http://192.168.1.11:8001"

app = FastAPI()

# Configuración de autenticación Basic
security = HTTPBasic()

# Base de datos simulada de usuarios con roles
USUARIOS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
}


# Función para verificar las credenciales y obtener el rol del usuario
def verificar_credenciales(
        credenciales: HTTPBasicCredentials = Depends(security)
) -> dict:
    usuario = USUARIOS.get(credenciales.username)
    if not usuario or not secrets.compare_digest(credenciales.password, usuario["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"username": credenciales.username, "role": usuario["role"]}


def verificar_permiso(*roles_requeridos: str):
    def permiso_checker(usuario: dict = Depends(verificar_credenciales)):
        # Admin bypass
        if usuario["role"] == "admin":
            return usuario

        # Check against allowed roles
        if usuario["role"] not in roles_requeridos:
            allowed = ", ".join(roles_requeridos)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Se requiere uno de los roles: {allowed}"
            )
        return usuario

    return permiso_checker


@app.get("/")
async def root(request: Request):
    """
    Endpoint raíz de la API.
    - **Acceso:** Público, no requiere autenticación.
    - **Descripción:** Reenvía una solicitud al servidor final para obtener la respuesta de la raíz.
    """
    auth = HTTPBasicAuth("lector", "lector1234")
    respuesta = requests.get(f"{BASE_URL}/", auth=auth)
    return respuesta.json()


@app.get("/prizes/{year}/{category}")
async def get_prizes_by_year_and_category(
        year: int, category: str, request: Request, usuario: dict = Depends(verificar_permiso("user"))
):
    """
    Obtiene premios por año y categoría.
    - **Acceso:** Permitido para todos los usuarios autenticados (`user` y `admin`).
    - **Descripción:** Este endpoint reenvía una solicitud al servidor final para obtener los premios relacionados con el año y la categoría especificados.
    """
    auth = None
    if usuario["role"] == "admin":
        auth = HTTPBasicAuth("admin", "admin1234")
    if usuario["role"] == "user":
        auth = HTTPBasicAuth("lector", "lector1234")

    respuesta = requests.get(f"{BASE_URL}/prizes/{year}/{category}/", auth=auth)
    return respuesta.json()


@app.get("/prizes/{year}")
async def get_prizes_by_year(
        year: int, request: Request, usuario: dict = Depends(verificar_permiso("user"))
):
    """
    Obtiene premios por año.
    - **Acceso:** Permitido para todos los usuarios autenticados (`user` y `admin`).
    - **Descripción:** Este endpoint reenvía una solicitud al servidor final para obtener los premios relacionados con el año especificado.
    """
    auth = None
    if usuario["role"] == "admin":
        auth = HTTPBasicAuth("admin", "admin1234")
    if usuario["role"] == "user":
        auth = HTTPBasicAuth("lector", "lector1234")
    respuesta = requests.get(f"{BASE_URL}/prizes/{year}", auth=auth)
    return respuesta.json()


@app.put("/prizes/{year}/{category}")
async def update_prize(
        year: int,
        category: str,
        prize_update: PrizeUpdate,
        request: Request,
        usuario: dict = Depends(verificar_permiso()),  # Solo admin puede usar este endpoint
):
    """
    Actualiza un premio específico.
    - **Acceso:** Solo permitido para usuarios con rol `admin`.
    - **Descripción:** Este endpoint permite a los administradores actualizar la información de un premio especificando el año y la categoría.
    """
    auth = None
    if usuario["role"] == "admin":
        auth = HTTPBasicAuth("admin", "admin1234")
    body = prize_update.model_dump(exclude_none=True)
    respuesta = requests.put(f"{BASE_URL}/prizes/{year}/{category}", json=body, auth=auth)
    return respuesta.json()


@app.delete("/prizes/{year}/{category}")
async def delete_prize(
        year: int,
        category: str,
        request: Request,
        usuario: dict = Depends(verificar_permiso()),  # Solo admin puede usar este endpoint
):
    """
    Elimina un premio específico.
    - **Acceso:** Solo permitido para usuarios con rol `admin`.
    - **Descripción:** Este endpoint permite a los administradores eliminar un premio especificando el año y la categoría.
    """
    auth = None
    if usuario["role"] == "admin":
        auth = HTTPBasicAuth("admin", "admin1234")
    respuesta = requests.delete(f"{BASE_URL}/prizes/{year}/{category}", auth=auth)
    if respuesta.status_code != 200:
        raise HTTPException(status_code=respuesta.status_code, detail=respuesta.text)
    return {"detail": "Premio eliminado exitosamente."}


@app.post("/prize")
async def create_prize(
        prize: Prize,
        request: Request,
        usuario: dict = Depends(verificar_permiso()),  # Solo admin puede usar este endpoint
):
    """
    Crea un nuevo premio.
    - **Acceso:** Solo permitido para usuarios con rol `admin`.
    - **Descripción:** Este endpoint permite a los administradores crear un nuevo premio en el servidor final.
    """
    auth = None
    if usuario["role"] == "admin":
        auth = HTTPBasicAuth("admin", "admin1234")
    body = prize.model_dump(exclude_none=True)
    respuesta = requests.post(f"{BASE_URL}/prize", json=body, auth=auth)
    if respuesta.status_code != 200:
        raise HTTPException(status_code=respuesta.status_code, detail=respuesta.text)
    return respuesta.json()
