from os import path, makedirs
from contextlib import asynccontextmanager
import requests
from fastapi import FastAPI, HTTPException
from json import dump


def cargaInicialBd():
    ruta_archivo = "./datos/bd.json"
    url_externa = "https://api.nobelprize.org/v1/prize.json"

    makedirs(path.dirname(ruta_archivo), exist_ok=True)
    if not path.isfile(ruta_archivo):
        try:
            print(f"Archivo no encontrado. Descargando desde {url_externa}...")
            response = requests.get(url_externa)
            response.raise_for_status()

            with open(ruta_archivo, "w", encoding="utf-8") as f:
                dump(response.json(), f, indent=4, ensure_ascii=False)

            print("Archivo descargado y guardado correctamente.")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"No se pudo obtener el archivo desde {url_externa}: {str(e)}"
            )


@asynccontextmanager
async def lifespan(_: FastAPI):
    cargaInicialBd()
    yield
    print("API BD Terminada.")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello World!!!"}