import re, sys, os
import asyncio
from typing import AsyncGenerator, List, Union

from playwright.async_api import Browser, ElementHandle, Page
from playwright_stealth import stealth_async
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraping_houses.database import engine
from scraping_houses.models import TableHouseVivaReal
from scraping_houses.schemas import HouseVivaReal, ScrapingVivalrealConfig
from scraping_houses.utils import cl, genetate_panel, logger

class ScrapingVivalreal:
    viewport_size = {'width': 1920, 'height': 1080}
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\
        (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'

    def __init__(self, browser: Browser, url_config: ScrapingVivalrealConfig):
        self.browser = browser
        self.page = None
        self.url_cfg = url_config
        self.last_page = 0
        self.extracted_properties = []

    async def new_page(self) -> Page:
        page = await self.browser.new_page(
            viewport=self.viewport_size,
            user_agent=self.user_agent
        )
        await stealth_async(page)
        return page

    async def current_page(self):
        try:
            return int(await self.page.query_selector(
                'button.js-change-page[data-active]'
            ).get_attribute('data-page'))
        except Exception:
            return 0

    @staticmethod
    async def query_selector(
        element,
        selector,
        all: bool = False
    ) -> Union[ElementHandle, List[ElementHandle], None]:
        try:
            return await element.query_selector_all(selector) if all\
                else await element.query_selector(selector)
        except Exception:
            return None

    @staticmethod
    def parse_to_string(text: str) -> str:
        try:
            return re.sub(r'R\$\s*|\xa0|\n', '', str(text).strip())
        except Exception:
            return 'undefined'

    async def extract_property_info(self) -> AsyncGenerator[HouseVivaReal, None]:
        await self.page.wait_for_selector('div.results-list')
        elements = await self.page.query_selector_all(
            'article.property-card__container'
        )
        for i, element in enumerate(elements):
            logger.info(f'[SCRAPING] => [ELEMENT] {i}')
            logger.info(f'[BROWSER] => [PAGE] {self.current_page}')
            url = self.url_cfg.base_url + await(await self.query_selector(
                element,
                'a.property-card__content-link'
            )).get_attribute('href')
            yield await self.extract_property_details(url)

    async def extract_property_details(
            self,
            url: str
        ) -> HouseVivaReal:
        page = await self.new_page()
        await page.goto(url)
        logger.info(f'[BROWSER] => [GOTO] {url}')
        async with page.expect_navigation():
            id_ = re.sub(r'[^a-zA-Z0-9\s+]', '', url.split('id')[1])
            title = (await self.query_selector(page, 'h1.description__title'))\
                .inner_text() or 'undefined'
            price = (await self.query_selector(
                page,
                'p.price-info-value'
            )).inner_text()
            additional_price = [
                element.inner_text() for element in await self.query_selector(
                    page,
                    'p.additional-price-info--value',
                    all=True
                ) or []
            ]
            address = (await self.query_selector(page, 'p.address-info-value'))\
                .inner_text()
            properties = [
                element.inner_text() for element in await self.query_selector(
                    page,
                    'p.amenities-item',
                    all=True
                ) or []
            ]
            house_type = (await self.query_selector(
                page,
                '.price-value-wrapper p#business-type-info'
            )).inner_text()
            description = (await self.query_selector(
                page,
                'div.desktop-only-container .description__content--text'
            )).inner_text()
            published_at = (await self.query_selector(
                page,
                'div.desktop-only-container span.description__created-at'
            )).inner_text()

            # Contact form
            form = await page.query_selector(
            '.base-page__main-content__right .lead-message-form'
            )
            forms = await self.query_selector(form, 'input', all=True)
            if forms:
                await forms[0].fill(self.url_cfg.contact_form.name)
                await forms[1].fill(self.url_cfg.contact_form.email)
                await forms[2].fill(self.url_cfg.contact_form.phone)
            await page.screenshot(path=f'logs/screenshots/{id_}.png')
            logger.info(f'[BROWSER] => [SCREENSHOT] {id_}.png')
            if form:
                await page.click(
                    '.base-page__main-content__right .lead-message-form button'
                )
            modal = await page.query_selector('.lead-modal__message')
            # modal.wait_for_element_state('visible')
            contacts = [
                element.get_attribute('href').replace('tel:', '').strip()
                for element in await self.query_selector(modal, 'a', all=True)
                    or []
            ]
            images = [
                image.get_attribute('srcset') for image in
                    await self.query_selector(
                        page,
                        'li.carousel-photos--item img',
                        all=True
                    ) or []
            ]
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
        await page.close()

    @staticmethod
    async def add_house_to_db(house: HouseVivaReal):
        async with Session(engine) as session:
            db_house = await session.query(TableHouseVivaReal).filter_by(
                url=house.url
            ).first()
            if db_house:
                await session.delete(db_house)
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
            await session.commit()
            await session.refresh(db_house)
            logger.info(f'[DB] => [ADD] {db_house}')

        return db_house

    async def run(self):
        logger.info('Starting scraping (VivaReal)...')
        self.page = await self.new_page()
        while True:
            if self.last_page > self.url_cfg.page:
                logger.info('End scraping (VivaReal)...')
                break
            if self.last_page >= 1:
                url = self.url_cfg.build_url(new_page=True)
            else:
                url = self.url_cfg.build_url()
            await self.page.goto(url)
            logger.info(f'[BROWSER] => [GOTO] {url} - {self.last_page}')
            async for p in self.extract_property_info():
                self.extracted_properties.append(p)
                await self.add_house_to_db(p)
                cl.print(genetate_panel(p))
                # yield p
            self.last_page += 1

        return self.extracted_properties

    


if __name__ == "__main__":
    import os
    import sys
    import asyncio

    # Adiciona o diretório pai ao sys.path
    from playwright.async_api import async_playwright

    from scraping_houses.schemas import (
        ContactForm,
        ScrapingVivalrealConfig,
    )
        
    
    async def main(url_config: ScrapingVivalrealConfig):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            c_vivareal = ScrapingVivalreal(browser, url_config)
            await c_vivareal.run()
            
        
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
    asyncio.run(main(url_config=url_cfg))
