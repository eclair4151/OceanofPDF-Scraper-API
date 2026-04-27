from urllib.parse import quote
import sys

from parser import paginate, filter_language, print_results


def author_slug(name):
    return quote(name.strip().lower().replace(" ", "-"))


def by_author(name, language="english"):
    slug = author_slug(name)
    def page_url(page):
        base = f"https://oceanofpdf.com/category/authors/{slug}"
        if page == 1:
            return f"{base}/"
        return f"{base}/page/{page}/"
    results = list(paginate(page_url))
    if language:
        results = filter_language(results, language)
    return results


if __name__ == "__main__":
    name = " ".join(sys.argv[1:]) or "Alice Feeney"
    print_results(by_author(name))
