import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise RuntimeError("Falta DATABASE_URL en el archivo .env")


def conectar():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

app = FastAPI(title="API de libros")

ARCHIVO = Path(__file__).parent / "libros.json"


class Libro(BaseModel):
    """Campos de un libro, sin el id (lo calcula la API)."""
    titulo: str
    autor: str
    paginas: int
    leido: bool = False


def cargar() -> list[dict]:
    with open(ARCHIVO, encoding="utf-8") as f:
        return json.load(f)


def guardar(libros: list[dict]) -> None:
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(libros, f, ensure_ascii=False, indent=2)


def no_encontrado(libro_id: int) -> HTTPException:
    return HTTPException(status_code=404, detail=f"No existe el libro con id {libro_id}")


@app.get("/libros")
def listar_libros():
    return cargar()


@app.get("/libros/{libro_id}")
def obtener_libro(libro_id: int):
    for libro in cargar():
        if libro["id"] == libro_id:
            return libro
    raise no_encontrado(libro_id)


@app.post("/libros", status_code=201)
def agregar_libro(nuevo: Libro):
    libros = cargar()
    nuevo_id = max((l["id"] for l in libros), default=0) + 1
    libro = {"id": nuevo_id, **nuevo.model_dump()}
    libros.append(libro)
    guardar(libros)
    return libro


@app.put("/libros/{libro_id}")
def editar_libro(libro_id: int, datos: Libro):
    libros = cargar()
    for i, libro in enumerate(libros):
        if libro["id"] == libro_id:
            libros[i] = {"id": libro_id, **datos.model_dump()}
            guardar(libros)
            return libros[i]
    raise no_encontrado(libro_id)


@app.delete("/libros/{libro_id}")
def borrar_libro(libro_id: int):
    libros = cargar()
    for i, libro in enumerate(libros):
        if libro["id"] == libro_id:
            borrado = libros.pop(i)
            guardar(libros)
            return borrado
    raise no_encontrado(libro_id)