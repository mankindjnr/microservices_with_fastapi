from fastapi import FastAPI, status, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis_om import get_redis_connection, HashModel
from fastapi.middleware.cors import CORSMiddleware

from models import ProductResp, createProduct


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "https://sj76vr3h-8000.euw.devtunnels.ms", "https://sj76vr3h-9400.euw.devtunnels.ms"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis = get_redis_connection(
    host="redis-12603.c326.us-east-1-3.ec2.cloud.redislabs.com",
    port=12603,
    password="prnrNkgQiIEFP5a0mBV63luOw6CRvyfB",
    decode_responses=True
)

class ProductRedis(HashModel):
    name: str
    price: float
    quantity: int

    class Meta:
        database = redis

@app.get("/products")
def all():
    return [format(pk) for pk in ProductRedis.all_pks()]


def format(pk: str):
    product = ProductRedis.get(pk)
    return {
        'id': product.pk,
        'name': product.name,
        'price': product.price,
        'quantity': product.quantity
    }


@app.post("/products", response_model=createProduct)
def create(product: createProduct):
    redis_model = ProductRedis(**product.dict())
    redis_model.save()

    return product

@app.get("/products/{pk}", response_model=ProductResp)
def get(pk: str):
    product = ProductRedis.get(pk)
    return product

@app.delete("/products/{pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete(pk: str):
    ProductRedis.delete(pk)
    return Response(status_code=status.HTTP_204_NO_CONTENT)