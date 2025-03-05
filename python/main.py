import os
import hashlib
import logging
import pathlib
import json
import sqlite3
from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from contextlib import asynccontextmanager


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


# STEP 5-1: set up the database connection
def setup_database():
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

JSON_FILE = 'items.json'
DB_NAME = '../db/mercari.sqlite3'

# Function to read the JSON file
def read_json_file():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w') as f:
            json.dump({"items": []}, f)  # Initialize with an empty list
    with open(JSON_FILE, 'r') as f:
        return json.load(f)

# Function to write data to the JSON file
def write_json_file(data):
    with open(JSON_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def sha256_hash(image_name):
    # Create image path
    image = images / image_name
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(image, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except FileNotFoundError:
        return "File not found"
    
def sha256_hash_step9(file_contents) -> str:
    sha256 = hashlib.sha256()
    sha256.update(file_contents)
    return sha256.hexdigest()

def insert_item_to_db(name, category_id, image_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?);
        """
    cursor.execute(query, (name, category_id, image_name))

    conn.commit()

    cursor.close()
    conn.close()
    return cursor.lastrowid

def get_item_by_id_from_database(item_id):
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Query the Items table
    query = f"""
    SELECT items.name, categories.name AS category, image_name 
    FROM items 
    JOIN categories
    ON category_id = categories.id
    WHERE items.id={item_id}
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    items_list = [{"name": name, "category": category, "image_name": image_name} for name, category, image_name in rows]
    result = {"items": items_list}


    # Clean up
    cursor.close()
    conn.close()
    
    return result

def get_items_from_database():
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Query the Items table
    query = """
    SELECT items.name, categories.name AS category, image_name 
    FROM items 
    JOIN categories
    ON category_id = categories.id
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    items_list = [{"name": name, "category": category, "image_name": image_name} for name, category, image_name in rows]
    result = {"items": items_list}

    # Clean up
    cursor.close()
    conn.close()
    
    return result

def search_items(keyword):
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Query the Items table
    query = f"""
    SELECT items.name AS name, categories.name AS category, image_name 
    FROM items 
    JOIN categories
    ON category_id = categories.id 
    WHERE items.name LIKE '*{keyword}*'"
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    items_list = [{"name": name, "category": category, "image_name": image_name} for name, category, image_name in rows]
    result = {"items": items_list}

    # Clean up
    cursor.close()
    conn.close()
    
    return result

def get_category_id(category: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Query the Items table
    query = f"SELECT id FROM categories WHERE name = '{category}'"
    cursor.execute(query)
    rows = cursor.fetchone()
    id = rows[0]
    # Clean up
    cursor.close()
    conn.close()
    
    return id

class HelloResponse(BaseModel):
    message: str

# For STEP 4
# @app.post("/items")
# def add_item(name: str = Form(...), category: str = Form(...), image: str = Form(...)):
#     logger.info(f"Receive item: {name}")
#     hash_image = sha256_hash(image) + ".jpg"
#     category_id = get_category_id(category)
#     logger.info(f"category id: {category_id}")
#     # Using JSON file
#     # current_data = read_json_file()
#     # current_data["items"].append({"name": name, "category": category, "image_name": hash_image})
#     # write_json_file(current_data)

#     # Using DataBase
#     new_id = insert_item_to_db(name, category_id, hash_image)
#     logger.info(f"inserted id: {new_id}")
#     return {"message": f"item received: {name}"}

# For STEP 9
# @app.post("/items")
# async def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
#     logger.info(f"Receive item: {name}")

@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})


    try:
        # Read file contents as bytes
        file_contents = await image.read()

        if not isinstance(file_contents, bytes):
            raise TypeError("File contents must be in bytes format")

        # Compute hash of the image's content
        hash_image = sha256_hash_step9(file_contents) + ".jpg"
        logger.info(f"Image hash: {hash_image}")

        file_path = images/ hash_image

        # Save the file to the local system
        with open(file_path, "wb") as file:
            file.write(file_contents)

        # Resolve category ID
        category_id = get_category_id(category)
        logger.info(f"Category ID: {category_id}")

        # Insert into database
        new_id = insert_item_to_db(name, category_id, hash_image)
        logger.info(f"Inserted ID: {new_id}")

        return {"message": f"Item received: {name}"}
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/items")
def get_items():
    #current_data = read_json_file()
    current_data = get_items_from_database()
    return current_data

@app.get("/items/{item_id}")
def get_item_by_id(item_id):
    item_id_int = int(item_id)
    # all_data = read_json_file()
    # item = all_data["items"][item_id_int - 1]
    item = get_item_by_id_from_database(item_id_int)
    return item

class AddItemResponse(BaseModel):
    message: str


# add_item is a handler to add a new item for POST /items .
@app.post("/items", response_model=AddItemResponse)
def add_item(
    name: str = Form(...),
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    insert_item(Item(name=name))
    return AddItemResponse(**{"message": f"item received: {name}"})


# get_image is a handler to return an image for GET /images/{filename} .
@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.info(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)

@app.get("/search")
def search_keyword(keyword: str = Form(...)):
    search_result = search_items(keyword)
    return search_result

class Item(BaseModel):
    name: str


def insert_item(item: Item):
    # STEP 4-2: add an implementation to store an item
    pass
