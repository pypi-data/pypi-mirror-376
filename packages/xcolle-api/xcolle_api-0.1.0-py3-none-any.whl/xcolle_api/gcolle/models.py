import dataclasses

from xcolle_api._common import Product


@dataclasses.dataclass(slots=True, kw_only=True)
class GcolleProduct(Product):
    category_id: int = dataclasses.field(repr=False)
    manufacturer_id: str = dataclasses.field(repr=False)
    video_preview: str | None = dataclasses.field(repr=False)
    root_category_id: int = dataclasses.field(repr=False)
