import requests
from fastapi import FastAPI, HTTPException, Request
from modelos.api_bd.modelos_bd import PrizeUpdate, Prize

# Define una variable global para la URL base
BASE_URL = "http://0.0.0.0:8001"

app = FastAPI()


@app.get("/")
async def root(request: Request):
    respuesta = requests.get(f"{BASE_URL}/")
    return respuesta.json()


@app.get("/prizes/{year}/{category}")
async def get_prizes_by_year_and_category(year: int, category: str, request: Request):
    respuesta = requests.get(f"{BASE_URL}/prizes/{year}/{category}/")
    return respuesta.json()


@app.get("/prizes/{year}")
async def get_prizes_by_year(year: int, request: Request):
    respuesta = requests.get(f"{BASE_URL}/prizes/{year}")
    return respuesta.json()


@app.put("/prizes/{year}/{category}")
async def update_prize(year: int, category: str, prize_update: PrizeUpdate, request: Request):
    # Convertimos el modelo prize_update a un diccionario JSON
    body = prize_update.model_dump(exclude_none=True)

    # Hacemos la solicitud PUT al endpoint externo con el cuerpo JSON
    respuesta = requests.put(f"{BASE_URL}/prizes/{year}/{category}", json=body)

    # Devolvemos la respuesta en formato JSON
    return respuesta.json()

@app.delete("/prizes/{year}/{category}")
async def delete_prize(year: int, category: str, request: Request):
    # Hacemos la solicitud DELETE al endpoint externo
    respuesta = requests.delete(f"{BASE_URL}/prizes/{year}/{category}")

    # Validamos si el recurso fue eliminado exitosamente
    if respuesta.status_code != 200:
        raise HTTPException(status_code=respuesta.status_code, detail=respuesta.text)

    # Devolvemos la respuesta en formato JSON
    return {"detail": "Premio eliminado exitosamente."}


@app.post("/prize")
async def create_prize(prize: Prize, request: Request):
    # Convertimos el modelo prize a un diccionario JSON
    body = prize.model_dump(exclude_none=True)

    # Hacemos la solicitud POST al endpoint externo con el cuerpo JSON
    respuesta = requests.post(f"{BASE_URL}/prizes", json=body)

    # Si hay algún error en la solicitud, levantamos una excepción HTTP
    if respuesta.status_code != 200:
        raise HTTPException(status_code=respuesta.status_code, detail=respuesta.text)

    # Devolvemos la respuesta en formato JSON
    return respuesta.json()
