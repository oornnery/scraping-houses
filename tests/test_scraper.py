from scraping_houses.schemas import House
from scraping_houses.scraper import (
    genetate_url_to_imovelweb,
    get_houses_from_imovelweb,
)


def test_genetate_url_to_imovelweb_no_flags():
    url = genetate_url_to_imovelweb()
    assert url == 'https://www.imovelweb.com.br/casas-padrao.html'


def test_genetate_url_to_imovelweb_all_flags():
    url = genetate_url_to_imovelweb(
        type_house='casas-padrao',
        operation_type='aluguel',
        district='sao-paulo-sp',
        bedrooms=(2, 2),
        price=(500, 1100),
    )
    assert (
        url
        == 'https://www.imovelweb.com.br/casas-padrao-aluguel-sao-paulo-sp-2-quartos-500-1100-reales.html'
    )


def test_genetate_url_to_imovelweb_bedrooms_int():
    url = genetate_url_to_imovelweb(
        bedrooms=2,
    )
    assert (
        url
        == 'https://www.imovelweb.com.br/casas-padrao-mais-de-2-quartos.html'
    )


# TODO: testar os erros

# def test_genetate_url_to_imovelweb_value_error_bedrooms_tuple():
#     url = genetate_url_to_imovelweb(
#         bedrooms=(2, 1),
#     )

#     assert url == isinstance(url, ValueError)


# def test_genetate_url_to_imovelweb_value_error_0_bedrooms_tuple():
#     url = genetate_url_to_imovelweb(
#         bedrooms=(0, 2),
#     )
#     assert url == isinstance(url, ValueError)


# def test_genetate_url_to_imovelweb_value_error_0_bedrooms_int():
#     url = genetate_url_to_imovelweb(
#         bedrooms=(0, 2),
#     )
#     assert url == isinstance(url, ValueError)


# def test_genetate_url_to_imovelweb_value_error_price():
#     url = genetate_url_to_imovelweb(
#         price=(1100, 500),
#     )
#     assert url == isinstance(url, ValueError)


def test_get_houses_from_imovelweb_no_houses(client):
    url = genetate_url_to_imovelweb()
    houses = get_houses_from_imovelweb(client, url)

    assert len(houses) > 0


def test_get_houses_from_imovelweb_house_type(client):
    url = genetate_url_to_imovelweb()
    houses = get_houses_from_imovelweb(client, url)

    assert isinstance(houses[0], House)
