from fastapi import FastAPI, HTTPException, Query, Request # type: ignore
from pydantic import BaseModel, Field # type: ignore
from typing import List, Optional
from fastapi.responses import HTMLResponse # type: ignore
from fastapi.templating import Jinja2Templates # type: ignore
import random
from datetime import datetime  # Importa datetime para obtener la fecha y hora actual


app = FastAPI()

# Modelo de datos para las solicitudes POST
class PostData(BaseModel):
    DNI: str = Field(..., example="12345678")
    Dificultad: int = Field(..., ge=1, le=5, example=3)
    NumBandera: int = Field(..., ge=0, example=5)
    codigo: str = Field(..., example="examplecode")
    timestamp: datetime = Field(default_factory=datetime.now)  # Campo para almacenar la fecha y hora de la publicación

# Almacenamiento en memoria para las entradas POST
posts_db = []

# Configuración de las plantillas Jinja2
templates = Jinja2Templates(directory="templates")

@app.post("/post/", response_model=PostData)
def create_post(data: PostData):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data.timestamp = timestamp
    posts_db.append(data)
    return data

@app.get("/get/", response_model=List[PostData])
def read_posts(dni: Optional[str] = Query(None, example="12345678")):
    if dni:
        filtered_posts = [post for post in posts_db if post.DNI == dni]
        if not filtered_posts:
            raise HTTPException(status_code=404, detail="No se encontraron entradas para el DNI especificado")
        return filtered_posts
    return posts_db

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    sorted_posts = sorted(posts_db, key=lambda post: (post.DNI, post.Dificultad, post.NumBandera))
    colored_posts = colorize_posts(sorted_posts)
    return templates.TemplateResponse("index.html", {"request": request, "posts": colored_posts})

def colorize_posts(posts):
    colored_posts = []
    prev_dni = None
    color = None
    for post in posts:
        if post.DNI != prev_dni:
            # Cambiar el color para un nuevo DNI
            color = random_light_color()
            prev_dni = post.DNI
        # Formatear el timestamp usando strftime
        colored_posts.append({"DNI": post.DNI, "Dificultad": post.Dificultad, "NumBandera": post.NumBandera, "codigo": post.codigo, "timestamp": post.timestamp, "color": color})
    return colored_posts

def random_light_color():
    r = random.randint(200, 255)
    g = random.randint(200, 255)
    b = random.randint(200, 255)
    return f"rgb({r}, {g}, {b})"

@app.delete("/delete/{index}")
def delete_post(index: int):
    try:
        del posts_db[index]
        return {"message": "Entrada eliminada correctamente"}
    except IndexError:
        raise HTTPException(status_code=404, detail="Índice fuera de rango")

@app.delete("/delete_all")
def delete_all_posts():
    posts_db.clear()
    return {"message": "Todas las entradas eliminadas correctamente"}

# Inicia el servidor con: uvicorn main:app --reload