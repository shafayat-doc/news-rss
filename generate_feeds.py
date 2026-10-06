import requests
from bs4 import BeautifulSoup
from email.utils import format_datetime
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
import html


# ============================================================
# WEBSITE SETTINGS
# ============================================================

WEBSITES = [
    {
        "name": "সমকাল",
        "feed_file": "samakal.xml",
        "url": "https://samakal.com/index.php/latest/news",
        "base_url": "https://samakal.com",
    },

    # We will add more websites here later.
]


# ============================================================
# GENERAL SETTINGS
# ============================================================

MAX_ITEMS = 30
OUTPUT_DIR = Path("feeds")
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


# ============================================================
# FETCH WEBSITE
# ============================================================

def get_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.text


# ============================================================
# CREATE RSS FEED
# ============================================================

def create_rss(site):

    print(f"Checking: {site['name']}")

    try:
        html_text = get_page(site["url"])
    except Exception as e:
        print(f"Could not access {site['name']}: {e}")
        return

    soup = BeautifulSoup(html_text, "html.parser")

    articles = []
    seen_urls = set()

    # Find article links
    for link in soup.find_all("a", href=True):

        href = link.get("href")

        if not href:
            continue

        article_url = urljoin(site["base_url"], href)

        # Samakal article URLs contain /article/
        if "/article/" not in article_url:
            continue

        if article_url in seen_urls:
            continue

        title = link.get_text(" ", strip=True)

        # Ignore links without meaningful titles
        if len(title) < 10:
            continue

        seen_urls.add(article_url)

        articles.append({
            "title": title,
            "url": article_url
        })

        if len(articles) >= MAX_ITEMS:
            break

    print(f"Found {len(articles)} articles")

    # --------------------------------------------------------
    # Build RSS XML
    # --------------------------------------------------------

    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom"
        }
    )

    channel = ET.SubElement(rss, "channel")

    ET.SubElement(
        channel,
        "title"
    ).text = site["name"]

    ET.SubElement(
        channel,
        "link"
    ).text = site["url"]

    ET.SubElement(
        channel,
        "description"
    ).text = f"Latest news from {site['name']}"

    ET.SubElement(
        channel,
        "language"
    ).text = "bn"

    ET.SubElement(
        channel,
        "lastBuildDate"
    ).text = format_datetime(
        datetime.now(timezone.utc)
    )

    # --------------------------------------------------------
    # Add articles
    # --------------------------------------------------------

    for article in articles:

        item = ET.SubElement(channel, "item")

        ET.SubElement(
            item,
            "title"
        ).text = article["title"]

        ET.SubElement(
            item,
            "link"
        ).text = article["url"]

        ET.SubElement(
            item,
            "guid",
            {"isPermaLink": "true"}
        ).text = article["url"]

        ET.SubElement(
            item,
            "description"
        ).text = article["title"]

    # --------------------------------------------------------
    # Save RSS
    # --------------------------------------------------------

    tree = ET.ElementTree(rss)

    output_file = OUTPUT_DIR / site["feed_file"]

    tree.write(
        output_file,
        encoding="utf-8",
        xml_declaration=True
    )

    print(f"Created: {output_file}")


# ============================================================
# MAIN
# ============================================================

for website in WEBSITES:
    create_rss(website)

print("RSS generation completed.")
