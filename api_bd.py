import json
import secrets
from contextlib import asynccontextmanager
from json import dump, load
from os import path, makedirs

import requests
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from api import security
from modelos.api_bd.modelos_bd import PrizesResponse, PrizeUpdate, Prize, Laureate

ARCHIVO_BD = "./datos/bd.json"
URL_DATOS = "https://api.nobelprize.org/v1/prize.json"

# Base de datos simulada de usuarios con roles
USUARIOS = {
    "lector": {"password": "lector1234", "role": "lector"},
    "admin": {"password": "admin1234", "role": "admin"},
}


def verificar_credenciales(credenciales: HTTPBasicCredentials = Depends(security)) -> dict:
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

        if usuario["role"] == "admin":
            return usuario

        if usuario["role"] not in roles_requeridos:
            allowed = ", ".join(roles_requeridos)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Se requiere uno de los roles: {allowed}"
            )
        return usuario

    return permiso_checker


def descargar_datos_si_no_existe(ruta_archivo: str):
    """
    Descarga el archivo de datos desde la URL especificada solo si no existe previamente en la ruta dada.

    Si el archivo ya existe en la ruta indicada, no realiza ninguna descarga y utiliza el archivo existente.
    Si el archivo no está presente, realiza una solicitud HTTP para obtener los datos y los guarda en formato JSON.
    Si ocurre un error durante la descarga, lanza una excepción HTTP.

    Parámetros:
        ruta_archivo (str): Ruta donde se debe verificar y/o guardar el archivo de datos.
    """
    makedirs(path.dirname(ruta_archivo), exist_ok=True)

    if not path.isfile(ruta_archivo):
        try:
            print(f"Archivo no encontrado. Descargando desde {URL_DATOS}...")
            respuesta = requests.get(URL_DATOS)
            respuesta.raise_for_status()

            with open(ruta_archivo, "w", encoding="utf-8") as archivo:
                dump(respuesta.json(), archivo, indent=4, ensure_ascii=False)

            print("Archivo descargado y guardado exitosamente.")
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"No se pudo obtener el archivo desde {URL_DATOS}: {str(e)}")
    else:
        print(f"El archivo ya existe en {ruta_archivo}. Usando el archivo existente.")


def cargar_datos_desde_archivo(ruta_archivo: str) -> PrizesResponse:
    """
    Carga y valida los datos desde un archivo JSON en la ruta especificada.

    Abre el archivo, carga su contenido y lo valida usando el modelo PrizesResponse.
    Si ocurre un error al leer o validar los datos, lanza una excepción HTTP.

    Parámetros:
        ruta_archivo (str): Ruta del archivo JSON a cargar.

    Retorna:
        PrizesResponse: Objeto validado con los datos cargados.
    """
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            return PrizesResponse.model_validate(load(f))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar los datos desde {ruta_archivo}: {str(e)}")


def guardar_datos_nobel_en_archivo(datos_nobel: PrizesResponse):
    """
    Serializa y escribe los datos de Premios Nobel en disco en formato JSON.

    Argumentos:
        datos_nobel (PrizesResponse): Modelo Pydantic que contiene la lista de premios Nobel a guardar.

    Retorna:
        None
    """
    with open(ARCHIVO_BD, "w", encoding="utf-8") as f:
        json.dump(datos_nobel.model_dump(), f, ensure_ascii=False, indent=2)


def get_max_laureate_id(laureates: list[Laureate]) -> int:
    """
    Devuelve el siguiente ID de laureado tomando el máximo existente + 1.
    """
    return max((l.id for l in laureates), default=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    descargar_datos_si_no_existe(ARCHIVO_BD)
    app.state.datos_nobel = cargar_datos_desde_archivo(ARCHIVO_BD)
    yield
    print("API finalizada.")


app = FastAPI(lifespan=lifespan)

# Configuración de autenticación Basic
security = HTTPBasic()


@app.get("/")
async def root(request: Request, usuario: dict = Depends(verificar_permiso("lector"))):
    datos_nobel: PrizesResponse = request.app.state.datos_nobel

    return datos_nobel.model_dump(exclude_none=True)


@app.get("/prizes/{year}/{category}")
async def get_prizes_by_year_and_category(year: int, category: str, request: Request,
                                          usuario: dict = Depends(verificar_permiso("lector", "admin"))):
    datos_nobel: PrizesResponse = request.app.state.datos_nobel

    # Filtrar los premios por año y categoría
    premios_filtrados = [premio for premio in datos_nobel.prizes if
                         premio.year == year and premio.category.lower() == category.lower()]

    if not premios_filtrados:
        raise HTTPException(status_code=404,
                            detail="No se encontraron premios para el año y la categoria especificada.")

    return [prize.model_dump(exclude_none=True) for prize in premios_filtrados]


@app.get("/prizes/{year}")
async def get_prizes_by_year(year: int, request: Request,
                             usuario: dict = Depends(verificar_permiso("lector", "admin"))):
    datos_nobel: PrizesResponse = request.app.state.datos_nobel

    # Filtrar los premios por año y categoría
    premios_filtrados = [premio for premio in datos_nobel.prizes if premio.year == year]

    if not premios_filtrados:
        raise HTTPException(status_code=404, detail="No se encontraron premios para el año solicitado.")

    return [prize.model_dump(exclude_none=True) for prize in premios_filtrados]


@app.put("/prizes/{year}/{category}")
async def update_prize(year: int, category: str, prize_update: PrizeUpdate, request: Request,
                       usuario: dict = Depends(verificar_permiso("admin"))):
    datos_nobel: PrizesResponse = request.app.state.datos_nobel

    # Encuentro el primer premio que coincida con el año y la categoría
    premio = next((p for p in datos_nobel.prizes if p.year == year and p.category.lower() == category), None)

    if not premio:
        raise HTTPException(status_code=404,
                            detail="No se encontró el premio para el año y la categoría especificados.")

    # Actualizar overallMotivation si se proporciona
    if prize_update.overallMotivation is not None:
        premio.overallMotivation = prize_update.overallMotivation

    # Actualizar atributos del premio
    if prize_update.laureates:
        for laureate_update in prize_update.laureates:
            laureate = next((l for l in premio.laureates if l.id == laureate_update.id), None)
            if laureate:
                # Actualizar atributos del laureado
                for attr, value in laureate_update.model_dump(exclude_unset=True).items():
                    setattr(laureate, attr, value)
            else:
                raise HTTPException(status_code=404,
                                    detail=f"El laureado de ID: {laureate_update.id} no fue encontrado.")

    guardar_datos_nobel_en_archivo(datos_nobel)

    return premio


@app.delete("/prizes/{year}/{category}")
async def delete_prize(year: int, category: str, request: Request, usuario: dict = Depends(verificar_permiso("admin"))):
    datos_nobel: PrizesResponse = request.app.state.datos_nobel

    # Encuentro el primer premio que coincida con el año y la categoría
    premio = next((p for p in datos_nobel.prizes if p.year == year and p.category.lower() == category), None)

    if not premio:
        raise HTTPException(status_code=404,
                            detail="No se encontró el premio para el año y la categoría especificados.")

    # Eliminar el premio de la lista
    datos_nobel.prizes.remove(premio)

    guardar_datos_nobel_en_archivo(datos_nobel)

    return {"detail": "Premio eliminado exitosamente."}


@app.post("/prize")
async def create_prize(prize: Prize, request: Request, usuario: dict = Depends(verificar_permiso("admin"))):
    datos_nobel: PrizesResponse = request.app.state.datos_nobel

    # Calculamos el ID inicial basándonos en los laureados existentes en todos los premios
    laureates = [l for p in datos_nobel.prizes for l in p.laureates]
    max_id = get_max_laureate_id(laureates)

    # Asignamos IDs secuenciales a los nuevos laureados
    nuevos_laureados = []

    for laureado in prize.laureates:
        max_id += 1
        laureado.id = max_id
        nuevos_laureados.append(laureado)

    # Crear un nuevo premio
    nuevo_premio = Prize(year=prize.year, category=prize.category, laureates=nuevos_laureados,
                         overallMotivation=prize.overallMotivation)

    # Agregar el nuevo premio a la lista de premios
    datos_nobel.prizes.append(nuevo_premio)

    guardar_datos_nobel_en_archivo(datos_nobel)

    return nuevo_premio.model_dump(exclude_none=True)
