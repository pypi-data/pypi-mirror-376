import random
import mimetypes

import html2text
from lxml import html, etree


def extract_metadata(page_source: str) -> dict:
    try:
        tree = html.fromstring(page_source)
    except Exception:
        return {}

    page_title = tree.xpath('//head/title/text()')
    page_description = tree.xpath('//head/meta[@name="description"]/@content')
    author = tree.xpath('//head/meta[@name="author"]/@content')
    twitter_handle = tree.xpath('//head/meta[@name="twitter:site"]/@content')

    result = {}

    if page_title:
        result['title'] = page_title[0]
    if page_description and valid_description_metadata(page_description[0]):
        result['description'] = page_description[0]
    if author:
        result['author'] = author[0]
    if twitter_handle:
        result['twitter'] = twitter_handle[0]

    return result


def valid_description_metadata(desc: str) -> bool:
    try:
        etree.fromstring(desc)
        return False
    except etree.XMLSyntaxError:
        return True


def generate_markdown(page_source: str, ignore_links: bool, ignore_images: bool) -> str:
    text_maker = html2text.HTML2Text()
    text_maker.ignore_links = ignore_links
    text_maker.ignore_images = ignore_images
    text_maker.body_width = 0  # Prevent automatic wrapping
    return text_maker.handle(page_source).strip()


def valid_type(url: str) -> bool:
    """
    Currently, only text / html pages are supported for extended data retrival.
    """
    mime, _ = mimetypes.guess_type(url)
    return mime in ('text/html', 'text/plain', 'application/xhtml+xml', None)
