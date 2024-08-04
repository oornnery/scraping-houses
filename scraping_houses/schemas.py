from typing import List, Literal

from pydantic import BaseModel, EmailStr

class ContactForm(BaseModel):
    name: str
    email: str
    phone: str

class ScrapingVivalrealConfig(BaseModel):
    contact_form: ContactForm
    base_url: str = f'https://www.vivareal.com.br'
    house_type: Literal['venda', 'aluguel', 'imoveis-lancamento'] = 'aluguel'
    state: Literal['sp'] = 'sp'
    country: Literal['sao-paulo'] = 'sao-paulo'
    region: Literal['zona-sul'] = None
    rooms: int = 0
    min_price: int = 0
    max_price: int = 0
    page: int = 1

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

class HouseVivaReal(BaseModel):
    url: str
    title: str
    price: str
    additional_price: List[str]
    address: str
    properties: List[str]
    house_type: str
    images: List[str]
    description: str
    published_at: str