from __future__ import annotations

import datetime
import logging
import re
from typing import TYPE_CHECKING

import yarl

from xcolle_api import _css, _utils
from xcolle_api._common import API, HumanBytes, ProductCategory, ProductTag
from xcolle_api.gcolle.models import GcolleProduct

if TYPE_CHECKING:
    from collections.abc import Iterable

    import bs4


logger = logging.getLogger(__name__)
_PRIMARY_URL = yarl.URL("https://gcolle.net/")


def _parse_url(string: str) -> yarl.URL:
    return _utils.parse_url(string.replace("/uploader/", "/"), _PRIMARY_URL)


class GcolleAPI(API):
    async def product(self, product_id: str, /) -> GcolleProduct:
        if not isinstance(product_id, str):
            raise TypeError(f"Invalid product_id = {product_id}")

        if not product_id.isalnum():
            raise ValueError(f"Invalid product_id = {product_id}")

        url = (_PRIMARY_URL / "product/detail/").update_query(product_id=product_id)
        soup = await self._fetch_webpage(url)
        return _parse_product(soup, url)


def _parse_product(soup: bs4.BeautifulSoup, url: yarl.URL) -> GcolleProduct:
    product_id = url.query["product_id"]
    main_section = _css.select_one(soup, "body > div.container")
    info_table = _css.select_one(main_section, "div.border-info table")

    def _parse_video_preview() -> str | None:
        try:
            source = _css.select_one(main_section, "video.video-js source")
        except _css.SelectorError:
            return None
        else:
            return str(_parse_url(_css.attr(source, "src")))

    def _parse_tags() -> Iterable[ProductTag]:
        for a_tag in main_section.select("p#tags a"):
            url = _parse_url(_css.attr(a_tag, "href"))
            yield ProductTag(id=int(url.name), name=a_tag.get_text(strip=True))

    human_bytes = HumanBytes(
        re.sub(
            r"\D",
            "",
            _css.select_one(_css.get_td(info_table, "File size:"), "small.text-muted").text,
        )
    )
    manufacturer_id = _css.attr(_css.select_one(soup, "#manufacturer dd a"), "href").rsplit("/", 1)[
        -1
    ]

    category_url = _css.attr(_css.select_one(main_section, "a.btn-info:last-of-type"), "href")

    return GcolleProduct(
        id=product_id,
        ratings=0,
        set="",
        additional_info=(),
        description_html="",
        url=str(url),
        category=ProductCategory(1, ""),
        price=int(
            re.sub(
                r"\D",
                "",
                _css.select_one(main_section, "b:has(span.fa-yen-sign)").get_text(),
            ).strip()
        ),
        manufacturer_id=manufacturer_id,
        seller_id=manufacturer_id,
        category_id=int(category_url.rsplit("/", 1)[-1].rsplit("_", 1)[-1]),
        root_category_id=int(category_url.rsplit("/", 1)[-1].rsplit("_", 1)[0]),
        description=(
            _css.select_one(main_section, "#description p").get_text().replace("\r\n", "\n").strip()
        ),
        title=_css.select_one(main_section, "h1").get_text(strip=True),
        previews=tuple(
            str(_parse_url(_css.attr(img, "src")))
            for img in main_section.select("a[data-gallery='banners'] img")
        ),
        tags=tuple(_parse_tags()),
        thumbnail=str(_parse_url(_css.attr(_css.select_one(main_section, "a img"), "src"))),
        video_preview=_parse_video_preview(),
        file_name=_css.get_td(info_table, "File name:").get_text(strip=True),
        file_size_bytes=int(human_bytes),
        file_size=human_bytes.to_string(),
        sales_start_date=datetime.datetime.fromisoformat(
            _css.attr(
                _css.select_one(_css.get_td(info_table, "Uploaded:"), "small.text-muted date"),
                "datetime",
            )
        ),
        views=int(re.sub(r"\D", "", _css.get_td(info_table, "Page viewed:").text)),
        contains=tuple(
            _css.attr(a_tag, "href").rsplit("/", 1)[-1]
            for a_tag in _css.get_td(info_table, "Contains:").select("a")
        ),
    )
