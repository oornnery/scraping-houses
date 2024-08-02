from typing import Union, List
from pydantic import BaseModel, EmailStr

class House(BaseModel):
    url: str
    description: str
    address: str
    price: str
    total_area: str
    rooms: str
    bedrooms: str
    photos: List[str]
    name: str
    email: EmailStr
    contacts: str
