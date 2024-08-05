import re, sys, os
from enum import Enum
from typing import List, Union
from random import randint
from datetime import datetime
import asyncio


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from scraping_houses.utils import cl, panel_grid, logger
from scraping_houses.database import engine
from scraping_houses.schemas import (
    UrlConfig,
    Property,
    Page,
)
from scraping_houses.models import TableProperty


from curl_cffi.requests import AsyncSession, Request
from pydantic import BaseModel
from parsel import Selector
from sqlalchemy.orm import Session

from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.progress import Progress


class ScrapingVivalreal:
    def __init__(self, url_config: UrlConfig = None):
        self.url_cfg = url_config
        self.pages: List[Page] = []
        self.total_properties: int = 0
        self.last_page: int = 0
        
        if not self.url_cfg:
            self.url_cfg = UrlConfig()

    @property
    def total_urls(self) -> int:
        return len([[p.url for p in p.properties] for p in self.pages])

    @property
    def total_pages(self):
        return self.total_properties // 36

    def build_url(self, page: int = 0) -> str:
        cfg = self.url_cfg
        url = f"/{cfg.house_type}"
        if cfg.state:
            url += f"/{cfg.state}"
        if cfg.country and cfg.state:
            url += f"/{cfg.country}"
        if cfg.region and self.country:
            url += f"/{cfg.region}"
        # flags
        flags = []
        if cfg.property_type:
            property_type = ','.join(cfg.property_type)
            flags.append(f'tipos={property_type}')
        if cfg.rooms:
            flags.append(f"quartos={cfg.rooms}")
        if cfg.min_price:
            flags.append(f"preco-desde={cfg.min_price}")
        if cfg.max_price:
            flags.append(f"preco-ate={cfg.max_price}")
        if cfg.order_by_price:
            flags.append(f"ordenar-por={cfg.order_by_price}")
        url += f"?pagina={page}"
        query_string = "&".join(flags)
        return f"{url}#{query_string}"

    def next_page(self):
        url = self.build_url(self.last_page + 1)
        self.last_page += 1
        return url

    def get_urls(self, html: str) -> List[Property]:
        try:
            sel = Selector(html)
            return [
                Property(url=url) for url in
                sel.css(
                    'article.property-card__container \
                        a.property-card__content-link::attr(href)'
                ).getall()
            ]
        except Exception as e:
            logger.error(f'[SELECTOR] {e}')
            return []

    def get_total_properties(self, html: str) -> int:
        try:
            return int(Selector(html).css(
                '.results-summary__data strong.results-summary__count::text'
            ).get().replace('.', ''))
        except Exception as e:
            logger.error(f'[SELECTOR] {e}')
            return 0

    def get_current_page(self, html: str) -> int:
        try:
            return int(Selector(html).css(
                'button.js-change-page[data-active]::attr(data-page)'
            ).get())
        except Exception as e:
            logger.error(f'[SELECTOR] {e}')
            return 0

    def extract_all_content_from_page(
        self,
        html: str,
        property: Property,
    ) -> Property:
        s = Selector(html)
        p = property
        p.title = s.css('h1.description__title::text').get()
        p.property_type = s.css(
            '.price-value-wrapper p#business-type-info::text'
        ).get()
        p.price = s.css('p.price-info-value::text').get()
        p.additional_price = s.css(
            'p.additional-price-info--value::text'
        ).getall()
        p.address = s.css('p.address-info-value::text').get()
        p.properties = s.css('p.amenities-item::text').getall()
        p.description = s.css(
            'div.desktop-only-container .description__content--text::text'
        ).get()
        p.published_at = s.css(
            'div.desktop-only-container span.description__created-at::text'
        ).get()
        p.images = s.css(
            'li.carousel-photos--item img::attr(srcset)'
        ).getall()
        return p


    async def get_all_content_from_page(
            self, 
            session: AsyncSession, 
            page: Page
        ) -> Page:
            for p in page.properties:
                if self.property_exists_on_db(p):
                    logger.info(f'[MAIN] => {p} already exists on db, skipping..')
                    continue
                logger.info(f'[REQUEST] => {p.url}')
                req = await session.get(p.url)
                logger.info(f'[RESPONSE] <= {req}')
                p = self.extract_all_content_from_page(req.text, p)
                p.status_code=req.status_code
                p.reason=req.reason
                p.local_ip=req.local_ip
                p.primary_ip=req.primary_ip
                await self.add_property_to_db(p)
                await asyncio.sleep(randint(1,5))
            return page

    def property_exists_on_db(self, property: Property) -> bool:
        with Session(engine) as session:
            req = session.query(TableProperty).filter_by(
                url=property.url
            ).first()
            if req:
                logger.info(f'[DB] => [EXIST] {req}')
                return True
            logger.info(f'[DB] => [NOT EXIST] {req}')
            return False

    @staticmethod
    async def add_property_to_db(property: Property):
        with Session(engine) as session:         
            p = property
            db_house: TableProperty = TableProperty(
                url=p.url,
                status_code=p.status_code,
                reason=p.reason,
                local_ip=p.local_ip,
                primary_ip=p.primary_ip,
                title=p.title,
                property_type=p.property_type,
                price=p.price,
                additional_price=p.additional_price,
                address=p.address,
                properties=p.properties,
                description=p.description,
                images=p.images,
                published_at=p.published_at,
                property_id=p.property_id,
            )
            session.add(db_house)
            session.commit()
            session.refresh(db_house)
            logger.info(f'[DB] => [ADD] {db_house}')
        return db_house

    
    def panel_page(self, page: Page) -> Panel:
        logger.info(f'[RICH] => {page}')
        return Panel(
            Columns([
                Panel(
                    panel_grid(
                            [   (
                                    f'Url: {p.url}',
                                    f'Status: {p.property_id}'
                                ),
                                (
                                    f'Status code: {p.status_code}',
                                    f'Price: {p.price}'
                                ),
                                (
                                    f'Reason: {p.reason}',
                                    f'Additional price: {p.additional_price}'
                                    ),
                                (
                                    f'Local IP: {p.local_ip}',
                                    f'Address: {p.address}'
                                ),
                                (
                                    f'Primary IP: {p.primary_ip}',
                                    f'Published at: {p.published_at}'
                                ),
                            ]
                        ),
                    width=60,
                    title=f'# {p.property_id} - {p.title}'
                ) for p in page.properties
                
            ]),
            expand=True,
            title=f'{page.page} - {page.url} ({len(page.properties)})',
        )

    
    async def run(self):
        def status():
            orde = 0
            if len(self.pages) != 0:
                orde = len(self.pages[-1].properties)
            return Panel(
                f'Ord: {orde}\n\
                Url: {url}\n\
                Page: {self.last_page} - {self.total_pages}',
                title='Scraping...'
            )
        async with AsyncSession(
            base_url=self.url_cfg.url_base,
            impersonate='chrome',
            allow_redirects=True
            ) as s:
            url = self.build_url()
            with cl.status('Scraping...') as ss:
                for _ in range(1, 100):
                    ss.update(status())
                    req = await s.get(url)
                    urls = self.get_urls(req.text)
                    if self.last_page == 0 or self.total_pages == 0:
                        self.total_properties = self.get_total_properties(req.text)
                    self.last_page = self.get_current_page(req.text)
                    ss.update(status())
                    #TODO: Verificar se o registro ja esta no banco de dados com base no ID
                    #TODO: E se deveremos ignorar ou atualizar/criar um novo registro
                    page = await self.get_all_content_from_page(
                        s,
                        Page(
                            url=url,
                            status_code=req.status_code,
                            reason=req.reason,
                            local_ip=req.local_ip,
                            primary_ip=req.primary_ip,
                            html=req.text,
                            request_at=datetime.now(),
                            properties=urls,
                            page=self.last_page
                        )
                    )
                    cl.print(self.panel_page(page))
                    ss.update(status())
                    self.pages.append(page)

                    cl.print(
                        Panel(
                            panel_grid([
                                (f'Last Page: {self.last_page}'),
                                (f'Total pages: {self.total_pages}'),
                                (f'Total properties: {self.total_properties}'),
                                (f'Total urls: {self.total_urls}')
                            ]),
                            title='Resume',
                        )
                    )
                    url = self.next_page()
                    await asyncio.sleep(3)


if __name__ == "__main__":
    import asyncio
    
    asyncio.run(ScrapingVivalreal().run())
