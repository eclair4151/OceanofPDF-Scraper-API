from urllib.parse import quote
import argparse

from parser import paginate, filter_language, print_results
from downloader import download_many


def author_slug(name):
    return quote(name.strip().lower().replace(" ", "-"))


def by_author(name, language="english", download_to=None):
    slug = author_slug(name)
    def page_url(page):
        base = f"https://oceanofpdf.com/category/authors/{slug}"
        if page == 1:
            return f"{base}/"
        return f"{base}/page/{page}/"
    results = list(paginate(page_url))
    if language:
        results = filter_language(results, language)
    if download_to:
        download_many([r["href"] for r in results if r.get("href")], download_to)
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("name", nargs="+")
    p.add_argument("--download", metavar="DIR", help="download every result to DIR")
    p.add_argument("--language", default="english", help="language filter (default: english)")
    args = p.parse_args()
    results = by_author(" ".join(args.name), language=args.language, download_to=args.download)
    # results = by_author("Colleen Hoover", language='english', download_to='./Books/')
    print_results(results)
