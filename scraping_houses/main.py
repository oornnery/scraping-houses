import sys
import os

# Adiciona o diretório pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Annotated
from playwright.sync_api import sync_playwright

from sqlalchemy.orm import Session

from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table

from scraping_houses.schemas import HouseVivaReal, ContactForm, ScrapingVivalrealConfig
from scraping_houses.scrapings.vivareal import ScrapingVivalreal
from scraping_houses.settings import Settings
from scraping_houses.models import TableHouseVivaReal
from scraping_houses.database import engine

    
cl = Console()


def add_house_to_db(house: HouseVivaReal):
    print(house)
    with Session(engine) as session:
        db_house = session.query(TableHouseVivaReal).filter_by(
            url=house.url
        ).first()
        if db_house:
            session.delete(db_house)
            
        db_house: TableHouseVivaReal = TableHouseVivaReal(**house.__dict__)
        session.add(db_house)
        session.commit()
        session.refresh(db_house)
    
    return db_house

def genetate_panel(property_info: HouseVivaReal) -> Panel:
    grid = Table.grid(expand=True)
    grid.add_column(style='cyan')
    grid.add_column()
    items = property_info.__dict__.items()
    for item in items:
        grid.add_row(
            f'[{item[0].upper()}] ::',
            f'{item[1]}'
        )
    return Panel(
        grid,
        title=property_info.title
    )


def main(url_config: ScrapingVivalrealConfig):
    extracted_properties = []
    http_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    viewport_size = {'width': 1920, 'height': 1080}
    with sync_playwright() as p:
        # Inicie o navegador
        browser = p.chromium.launch(headless=True)
        # context = browser.new_context(
        #     extra_http_headers=http_headers,
        #     viewport=viewport_size,
        # )
        
        viewport_size = {'width': 1920, 'height': 1080}
        c_vivareal = ScrapingVivalreal(browser, url_config)
        columns = []
        for p in c_vivareal.run():
            cl.clear()
            extracted_properties.append(p)
            columns.append(genetate_panel(p))
            yield p
            cl.print(Columns(columns))
            
            
        # Feche o navegador
        browser.close()
    cl.clear()
    cl.print(Panel('FIM', expand=True, style='bold red'))
    cl.print(Columns(
        genetate_panel(p) for p in extracted_properties
    ))



if __name__ == "__main__":
    contact_form = ContactForm(
        name='Jose Felipe Santos',
        email='jose.felipe@outlook.com.br',
        phone='11999999999'
    )
    url_cfg = ScrapingVivalrealConfig(
        contact_form=contact_form
    )
    for p in main(url_config=url_cfg):
        add_house_to_db(p)
