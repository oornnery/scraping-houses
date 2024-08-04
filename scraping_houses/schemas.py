from enum import Enum
from typing import List

from pydantic import BaseModel, EmailStr


class ContactForm(BaseModel):
    name: str
    email: str
    phone: str


class EnumHouseType(Enum):
    SALE = 'venda'
    HENT = 'aluguel'
    LAUNCH = 'imoveis-lancamento'


class EnumState(Enum):
    SP = 'sp'


class EnumCountry(Enum):
    SAO_PAULO = 'sao-paulo'


class EnumRegion(Enum):
    SOUTH_ZONE = 'zona-sul'
    NORTH_ZONE = 'zona-norte'
    CENTER_ZONE = 'zona-central'
    WEST_ZONE = 'zona-oeste'
    EAST_ZONE = 'zona-leste'


# ordenar-por=preco-total:ASC
# ordenar-por=preco-total:DESC
# ordenar-por=preco:ASC
# ordenar-por=preco:DESC
class EnumOrderByPrice(Enum):
    PRICE_ASC = 'preco:ASC'
    PRICE_DESC = 'preco:DESC'
    TOTAL_PRICE_ASC = 'preco-total:ASC'
    TOTAL_PRICE_DESC = 'preco-total:DESC'


class PropertyType(Enum):
    HOUSE = 'casa_residencial'
    APARTMENT = 'apartamento_residencial'
    CONDOMINIUM = 'condominio_residencial'
    TOWNHOUSE = 'sobrado_residencial'
    FARM = 'granja_comercial'
    KITNET = 'kitnet_residencial'
    FLAT = 'flat_residencial'
    ROOF = 'cobertura_residencial'


class ScrapingVivalrealConfig(BaseModel):
    contact_form: ContactForm
    base_url: str = 'https://www.vivareal.com.br'
    house_type: EnumHouseType = EnumHouseType.HENT
    state: EnumState = EnumState.SP
    country: EnumCountry = EnumCountry.SAO_PAULO
    region: EnumRegion = EnumRegion.SOUTH_ZONE
    order_by_price: EnumOrderByPrice = EnumOrderByPrice.TOTAL_PRICE_ASC
    property_type: List[PropertyType] = [PropertyType.HOUSE]
    rooms: int = 0
    min_price: int = 0
    max_price: int = 0
    page: int = 1

    def build_url(self, new_page: bool = False) -> str:
        url = self.base_url
        if self.house_type:
            url += f"/{self.house_type.value}"
        if self.state and self.house_type:
            url += f"/{self.state.value}"
        if self.country and self.state:
            url += f"/{self.country.value}"
        if self.region and self.country:
            url += f"/{self.region.value}"
        if new_page:
            self.page += 1
            url += f"?pagina={self.page}"
        flags = []
        if self.rooms:
            flags.append(f"quartos={self.rooms}")
        if self.min_price:
            flags.append(f"preco-desde={self.min_price}")
        if self.max_price:
            flags.append(f"preco-ate={self.max_price}")
        if self.order_by_price:
            flags.append(f"ordenar-por={self.order_by_price.value}")
        if self.property_type:
            property_type = ','.join([p.value for p in self.property_type])
            flags.append(f'tipos={property_type}')
        query_string = "&".join(flags)
        return f"{url}#{query_string}"


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
