"""Free public RSS headlines for NBA coaching news; fail closed on network errors."""
import datetime as dt
import email.utils
import json
import pathlib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

OUT = pathlib.Path("feed/nba_coaches_news.json")
QUERIES = [
    'NBA coach rotation minutes restriction player lineup when:3d',
    'NBA head coach press conference starting lineup injury when:3d',
]
def collect():
    articles = {}
    for query in QUERIES:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
            {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
        req = urllib.request.Request(url, headers={"User-Agent": "KennySportsLab/1.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            root = ET.fromstring(response.read(2_000_000))
        for item in root.findall("./channel/item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if not title or not link.startswith("https://"):
                continue
            source = item.find("source")
            published = (item.findtext("pubDate") or "").strip()
            articles[link] = {"title": title[:240], "url": link,
                              "source": (source.text or "").strip() if source is not None else "Google News",
                              "published": published}
    return list(articles.values())[:30]

def main():
    try:
        items = collect()
        if not items:
            raise ValueError("No verified headlines")
    except Exception as exc:
        print("No new coaching-news feed: " + str(exc))
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                               "source": "google-news-rss-public-search", "items": items}, indent=2) + "\n")
    print(f"Saved {len(items)} attributed NBA news items")

if __name__ == "__main__":
    main()
