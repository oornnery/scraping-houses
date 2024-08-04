import os
import sys

# Adiciona o diretório pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from playwright.sync_api import sync_playwright

from scraping_houses.schemas import (
    ContactForm,
    ScrapingVivalrealConfig,
)
from scraping_houses.scrapings.vivareal import ScrapingVivalreal

# from scraping_houses.utils import logger, cl


def main(url_config: ScrapingVivalrealConfig):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        c_vivareal = ScrapingVivalreal(browser, url_config)
        c_vivareal.run()


if __name__ == "__main__":
    contact_form = ContactForm(
        name='Jose Felipe Santos',
        email='jose.felipe@outlook.com.br',
        phone='11999999999'
    )
    url_cfg = ScrapingVivalrealConfig(
        contact_form=contact_form,
        # region='zona-sul',
        country='sao-paulo',
    )
    main(url_config=url_cfg)
