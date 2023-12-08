from fastapi import FastAPI, status, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis_om import get_redis_connection, HashModel
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import requests, json, time, asyncio
from fastapi.background import BackgroundTasks

from models import OrderModel


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "https://sj76vr3h-9400.euw.devtunnels.ms", ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This should be a different database than the one used by the inventory service
redis = get_redis_connection(
    host="redis-12603.c326.us-east-1-3.ec2.cloud.redislabs.com",
    port=12603,
    password="prnrNkgQiIEFP5a0mBV63luOw6CRvyfB",
    decode_responses=True
)

class OrderRedis(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str # pending, paid, cancelled, refunded

    class Meta:
        database = redis


@app.get("/orders/{pk}")
def get(pk: str):
    return OrderRedis.get(pk)

@app.post("/orders")
async def create(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    req = requests.get(f"http://127.0.0.1:8000/products/{body['product_id']}") #we are getting a response from the other microservice
    product = req.json()

    # creating the order
    order = OrderRedis(
        product_id=product['pk'],
        price=product['price'],
        fee = 0.2 * product['price'],
        total = 1.2 * product['price'],
        quantity=body['quantity'],
        status='pending' # we are waiting for the payment processor to complete the payment
    )

    order.save()

    background_tasks.add_task(order_completed, order)

    return order

async def order_completed(order: OrderRedis):
    await asyncio.sleep(40)
    order.status = 'paid'
    order.save()

    redis.xadd('order_completed', order.dict(), '*')