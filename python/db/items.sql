-- For STEP 5-1
-- CREATE TABLE IF NOT EXISTS items (
--     id INTEGER PRIMARY KEY AUTOINCREMENT, 
--     name TEXT NOT NULL, 
--     category TEXT, 
--     image_name TEXT 
-- );

-- For STEP 5-3
CREATE TABLE IF NOT EXISTS categories(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    name TEXT NOT NULL, 
    category_id INTEGER, 
    image_name TEXT,
    FOREIGN KEY (category_id) REFERENCES categories (category_id)
    );