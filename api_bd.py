from os import path, makedirs
from contextlib import asynccontextmanager
import requests
from fastapi import FastAPI, HTTPException, Request
from json import dump, load
from modelos.api_bd.modelos_bd import PrizesResponse

ARCHIVO_BD = "./datos/bd.json"
URL_DATOS = "https://api.nobelprize.org/v1/prize.json"


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
            raise HTTPException(
                status_code=500,
                detail=f"No se pudo obtener el archivo desde {URL_DATOS}: {str(e)}"
            )
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
        raise HTTPException(
            status_code=500,
            detail=f"Error al cargar los datos desde {ruta_archivo}: {str(e)}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    descargar_datos_si_no_existe(ARCHIVO_BD)
    app.state.datos_nobel = cargar_datos_desde_archivo(ARCHIVO_BD)
    yield
    print("API finalizada.")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root(request: Request):
    datos_nobel: PrizesResponse = request.app.state.datos_nobel

    return datos_nobel.model_dump(exclude_none=True)


@app.get("/prizes/{year}/{category}")
async def get_prizes_by_year_and_category(year: int, category: str, request: Request):
    datos_nobel: PrizesResponse = request.app.state.datos_nobel

    # Filtrar los premios por año y categoría
    premios_filtrados = [
        premio for premio in datos_nobel.prizes
        if premio.year == year and premio.category.lower() == category.lower()
    ]

    if not premios_filtrados:
        raise HTTPException(status_code=404, detail="No se encontraron premios para el año y la categoria especificada.")

    return [prize.model_dump(exclude_none=True) for prize in premios_filtrados]


@app.get("/prizes/{year}")
async def get_prizes_by_year(year: int, request: Request):
    datos_nobel: PrizesResponse = request.app.state.datos_nobel

    # Filtrar los premios por año y categoría
    premios_filtrados = [ premio for premio in datos_nobel.prizes if premio.year == year ]

    if not premios_filtrados:
        raise HTTPException(status_code=404, detail="No se encontraron premios para el año solicitado.")

    return [prize.model_dump(exclude_none=True) for prize in premios_filtrados]