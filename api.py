from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
async def root():
    respuesta = requests.get("http://localhost:8001/")
    return respuesta.json()