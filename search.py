from urllib.parse import quote_plus
import sys

from parser import paginate, filter_language, print_results


def search(query, language="english"):
    q = quote_plus(query)
    def page_url(page):
        if page == 1:
            return f"https://oceanofpdf.com/?s={q}"
        return f"https://oceanofpdf.com/page/{page}/?s={q}"
    results = list(paginate(page_url))
    if language:
        results = filter_language(results, language)
    return results


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "My Husband's Wife Alice"
    print_results(search(query))
