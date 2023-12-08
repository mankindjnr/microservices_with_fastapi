from pydantic import BaseModel

class OrderModel(BaseModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str

    class Config:
        orm_mode = True