from urllib.parse import quote_plus
import argparse

from parser import paginate, filter_language, print_results
from downloader import download_many


def search(query, language="english", download_to=None):
    q = quote_plus(query)
    def page_url(page):
        if page == 1:
            return f"https://oceanofpdf.com/?s={q}"
        return f"https://oceanofpdf.com/page/{page}/?s={q}"
    results = list(paginate(page_url))
    if language:
        results = filter_language(results, language)
    if download_to:
        download_many([r["href"] for r in results if r.get("href")], download_to)
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("query", nargs="+")
    p.add_argument("--download", metavar="DIR", help="download every result to DIR")
    p.add_argument("--language", default="english", help="language filter (default: english)")
    args = p.parse_args()
    results = search(" ".join(args.query), language=args.language, download_to=args.download)
    print_results(results)
