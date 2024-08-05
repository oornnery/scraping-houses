import re
from enum import Enum
from typing import List, Union
from typing_extensions import Unpack

from pydantic import BaseModel, ConfigDict

from scraping_houses.settings import Settings

settings = Settings()

class FlagHouseType(Enum):
    SALE = 'venda'
    HENT = 'aluguel'
    LAUNCH = 'imoveis-lancamento'

    def __str__(self) -> str:
        return self.value


class FlagState(Enum):
    SP = 'sp'

    def __str__(self) -> str:
        return self.value


class FlagCountry(Enum):
    SAO_PAULO = 'sao-paulo'

    def __str__(self) -> str:
        return self.value


class FlagRegion(Enum):
    SOUTH_ZONE = 'zona-sul'
    NORTH_ZONE = 'zona-norte'
    CENTER_ZONE = 'zona-central'
    WEST_ZONE = 'zona-oeste'
    EAST_ZONE = 'zona-leste'
    
    def __str__(self) -> str:
        return self.value


class FlagOrderByPrice(Enum):
    TOTAL_PRICE_ASC = 'preco-total:ASC'
    TOTAL_PRICE_DESC = 'preco-total:DESC'
    PRICE_ASC = 'preco:ASC'
    PRICE_DESC = 'preco:DESC'
    
    def __str__(self) -> str:
        return self.value


class FlagPropertyType(Enum):
    HOUSE = 'casa_residencial'
    APARTMENT = 'apartamento_residencial'
    CONDOMINIUM = 'condominio_residencial'
    TOWNHOUSE = 'sobrado_residencial'
    FARM = 'granja_comercial'
    KITNET = 'kitnet_residencial'
    FLAT = 'flat_residencial'
    ROOF = 'cobertura_residencial'
    
    def __str__(self) -> str:
        return self.value


class UrlConfig(BaseModel):
    url_base: str = settings.URL_VIVAREAL
    house_type: FlagHouseType = FlagHouseType.HENT
    state: Union[FlagState, None] = FlagState.SP
    country: Union[FlagCountry, None] = FlagCountry.SAO_PAULO
    property_type: Union[List[FlagPropertyType], None] = None
    region: Union[FlagRegion, None] = None
    order_by_price: Union[FlagOrderByPrice, None] = None
    rooms: int = 0
    min_price: int = 0
    max_price: int = 0


class Property(BaseModel):
    url: str
    url_req: str = ''
    status_code: int = 0
    reason: str = ''
    local_ip: str = ''
    primary_ip: str = ''
    title: str = ''
    property_type: str = ''
    price: str = ''
    additional_price: List[str] = []
    address: str = ''
    properties: List[str] = []
    description: List[str] = []
    images: List[str] = []
    published_at: str = ''
    
    @property
    def property_id(self) -> str:
        return re.findall(r'id-(\d+)', self.url)[0]
    
    def __str__(self) -> str:
        return f'<Property {self.property_id}>'


class Page(BaseModel):
    url: str
    status_code: int
    reason: str
    primary_ip: str
    local_ip: str
    html: str
    properties: List[Property]
    page: int

    def __str__(self) -> str:
        return f'<Page {self.page} ({self.url}) Property {len(self.properties)}>'
