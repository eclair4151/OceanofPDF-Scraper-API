import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36"
}


def _filename_from_url(url):
    return url.split("/")[-1].split("?")[0]


def download(book_url, destination):
    """Resolve the epub from an oceanofpdf book page and save it to destination.

    Raises RuntimeError if the resolved file is not an epub.
    Returns the saved file path.
    """
    page = BeautifulSoup(requests.get(book_url, headers=HEADERS).content, "html.parser")

    epub_form = None
    for form in page.find_all("form"):
        fn = form.find("input", {"name": "filename"})
        if fn and fn.get("value", "").lower().endswith(".epub"):
            epub_form = form
            break
    if epub_form is None:
        raise RuntimeError("no epub form found on page")

    form_id = epub_form.find("input", {"name": "id"})["value"]
    filename = epub_form.find("input", {"name": "filename"})["value"]
    post_url = epub_form.get("action")

    res = requests.post(post_url, headers=HEADERS, data={"id": form_id, "filename": filename})
    download_page = BeautifulSoup(res.content, "html.parser")
    link = download_page.find_all("meta")[-1]["content"][6:]

    if not link.lower().split("?")[0].endswith(".epub"):
        raise RuntimeError(f"resolved link is not an epub: {link}")

    out_path = os.path.join(destination, _filename_from_url(link))
    with open(out_path, "wb") as f:
        f.write(requests.get(link, headers=HEADERS, stream=True).content)
    return out_path


def download_many(book_urls, destination, max_workers=8):
    """Download multiple books concurrently.

    Prints progress per finished item.
    Returns a list of (url, path_or_None, error_or_None) tuples.
    """
    book_urls = list(book_urls)
    results = []
    workers = min(max_workers, len(book_urls)) or 1
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(download, url, destination): url for url in book_urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                path = future.result()
                print(f"saved: {path}")
                results.append((url, path, None))
            except Exception as e:
                print(f"error ({url}): {e}")
                results.append((url, None, e))
    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python downloader.py <destination> <book_url> [<book_url> ...]")
        sys.exit(1)
    download_many(sys.argv[2:], sys.argv[1])
