"""Pydantic shapes for the shop agent.

ChatReply is what the widget receives. ProductCard is one real catalogue
piece inside that reply. ProductLookup and StockLookup are what the
catalogue tools return. Quote a price or a quantity only from those.
"""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field


class ProductCard(BaseModel):
    """One catalogue piece the website can render. Never invent these fields."""

    model_config = ConfigDict(populate_by_name=True)

    product_id: str = Field(alias="productId", description="The catalogue product_id.")
    name: str = Field(description="The catalogue name.")
    price: float = Field(description="The catalogue price in dollars.")
    image: str = Field(default="", description="Image path the shop already serves.")
    blurb: str = Field(
        default="",
        description="Short line from the catalogue description for the card.",
    )


class SizeCount(BaseModel):
    """One size and the inventory quantity for it."""

    size: str
    quantity: int = Field(description="Units in inventory for this size.")
    in_stock: bool = Field(description="False when quantity is 0. Say that size is out of stock.")


class ProductRecord(BaseModel):
    """One catalogue row, with the quantity in every size."""

    product_id: str
    name: str
    garment_type: str = ""
    description: str = Field(description="Catalogue description. Do not add details it does not state.")
    price: float = Field(description="Catalogue price in dollars. Quote this number.")
    colors: list[str] = Field(default_factory=list)
    image: str = ""
    description_is_stub: bool = Field(
        default=False,
        description="True when the description is only a filename stub. Do not invent the garment.",
    )
    sizes: list[SizeCount] = Field(default_factory=list)


class ProductLookup(BaseModel):
    """What lookup_product returns for a price or product question."""

    found: bool
    query: str = ""
    match_count: int = 0
    shown: list[ProductRecord] = Field(
        default_factory=list,
        description="Catalogue rows that matched. Quote a price only from this list.",
    )
    cards: list[ProductCard] = Field(
        default_factory=list,
        description="Structured matches the website renders. image, name, price, and blurb.",
    )
    note: str = Field(description="How to use this result. Follow it.")


class StockLookup(BaseModel):
    """What stock_by_size returns for a stock question."""

    found: bool
    product_id: str = ""
    name: str = ""
    price: float | None = Field(default=None, description="Catalogue price. Do not invent one.")
    size: str = Field(default="", description="The size asked for. Empty when every size is listed.")
    quantity: int | None = Field(default=None, description="Units for that size. 0 is out of stock.")
    in_stock: bool | None = Field(default=None, description="False means say that size is out of stock.")
    sizes: list[SizeCount] = Field(
        default_factory=list,
        description="Inventory counts. Quote a quantity only from this list.",
    )
    candidates: list[ProductCard] = Field(
        default_factory=list,
        description="More than one piece matched. Do not quote a quantity until one product_id is chosen.",
    )
    note: str = Field(description="How to use this result. Follow it.")


class ChatReply(BaseModel):
    """The stylist's answer, plus any real product cards a tool supplied."""

    reply: str = Field(description="What the stylist says, in the Campus Customs voice.")
    products: list[ProductCard] = Field(
        default_factory=list,
        description="Cards copied from lookup_product. The website renders this list.",
    )


@dataclass
class ShopperDeps:
    """Who is at the counter, and which page is open. Never a password."""

    user_id: int | None = None
    name: str = ""
    email: str = ""
    page_path: str = ""
    product_id: str = ""


class WearStop(BaseModel):
    """A real New Haven restaurant or social stop. Do not invent one."""

    kind: str = Field(description="restaurant or event.")
    name: str
    where: str
    why: str


class WearAdvice(BaseModel):
    """When to wear a queued piece, with weather icons and New Haven stops."""

    product_id: str = ""
    name: str = ""
    icons: list[str] = Field(default_factory=list, description="sun, cloud, rain, snow, wind, cold, or night.")
    when: str = ""
    stops: list[WearStop] = Field(default_factory=list)
    reply: str = ""
