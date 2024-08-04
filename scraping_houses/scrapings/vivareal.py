import re
import time
from typing import Generator, List, Union

from playwright.sync_api import Browser, ElementHandle, Page
from playwright_stealth import stealth_sync
from sqlalchemy.orm import Session

from scraping_houses.database import engine
from scraping_houses.models import TableHouseVivaReal
from scraping_houses.schemas import HouseVivaReal, ScrapingVivalrealConfig
from scraping_houses.utils import cl, genetate_panel, logger
from scraping_houses.settings import Settings



class ScrapingVivalreal:
    viewport_size = {'width': 1920, 'height': 1080}
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\
        (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    settings = Settings()
    
    def __init__(self, browser: Browser, url_config: ScrapingVivalrealConfig):
        self.browser = browser
        self.page = self.new_page()
        stealth_sync(self.page)
        self.url_cfg = url_config
        self.last_page = 0
        self.extracted_properties = []

    @property
    def current_page(self) -> int:
        try:
            return int(self.page.query_selector(
                'button.js-change-page[data-active]'
            ).get_attribute('data-page'))
        except Exception:
            return 0

    def new_page(self) -> Page:
        return self.browser.new_page(
            viewport=self.viewport_size,
            user_agent=self.user_agent
        )

    @staticmethod
    def query_selector(
        element,
        selector,
        all: bool = False
    ) -> Union[ElementHandle, List[ElementHandle], None]:
        try:
            return element.query_selector_all(selector) if all\
                else element.query_selector(selector)
        except Exception:
            return None

    @staticmethod
    def parse_to_string(text: str) -> str:
        try:
            return re.sub(r'R\$\s*|\xa0|\n', '', str(text).strip())
        except Exception:
            return 'undefined'

    def screenshot(
            self,
            name: str = 'screenshot',
            error: bool = False,
            page: Page = None
        ) -> None:
        if not page:
            page = self.page
        if error:
            page.screenshot(path=f'{name}_error_{time.time()}.png', full_page=True)
        else:
            page.screenshot(path=f'{name}_{time.time()}.png', full_page=True)
        
    def extract_property_info(self) -> Generator[HouseVivaReal, None, None]:
        try: 
            self.page.wait_for_selector('div.results-list')
            elements = self.page.query_selector_all(
                'article.property-card__container'
            )
            for i, element in enumerate(elements):
                logger.info(f'[SCRAPING] => [ELEMENT] {i}')
                logger.info(f'[BROWSER] => [PAGE] {self.current_page}')
                url = self.url_cfg.base_url + self.query_selector(
                    element,
                    'a.property-card__content-link'
                ).get_attribute('href')
                yield self.extract_property_details(url)
        except Exception:
            self.screenshot(error=True)

    def extract_property_details(
            self,
            url: str
        ) -> Generator[HouseVivaReal, None, None]:
        page = self.new_page()
        page.goto(url)
        logger.info(f'[BROWSER] => [GOTO] {url}')
        with page.expect_navigation():
            id_ = re.sub(r'[^a-zA-Z0-9\s+]', '', url.split('id')[1])
            title = self.query_selector(page, 'h1.description__title')\
                .inner_text() or 'undefined'
            price = self.query_selector(
                page,
                'p.price-info-value'
            ).inner_text()
            additional_price = [
                element.inner_text() for element in self.query_selector(
                    page,
                    'p.additional-price-info--value',
                    all=True
                ) or []
            ]
            address = self.query_selector(page, 'p.address-info-value')\
                .inner_text()
            properties = [
                element.inner_text() for element in self.query_selector(
                    page,
                    'p.amenities-item',
                    all=True
                ) or []
            ]
            house_type = self.query_selector(
                page,
                '.price-value-wrapper p#business-type-info'
            ).inner_text()
            description = self.query_selector(
                page,
                'div.desktop-only-container .description__content--text'
            ).inner_text()
            published_at = self.query_selector(
                page,
                'div.desktop-only-container span.description__created-at'
            ).inner_text()

            # Contact form
            form = page.query_selector(
            '.base-page__main-content__right .lead-message-form'
            )
            forms = self.query_selector(form, 'input', all=True)
            if forms:
                forms[0].fill(self.url_cfg.contact_form.name)
                forms[1].fill(self.url_cfg.contact_form.email)
                forms[2].fill(self.url_cfg.contact_form.phone)
            page.screenshot(path=f'logs/screenshots/{id_}.png')
            logger.info(f'[BROWSER] => [SCREENSHOT] {id_}.png')
            
            contacts = []
            if form:
                page.click(
                    '.base-page__main-content__right .lead-message-form button'
                )
                modal = page.query_selector('.lead-modal__message')
                contacts = [
                    element.get_attribute('href').replace('tel:', '').strip()
                    for element in self.query_selector(modal, 'a', all=True)
                        or []
                ]
            images = [
                image.get_attribute('srcset') for image in
                    self.query_selector(
                        page,
                        'li.carousel-photos--item img',
                        all=True
                    ) or []
            ]
            page.close()
            return HouseVivaReal(
                title=title,
                house_type=house_type,
                price=price,
                additional_price=additional_price,
                address=address,
                properties=properties,
                description=description,
                published_at=published_at,
                contact=contacts,
                url=url,
                images=images
            )

    @staticmethod
    def add_house_to_db(house: HouseVivaReal):
        with Session(engine) as session:
            db_house = session.query(TableHouseVivaReal).filter_by(
                url=house.url
            ).first()
            if db_house:
                session.delete(db_house)
                logger.info(f'[DB] => [DELETE] {db_house}')
            db_house: TableHouseVivaReal = TableHouseVivaReal(
                url=house.url,
                title=house.title,
                price=house.price,
                additional_price=house.additional_price,
                address=house.address,
                properties=house.properties,
                house_type=house.house_type,
                images=house.images,
                description=house.description,
                published_at=house.published_at
            )
            session.add(db_house)
            session.commit()
            session.refresh(db_house)
            logger.info(f'[DB] => [ADD] {db_house}')

        return db_house

    def run(self):
        logger.info('Starting scraping (VivaReal)...')
        while True:
            start_time = time.time()
            if self.last_page > self.url_cfg.page:
                logger.info('End scraping (VivaReal)...')
                break
            if self.last_page >= 1:
                url = self.url_cfg.build_url(new_page=True)
            else:
                url = self.url_cfg.build_url()
            self.page.goto(url)
            with self.page.expect_navigation():
                logger.info(f'[BROWSER] => [GOTO] {url} - {self.last_page}')
                for p in self.extract_property_info():
                    self.extracted_properties.append(p)
                    cl.print(genetate_panel(p))
                    self.add_house_to_db(p)
                    # yield p
                self.last_page += 1
                end_time = time.time()
                logger.info(f'Elapsed time: {end_time - start_time} seconds')

        return self.extracted_properties
