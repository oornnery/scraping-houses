import re
from typing import Union, List, Generator

from playwright.sync_api import ElementHandle, Page, Browser
from playwright_stealth import stealth_sync

from scraping_houses.schemas import HouseVivaReal, ScrapingVivalrealConfig
from scraping_houses.settings import Settings




class ScrapingVivalreal:
    viewport_size = {'width': 1920, 'height': 1080}
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    
    def __init__(self, browser: Browser, url_config: ScrapingVivalrealConfig):
        self.browser = browser
        self.page = self.browser.new_page(
            viewport=self.viewport_size,
            user_agent=self.user_agent
        )
        stealth_sync(self.page)
        self.url_cfg = url_config
        self.last_page = 0
        self.extracted_properties = []

    @property
    def atual_page(self) -> int:
        try:
            return int(self.page.query_selector(
                'button.js-change-page[data-active]'
            ).get_attribute('data-page'))
        except Exception:
            return 0

    def contruct_url(self, new_page: bool = False) -> str:
        cfg = self.url_cfg
        url = cfg.base_url
        if cfg.house_type:
            url += f"/{cfg.house_type}"
        if cfg.state and cfg.house_type:
            url += f"/{cfg.state}"
        if cfg.country and cfg.state:
            url += f"/{cfg.country}"
        if cfg.region and cfg.country:
            url += f"/{cfg.region}"
        
        if new_page:
            cfg.page += 1
            url += f"?pagina={cfg.page}"
        flags = []
        if cfg.rooms:
            flags += f"quartos={cfg.rooms}"
        if cfg.min_price:
            flags += f"preco-desde={cfg.min_price}"
        if cfg.max_price:
            flags += f"preco-ate={cfg.max_price}"
            
        query_string = "&".join(flags)
        url += f"#{query_string}"
        return url

    def query_selector(
        self,
        element,
        selector,
        all: bool = False
    ) -> Union[ElementHandle, List[ElementHandle], None]:
        try:
            if all:
                return element.query_selector_all(selector)
            return element.query_selector(selector)
        except Exception:
            return None

    def get_attribute(
        self,
        element,
        attribute,
    ) -> Union[str, None]:
        try:
            if isinstance(element, list):
                return [
                    element.get_attribute(attribute) 
                        for element in element
                ]
            return element.get_attribute(attribute)
        except Exception:
            return None

    def query_selector_attr_parsing(
        self,
        element,
        selector: str,
        attribute: str,
    ) -> Union[str, list, None]:
        try:
            if isinstance(element, list):
                return [
                    self.parse_to_string(
                        element.get_attribute(attribute)
                    ) for element in self.query_selector(element, selector, all=True)
                ]
            return self.parse_to_string(
                self.query_selector(element, selector).get_attribute(attribute)
            )
        except Exception:
            return None

    def parse_to_string(self, text: str) -> str:
        try:
            text = str(text)
            text = text.replace('\n', ' ')
            text = re.sub(r'R\$\s*', '', text)
            text = re.sub(r'\xa0', '', text)
            text = text.strip()
            return text
        except Exception:
            return 'undefined'

    def query_selector_inner_text_parsing(
            self,
            element,
            selector: str,
            default: str = 'undefined',
            all: bool = False
        ) -> Union[str, list]:
        """Tenta obter o texto de um seletor, retornando um valor padrão se falhar."""
        try:
            if all:
                return [
                    self.parse_to_string(
                        element.inner_text()
                    ) for element in self.query_selector(element, selector, all=True)
                ]
            return self.parse_to_string(
                self.query_selector(element, selector).inner_text()
            )
        except Exception:
            return default

    def get_contact_info(self, page: Page) -> List[str]:
        try:
            page.wait_for_selector('.base-page__main-content__right .lead-message-form')
            form = page.query_selector('.base-page__main-content__right .lead-message-form')
            forms = form.query_selector_all('input')
            page.wait_for_timeout(500)
            forms[0].fill(self.url_cfg.contact_form.name)
            page.wait_for_timeout(500)
            forms[1].fill(self.url_cfg.contact_form.email)
            page.wait_for_timeout(500)
            forms[2].fill(self.url_cfg.contact_form.phone)
            page.wait_for_timeout(1000)
            page.click('.base-page__main-content__right .lead-message-form button')
            page.wait_for_timeout(500)
            page.wait_for_selector('.lead-modal__message', timeout=3000)
            modal = page.query_selector('.lead-modal__message')
            contacts = [
                el.get_attribute('href').replace('tel:', '').strip()
                for el in modal.query_selector_all('a')
            ]
            return contacts
        except Exception:
            return []
    
    def extract_property_info(self) -> Generator[HouseVivaReal, None, None]:
        self.page.wait_for_selector('div.results-list')
        elements = self.page.query_selector_all('article.property-card__container')
        for element in elements:
            url = self.url_cfg.base_url + self.query_selector_attr_parsing(
                element,
                'a.property-card__content-link',
                'href'
            )
            
            page = self.browser.new_page(
            viewport=self.viewport_size,
            user_agent=self.user_agent
        )
            page.goto(url)
            page.wait_for_timeout(1000)
            id_ = url.split('id')[1].replace('-', '').replace('/', '').strip()
            page.screenshot(path=f'logs/screenshots/{id_}.png')
            
            title = self.query_selector_inner_text_parsing(
                page, 
                'h1.description__title'
            )
            price = self.query_selector_inner_text_parsing(
                page,
                'p.price-info-value'
            )
            additional_price = self.query_selector_inner_text_parsing(
                page,
                'p.additional-price-info--value',
                all=True
            )
            address = self.query_selector_inner_text_parsing(
                page,
                'p.address-info-value'
            )
            properties = self.query_selector_inner_text_parsing(
                page,
                'p.amenities-item',
                all=True
            )
            house_type = self.query_selector_inner_text_parsing(
                page,
                '.price-value-wrapper p#business-type-info'
            )
            description = self.query_selector_inner_text_parsing(
                page,
                'div.desktop-only-container .description__content--text'
            )
            published_at = self.query_selector_inner_text_parsing(
                page,
                'div.desktop-only-container span.description__created-at'
            )
            
            contact = self.get_contact_info(page)

            images = [
                image.get_attribute('srcset') for image in 
                    page.query_selector_all('li.carousel-photos--item img')
            ]
            page.close()
            
            yield HouseVivaReal(
                title=title,
                house_type=house_type,
                price=price,
                additional_price=additional_price,
                address=address,
                properties=properties,
                description=description,
                published_at=published_at,
                contact=contact,
                url=url,
                images=images
            )

    def run(self):
        while True:
            if self.last_page > self.url_cfg.page:
                break
            if self.last_page >= 1:
                url = self.contruct_url(new_page=True)
            else:
                url = self.contruct_url()
            self.page.goto(url)
            for p in self.extract_property_info():
                
                self.extracted_properties.append(p)
                yield p
            self.last_page += 1

        return self.extracted_properties





