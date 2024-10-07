from pydantic import BaseModel, validator
from typing import List

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: List[int]  # [red, green, blue, dark]
    price: int
    quantity: int  # Quantity available for sale in catalog

class BarrelPurchase(BaseModel):
    sku: str
    quantity: int

class BarrelDelivery(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: List[int]  # [red, green, blue, dark]
    price: int
    quantity: int