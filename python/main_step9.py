import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Dict, List
from PIL import Image, UnidentifiedImageError



# Define the path to the images & sqlite3 database
images = pathlib.Path(__file__).parent.resolve() / "images"
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"


def get_db():
    if not db.exists():
        yield

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()


################## for STEP 4-1: ####################
# import json
# JSON_FILE = 'items.json'
# # Function to read the JSON file
# def read_json_file() -> Dict[str, List[Dict[str,str]]]:
#     if not os.path.exists(JSON_FILE):
#         with open(JSON_FILE, 'w') as f:
#             json.dump({"items": []}, f)  # Initialize with an empty list
#     with open(JSON_FILE, 'r') as f:
#         return json.load(f)

# # Function to write data to the JSON file
# def write_json_file(data):
#     with open(JSON_FILE, 'w') as f:
#         json.dump(data, f, indent=4)

######################################################

################## for STEP 4-4: #####################
import hashlib
def hash_image(image_file: UploadFile) -> str:
    try:
        # Validate image type
        try:
            with Image.open(image_file.file) as img:
                if img.format != 'JPEG':  # Check if the image format is JPEG
                    raise ValueError("Uploaded file is not a JPEG image.")
        except UnidentifiedImageError:
            raise ValueError("The file doesn't appear to be an image.")

        # Read image
        image = image_file.file.read()
        hash_value = hashlib.sha256(image).hexdigest()
        hashed_image_name = f"{hash_value}.jpg"
        hashed_image_path = images / hashed_image_name
        # Save image with hashed value as image name
        with open(hashed_image_path, 'wb') as f:
            f.write(image)
        return hashed_image_name
    
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")

######################################################

# STEP 5-1: set up the database connection
def setup_database():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    sql_file = pathlib.Path(__file__).parent.resolve() / "db" / "items.sql"
    with open(sql_file, "r") as f:
        cursor.executescript(f.read())
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("uvicorn")
# For STEP 4-6
logger.level = logging.DEBUG
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class HelloResponse(BaseModel):
    message: str


@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})


class AddItemResponse(BaseModel):
    message: str


# add_item is a handler to add a new item for POST /items .
@app.post("/items", response_model=AddItemResponse)
def add_item(
    name: str = Form(...),
    category: str = Form(...), # For STEP 4-2
    image: UploadFile = File(...), # For STEP 4-4
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    # for STEP 4-2
    if not category:
        raise HTTPException(status_code=400, detail="category is required")
    # for STEP 4-4
    if not image:
        raise HTTPException(status_code=400, detail="image is required")

    hashed_image = hash_image(image)
    # For STEP 4
    # insert_item(Item(name=name, category=category, image=hashed_image))
    insert_item_db(Item(name=name, category=category, image=hashed_image), db)
    return AddItemResponse(**{"message": f"item received: {name}"})

@app.get("/items")
def get_items(db: sqlite3.Connection = Depends(get_db)):
    # For STEP 4-3
    # all_data = read_json_file()
    # For STEP 5-1
    all_data = get_items_from_database(db)
    return all_data

@app.get("/items/{item_id}")
def get_item_by_id(item_id: str, db: sqlite3.Connection = Depends(get_db)):
    item_id_int = int(item_id)
    # For STEP 4-5
    # all_data = read_json_file()
    # item = all_data["items"][item_id_int - 1]
    # For STEP 5
    item = get_items_from_database_by_id(item_id_int, db)
    return item

# get_image is a handler to return an image for GET /images/{filename} .
@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)

@app.get("/search")
def search_keyword(keyword: str = Query(...), db: sqlite3.Connection = Depends(get_db)):
    search_result = search_items(keyword, db)
    return search_result


class Item(BaseModel):
    name: str
    category: str
    image: str


# For STEP 4
# def insert_item(item: Item): 
#     current_data = read_json_file()

#     ################################ for STEP 4-2 ################################
#     # current_data["items"].append({"name": item.name, "category": item.category})
#     #############################################################################

#     ################################ for STEP 4-4 ################################
#     current_data["items"].append({"name": item.name, "category": item.category, "image_name": item.image})
#     #############################################################################
    
#     write_json_file(current_data)

def get_items_from_database(db: sqlite3.Connection):
    cursor = db.cursor()
    # Query the Items table
    query = """
    SELECT items.id, items.name, categories.name AS category, image_name 
    FROM items 
    JOIN categories
    ON category_id = categories.id
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    items_list = [{"id": id, "name": name, "category": category, "image_name": image_name} for id, name, category, image_name in rows]
    result = {"items": items_list}
    cursor.close()
    
    return result

def get_items_from_database_by_id(id: int, db: sqlite3.Connection) -> Dict[str, List[Dict[str,str]]]:
    cursor = db.cursor()
    # Query the Items table
    query = """
    SELECT items.name, categories.name AS category, image_name 
    FROM items
    JOIN categories
    ON category_id = categories.id
    WHERE items.id = ?
    """
    cursor.execute(query, (id,))
    rows = cursor.fetchall()
    items_list = [{"name": name, "category": category, "image_name": image_name} for name, category, image_name in rows]
    result = {"items": items_list}
    cursor.close()
    
    return result

def search_items(keyword: str, db: sqlite3.Connection) -> Dict[str, List[Dict[str,str]]]:
    cursor = db.cursor()
    query = """
    SELECT items.name AS name, categories.name AS category, image_name 
    FROM items 
    JOIN categories
    ON category_id = categories.id 
    WHERE items.name LIKE ?
    """
    pattern = f"%{keyword}%"
    cursor.execute(query, (pattern,))
    rows = cursor.fetchall()
    items_list = [{"name": name, "category": category, "image_name": image_name} for name, category, image_name in rows]
    result = {"items": items_list}
    cursor.close()

    return result

# For STEP 5
def insert_item_db(item: Item, db: sqlite3.Connection) -> int:
    cursor = db.cursor()
    # Query the category table
    query_category = "SELECT id FROM categories WHERE name = ?"
    cursor.execute(query_category, (item.category,))
    rows = cursor.fetchone()
    if rows is None:
        insert_query_category = "INSERT INTO categories (name) VALUES (?)"
        cursor.execute(insert_query_category, (item.category,))
        category_id = cursor.lastrowid
    else:
        category_id = rows[0]
    
    query = """
        INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?);
        """
    cursor.execute(query, (item.name, category_id, item.image))

    db.commit()

    cursor.close()
    return cursor.lastrowid