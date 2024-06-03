from fastapi import FastAPI, HTTPException, Query, Request, Depends # type: ignore
from pydantic import BaseModel, Field # type: ignore
from typing import List, Optional
from fastapi.responses import HTMLResponse # type: ignore
from fastapi.templating import Jinja2Templates # type: ignore
import random
from datetime import datetime
import sqlite3

app = FastAPI()

# Crear la tabla en la base de datos si no existe
conn = sqlite3.connect('posts.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY,
        DNI TEXT,
        Dificultad INTEGER,
        NumBandera INTEGER,
        codigo TEXT,
        timestamp TEXT
    )
''')
conn.commit()

# Configuración de las plantillas Jinja2
templates = Jinja2Templates(directory="templates")

class PostData(BaseModel):
    DNI: str = Field(..., example="12345678")
    Dificultad: int = Field(..., ge=1, le=5, example=3)
    NumBandera: int = Field(..., ge=0, example=5)
    codigo: str = Field(..., example="examplecode")
    timestamp: datetime = Field(default_factory=datetime.now)

def colorize_posts(posts):
    colored_posts = []
    prev_dni = None
    color = None
    for post in posts:
        if post.DNI != prev_dni:
            color = random_light_color()
            prev_dni = post.DNI
        colored_posts.append({"DNI": post.DNI, "Dificultad": post.Dificultad, "NumBandera": post.NumBandera, "codigo": post.codigo, "timestamp": post.timestamp, "color": color})
    return colored_posts

def random_light_color():
    r = random.randint(200, 255)
    g = random.randint(200, 255)
    b = random.randint(200, 255)
    return f"rgb({r}, {g}, {b})"

@app.post("/post/", response_model=PostData)
def create_post(data: PostData):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO posts (DNI, Dificultad, NumBandera, codigo, timestamp) VALUES (?, ?, ?, ?, ?)",
                 (data.DNI, data.Dificultad, data.NumBandera, data.codigo, timestamp))
    new_id = cursor.lastrowid  # Obtener el ID de la fila insertada
    conn.commit()
    conn.close()
    return PostData(id=new_id, **data.dict())  # Crear una nueva instancia de PostData con el ID correcto


@app.get("/get/", response_model=List[PostData])
def read_posts(dni: Optional[str] = Query(None, example="12345678")):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    if dni:
        cursor.execute("SELECT * FROM posts WHERE DNI = ?", (dni,))
    else:
        cursor.execute("SELECT * FROM posts")
    fetched_posts = cursor.fetchall()
    conn.close()
    if not fetched_posts:
        raise HTTPException(status_code=404, detail="No se encontraron entradas")
    return [PostData(id=post[0], DNI=post[1], Dificultad=post[2], NumBandera=post[3], codigo=post[4], timestamp=post[5]) for post in fetched_posts]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts")
    fetched_posts = cursor.fetchall()
    sorted_posts = [PostData(id=post[0], DNI=post[1], Dificultad=post[2], NumBandera=post[3], codigo=post[4], timestamp=post[5]) for post in fetched_posts]
    colored_posts = colorize_posts(sorted_posts)
    indexed_posts = [(index, post) for index, post in enumerate(colored_posts)]  # Agregar índices a cada post
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "posts": indexed_posts})


@app.delete("/delete/")
def delete_post(dni: str, num_bandera: int, dificultad: int):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    # Verificar si la entrada existe antes de intentar eliminarla
    cursor.execute("SELECT COUNT(*) FROM posts WHERE DNI = ? AND NumBandera = ? AND Dificultad = ?", (dni, num_bandera, dificultad))
    count = cursor.fetchone()[0]
    
    if count == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    # Eliminar la entrada
    cursor.execute("DELETE FROM posts WHERE DNI = ? AND NumBandera = ? AND Dificultad = ?", (dni, num_bandera, dificultad))
    conn.commit()
    conn.close()
    return {"message": "Entrada eliminada correctamente"}


@app.delete("/delete_all")
def delete_all_posts():
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts")
    conn.commit()
    conn.close()
    return {"message": "Todas las entradas eliminadas correctamente"}
