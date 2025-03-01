import os
import hashlib
import logging
import pathlib
import json
import sqlite3
from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
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

@app.get("/")
def root():
    return {"message": "Hello, world!"}

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
@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}")
    hash_image = sha256_hash_step9(image) + ".jpg"
    category_id = get_category_id(category)
    logger.info(f"category id: {category_id}")

    # Using DataBase
    new_id = insert_item_to_db(name, category_id, hash_image)
    logger.info(f"inserted id: {new_id}")
    return {"message": f"item received: {name}"}

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
