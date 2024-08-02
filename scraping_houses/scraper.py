from typing import List, Literal, Tuple, Union

import httpx
from parsel import Selector

from scraping_houses.schemas import House






def _genetate_url_to_imovelweb(
        type_house: Literal['casas-padrao', 'casas-sobrado', 'casas-casa-de-condominio', 'casas-casa-de-vila', 'casas-quarto'] = 'casas-padrao', 
        operation_type: Literal['aluguel', 'venda'] = None,
        district: Literal['sao-paulo-sp'] = None,
        price: Tuple[int, int] = None,
        bedrooms: Union[int, Tuple[int, int]] = None,
    ) -> str:
    
    
    # https://www.imovelweb.com.br/casas-padrao-aluguel-sao-paulo-sp-2-quartos-500-1100-reales.html
    # https://www.imovelweb.com.br/casas-padrao-aluguel-sao-paulo-sp-mais-de-2-quartos-500-1100-reales.html
    
    flags = [type_house]
    if operation_type:
        flags.append(operation_type)
    if district:
        flags.append(district)
    if isinstance(bedrooms, int):
        if bedrooms == 0:
            raise ValueError('bedrooms must be greater than 0')
        flags.append(f'mais-de-{bedrooms}-quartos')
    elif isinstance(bedrooms, tuple):
        if bedrooms[1] <= bedrooms[0]:
            raise ValueError('bedrooms[1] must be greater than bedrooms[0]')
        if bedrooms[0] == 0:
            raise ValueError('bedrooms[0] must be greater than 0')
        flags.append(f'{bedrooms[0]}-{bedrooms[1]}-quartos')
    if price:
        if price[1] <= price[0]:
            raise ValueError('price[1] must be greater than price[0]')
        flags.append(f'{price[0]}-{price[1]}-reales')
    url = f'https://www.imovelweb.com.br{'-'.join(flags)}.html'
    
    return url
    
    
def locate_house(options: dict) -> House:
    
