import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

# from scraping_houses.settings import Settings

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

def panel_grid(items: list[tuple[str, str]]) -> Table:
    grid = Table.grid(expand=True)
    grid.add_column(style='cyan', justify='left', no_wrap=True)
    grid.add_column(style='green', justify='center')
    grid.add_column(style='red', justify='right', no_wrap=True)
    for item in items:
        grid.add_row(item[0], '|', item[1])
    return grid

