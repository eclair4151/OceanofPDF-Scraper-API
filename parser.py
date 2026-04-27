from requests import get
from bs4 import BeautifulSoup
import json

headers = {'Accept-Encoding': 'identity', 'User-Agent': 'Defined'}


def parse_page(url):
    res = get(url, headers=headers)
    if res.status_code == 404:
        return []
    html = BeautifulSoup(res.text, "html.parser")

    results = []
    for article in html.select("article.post"):
        link = article.select_one("a.entry-title-link")
        time_el = article.select_one("time.entry-time")
        meta = article.select_one("div.postmetainfo")

        fields = {}
        if meta:
            for label in meta.find_all("strong"):
                key = label.get_text(strip=True).rstrip(":").strip()
                value = label.next_sibling
                fields[key] = value.strip(" \n") if isinstance(value, str) else None

        results.append({
            "title": link.get_text(strip=True) if link else None,
            "href": link["href"] if link else None,
            "date": time_el.get_text(strip=True) if time_el else None,
            "author": fields.get("Author"),
            "language": fields.get("Language"),
            "genre": fields.get("Genre"),
        })
    return results


def paginate(page_url):
    """page_url is a callable: page_num -> url. Stops on first empty page."""
    page = 1
    while True:
        url = page_url(page)
        print(f"fetching page {page}: {url}")
        results = parse_page(url)
        print(f"  page {page}: {len(results)} result(s)")
        if not results:
            return
        for r in results:
            yield r
        page += 1


def filter_language(results, language="english"):
    needle = language.lower()
    out = []
    for r in results:
        lang = r.get("language")
        if lang and needle not in lang.lower():
            continue
        out.append(r)
    return out


def print_results(results):
    # print
    print(json.dumps(results, indent=2, ensure_ascii=False))
    # for r in results:
    #     print(f"{r['title']}")
    #     print(f"  href:     {r['href']}")
    #     print(f"  date:     {r['date']}")
    #     print(f"  author:   {r['author']}")
    #     print(f"  language: {r['language']}")
    #     print(f"  genre:    {r['genre']}")
    #     print()
