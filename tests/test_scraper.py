import pytest

from scraping_houses.scraper import _genetate_url_to_imovelweb


def test_genetate_url_to_imovelweb_no_flags():
    url = _genetate_url_to_imovelweb()
    assert url == 'https://www.imovelweb.com.br/casas-padrao-aluguel.html'

def test_genetate_url_to_imovelweb_all_flags():
    url = _genetate_url_to_imovelweb(
        type_house='casas-padrao',
        operation_type='alugel',
        district='sao-paulo-sp',
        bedrooms=(2, 2),
        price=(500, 1100),
    )
    assert url == 'https://www.imovelweb.com.br/casas-padrao-aluguel-sao-paulo-sp-2-quartos-500-1100-reales.html'

def test_genetate_url_to_imovelweb_bedrooms_int():
    url = _genetate_url_to_imovelweb(
        bedrooms=2,
    )
    assert url == 'https://www.imovelweb.com.br/casas-padrao-aluguel-mais-de-2-quartos.html'

def test_genetate_url_to_imovelweb_value_error_bedrooms_tuple():
    url = _genetate_url_to_imovelweb(
        bedrooms=(1, 2),
    )
    assert url == ValueError

def test_genetate_url_to_imovelweb_value_error_0_bedrooms_tuple():
    url = _genetate_url_to_imovelweb(
        bedrooms=(0, 2),
    )
    assert url == ValueError

def test_genetate_url_to_imovelweb_value_error_0_bedrooms_int():
    url = _genetate_url_to_imovelweb(
        bedrooms=(0, 2),
    )
    assert url == ValueError

def test_genetate_url_to_imovelweb_value_error_price():
    url = _genetate_url_to_imovelweb(
        price=(1100, 500),
    )
    assert url == ValueError