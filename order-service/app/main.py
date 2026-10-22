from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time
import httpx

app = FastAPI(title="Order Service")

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")

def get_db_connection():
    max_retries = 5
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "order-db"),
                database=os.getenv("DB_NAME", "orderdb"),
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

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class Order(BaseModel):
    user_id: int
    items: List[OrderItem]

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str

@app.on_event("startup")
def startup():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price DECIMAL(10, 2) NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.get("/")
def read_root():
    return {"service": "Order Service", "status": "running"}

@app.post("/orders", response_model=OrderResponse)
async def create_order(order: Order):
    # Verify user exists
    async with httpx.AsyncClient() as client:
        try:
            user_response = await client.get(f"{USER_SERVICE_URL}/users/{order.user_id}")
            if user_response.status_code != 200:
                raise HTTPException(status_code=404, detail="User not found")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="User service unavailable")
   
    # Calculate total and verify products
    total_amount = 0
    order_items_data = []
   
    async with httpx.AsyncClient() as client:
        for item in order.items:
            try:
                product_response = await client.get(
                    f"{PRODUCT_SERVICE_URL}/products/{item.product_id}"
                )
                if product_response.status_code != 200:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Product {item.product_id} not found"
                    )
               
                product = product_response.json()
               
                if product['stock'] < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for product {item.product_id}"
                    )
               
                item_total = float(product['price']) * item.quantity
                total_amount += item_total
                order_items_data.append({
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'price': product['price']
                })
               
                # Update stock
                await client.put(
                    f"{PRODUCT_SERVICE_URL}/products/{item.product_id}/stock",
                    params={"quantity": -item.quantity}
                )
               
            except httpx.RequestError:
                raise HTTPException(status_code=503, detail="Product service unavailable")
   
    # Create order in database
    conn = get_db_connection()
    cur = conn.cursor()
   
    try:
        cur.execute(
            "INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, %s) RETURNING *",
            (order.user_id, total_amount, 'confirmed')
        )
        new_order = cur.fetchone()
       
        for item_data in order_items_data:
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (new_order['id'], item_data['product_id'], item_data['quantity'], item_data['price'])
            )
       
        conn.commit()
        return new_order
    finally:
        cur.close()
        conn.close()

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
   
    cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()
   
    if not order:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")
   
    cur.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
    items = cur.fetchall()
   
    cur.close()
    conn.close()
   
    return {
        "order": order,
        "items": items
    }

@app.get("/orders")
def get_all_orders():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cur.fetchall()
    cur.close()
    conn.close()
    return orders
