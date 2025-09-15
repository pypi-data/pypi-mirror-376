from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag
from httpx import AsyncClient, HTTPStatusError, RequestError

from not_my_ex.media import Media
from not_my_ex.mime import mime_for


async def request_bytes(client: AsyncClient, url: str) -> bytes | None:
    try:
        response = await client.get(url)
    except (HTTPStatusError, RequestError):
        return None
    if response.status_code != 200:
        return None
    return response.content


def meta(soup: BeautifulSoup, prop: str) -> str | None:
    tag = soup.find("meta", property=prop)
    if isinstance(tag, Tag) and tag.has_attr("content"):
        return str(tag["content"])
    return None


@dataclass
class Card:
    uri: str
    title: str
    description: str | None
    thumb: bytes | None
    mime: str | None

    @property
    def media(self):
        if not self.thumb or not self.mime:
            return None
        return Media(None, self.thumb, self.mime)

    @classmethod
    async def from_url(cls, url: str) -> "Card | None":
        async with AsyncClient() as client:
            html = await request_bytes(client, url)
            if html is None:
                return None

            soup = BeautifulSoup(html.decode("utf-8"), "html.parser")
            title = meta(soup, "og:title")
            if not title:
                return None

            uri = meta(soup, "og:url")
            if not uri:
                return None

            description = meta(soup, "og:description")
            thumb_url = meta(soup, "og:image")
            if not thumb_url:
                return Card(uri, title, description, None, None)

            if "://" not in thumb_url:
                thumb_url = f"{url}{thumb_url}"

            thumb = await request_bytes(client, thumb_url)
            if not thumb:
                return Card(uri, title, description, None, None)

            mime = mime_for(thumb_url, thumb)
            if not mime:
                return Card(uri, title, description, None, None)

        return Card(url, title, description, thumb, mime)
