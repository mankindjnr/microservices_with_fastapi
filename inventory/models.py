from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

class ProductResp(BaseModel):
    pk: str
    name: str
    price: float
    quantity: int

    class Config:
        orm_mode = True

class createProduct(BaseModel):
    name: str
    price: float
    quantity: int

    class Config:
        orm_mode = True