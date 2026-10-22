from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time

app = FastAPI(title="Product Service")

def get_db_connection():
    max_retries = 5
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "product-db"),
                database=os.getenv("DB_NAME", "productdb"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
                cursor_factory=RealDictCursor
            )
            return conn
        except psycopg2.OperationalError:
            if i < max_retries - 1:
                time.sleep(2)
            else:
                raise

class Product(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    stock: int

@app.on_event("startup")
def startup():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.get("/")
def read_root():
    return {"service": "Product Service", "status": "running"}

@app.post("/products", response_model=ProductResponse)
def create_product(product: Product):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s) RETURNING *",
        (product.name, product.description, product.price, product.stock)
    )
    new_product = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_product

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()
   
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/products")
def get_all_products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    conn.close()
    return products

@app.put("/products/{product_id}/stock")
def update_stock(product_id: int, quantity: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE products SET stock = stock + %s WHERE id = %s RETURNING *",
        (quantity, product_id)
    )
    product = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
   
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
