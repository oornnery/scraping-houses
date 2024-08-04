from datetime import datetime

from sqlalchemy import func, JSON
from sqlalchemy.orm import Mapped, mapped_column, registry

table_registry = registry()


@table_registry.mapped_as_dataclass
class TableHouseVivaReal:
    __tablename__ = 'houses-vivareal'
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    url: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str]
    price: Mapped[str]
    additional_price: Mapped[list] = mapped_column(JSON)
    address: Mapped[str]
    properties: Mapped[list] = mapped_column(JSON)
    house_type: Mapped[str]
    images : Mapped[list] = mapped_column(JSON)
    description: Mapped[str]
    published_at: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )