import feedparser
import re
import json
import html
import unicodedata
from urllib.parse import urlparse
from datetime import datetime, timedelta
import time
from dateutil import parser
import requests

def clean_text(text: str) -> str:
    # Eliminar HTML
    text = re.sub(r"<.*?>", "", text)
    # Decodificar entidades HTML (&amp; → &)
    text = html.unescape(text)
    # Normalizar caracteres raros
    text = unicodedata.normalize("NFKC", text)
    # Quitar espacios extra
    return text.strip()

def get_news_feed(limit: int = 5):
    url = "https://news.google.com/rss?hl=es-419&gl=US&ceid=US:es-419"
    feed = feedparser.parse(url)
    news_list = []

    for entry in feed.entries[:limit]:
        title = clean_text(entry.title)
        description = clean_text(entry.get("summary", ""))
        link = entry.get("source", {}).get("href", entry.link)

        parsed_url = urlparse(link)
        domain = parsed_url.netloc

        site_icon = f"https://logo.clearbit.com/{domain}"

        news_item = {
            "title": title,
            "description": description,
            "site_icon": site_icon,
            "link": link
        }
        news_list.append(news_item)

    return json.dumps(news_list, indent=4, ensure_ascii=False)

def get_news_feed1(url ,limit: int = 1000):
    
    feed = feedparser.parse(url)
    news_list = []

    for entry in feed.entries[:limit]:
        title = clean_text(entry.title)
        description = clean_text(entry.get("summary", ""))
        fecha_str = clean_text(entry.get("published", ""))
        try:
            fecha_obj = parser.parse(fecha_str)
            publicado = fecha_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            publicado = "Fecha no disponible"
        link = entry.get("source", {}).get("href", entry.link)
        parsed_url = urlparse(link)
        domain = parsed_url.netloc

        site_icon = f"https://logo.clearbit.com/{domain}"

        news_item = {
            "title": title,
            "description": description,
            "fecha": publicado,
            "site_icon": site_icon,
            "link": link
        }
        news_list.append(news_item)

    return json.dumps(news_list, indent=4, ensure_ascii=False)

def request_scraper():
    response = requests.get("https://news-public-api.onrender.com/api/noticias/?limit=1000")

    return response.json()




