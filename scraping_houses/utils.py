import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

# from scraping_houses.settings import Settings
from scraping_houses.schemas import HouseVivaReal

cl = Console()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(
        omit_repeated_times=False,
        rich_tracebacks=True,
        console=cl
        )]
)

logger = logging.getLogger()


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
