from sqlalchemy import JSON, func
from sqlalchemy.orm import Mapped, mapped_column, registry
import re
from datetime import datetime
from typing import List

table_registry = registry()

@table_registry.mapped_as_dataclass
class TableProperty:
    __tablename__ = 'properties'
    
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    url: Mapped[str] = mapped_column(unique=True)
    status_code: Mapped[int]
    reason: Mapped[str]
    local_ip: Mapped[str]
    primary_ip: Mapped[str]
    title: Mapped[str]
    property_type: Mapped[str]
    price: Mapped[str]
    additional_price: Mapped[List[str]] = mapped_column(JSON)
    address: Mapped[str]
    properties: Mapped[List[str]] = mapped_column(JSON)
    description: Mapped[List[str]] = mapped_column(JSON)
    images: Mapped[List[str]] = mapped_column(JSON)
    published_at: Mapped[str]
    property_id: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )

    def __repr__(self):
        return f'<TableProperty {self.property_id}>'

    def __str__(self):
        return f'<Property {self.property_id}>'