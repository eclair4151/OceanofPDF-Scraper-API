import os
import re
import sys
import zipfile
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


def _looks_like_challenge(html_bytes):
    snippet = html_bytes[:2000].lower()
    return b"just a moment" in snippet or b"cf-chl" in snippet or b"cloudflare" in snippet


def download(book_url, destination):
    """Resolve the epub from an oceanofpdf book page and save it to destination.

    Raises RuntimeError with a descriptive message on any failure.
    Returns the saved file path.
    """
    # 1. fetch the book page
    page_res = requests.get(book_url, headers=HEADERS)
    if page_res.status_code != 200:
        raise RuntimeError(f"book page returned HTTP {page_res.status_code}")
    if _looks_like_challenge(page_res.content):
        raise RuntimeError("book page returned a Cloudflare challenge (likely rate-limited)")

    page = BeautifulSoup(page_res.content, "html.parser")
    forms = page.find_all("form")

    # 2. find the epub form; classify the failure if absent
    epub_form = None
    has_pdf_form = False
    for form in forms:
        fn = form.find("input", {"name": "filename"})
        if not fn:
            continue
        val = fn.get("value", "").lower()
        if val.endswith(".epub"):
            epub_form = form
            break
        if val.endswith(".pdf"):
            has_pdf_form = True
    if epub_form is None:
        if has_pdf_form:
            raise RuntimeError("book is PDF-only (no epub form on page)")
        if not any(f.find("input", {"name": "filename"}) for f in forms):
            raise RuntimeError(
                f"no download forms on page (got {len(forms)} form(s); "
                f"page len={len(page_res.content)}b — possible block or empty page)"
            )
        raise RuntimeError("no epub form found on page (unknown filename format)")

    form_id = epub_form.find("input", {"name": "id"})["value"]
    filename = epub_form.find("input", {"name": "filename"})["value"]
    post_url = epub_form.get("action")

    # 3. post to Fetching_Resource.php and parse meta refresh
    res = requests.post(post_url, headers=HEADERS, data={"id": form_id, "filename": filename})
    if res.status_code != 200:
        raise RuntimeError(f"resource POST returned HTTP {res.status_code}")
    if _looks_like_challenge(res.content):
        raise RuntimeError("resource POST returned a Cloudflare challenge")

    download_page = BeautifulSoup(res.content, "html.parser")
    refresh = download_page.find("meta", attrs={"http-equiv": lambda v: v and v.lower() == "refresh"})
    if refresh is None or not refresh.get("content"):
        metas = download_page.find_all("meta")
        raise RuntimeError(
            f"no meta-refresh on resource response (status={res.status_code}, "
            f"len={len(res.content)}b, metas={len(metas)})"
        )
    content_attr = refresh["content"]
    _, _, link = content_attr.partition("url=")
    link = link.strip()
    if not link:
        raise RuntimeError(f"meta-refresh missing url= part (content={content_attr!r})")
    if not link.lower().split("?")[0].endswith(".epub"):
        raise RuntimeError(f"resolved link is not an epub: {link!r}")

    # 4. fetch the file from the CDN
    out_path = os.path.join(destination, _filename_from_url(link))
    file_res = requests.get(link, headers=HEADERS, stream=True)
    if file_res.status_code != 200:
        raise RuntimeError(f"CDN returned HTTP {file_res.status_code} for {link}")
    ct = file_res.headers.get("content-type", "")
    if "html" in ct.lower():
        raise RuntimeError(f"CDN returned HTML (content-type={ct!r}) — likely a challenge")
    with open(out_path, "wb") as f:
        f.write(file_res.content)
    return out_path


def epub_language(path):
    """Return the dc:language value from an epub, or None if not found."""
    try:
        with zipfile.ZipFile(path) as z:
            container = z.read("META-INF/container.xml").decode("utf-8", "ignore")
            m = re.search(r'full-path="([^"]+)"', container)
            if not m:
                return None
            opf = z.read(m.group(1)).decode("utf-8", "ignore")
            lang = re.search(r"<dc:language[^>]*>([^<]+)</dc:language>", opf, re.I)
            return lang.group(1).strip() if lang else None
    except (zipfile.BadZipFile, KeyError):
        return None


def is_pdf_only_url(book_url):
    """oceanofpdf URLs include 'epub' in the slug when an epub is available."""
    return "epub" not in book_url.lower()


def download_many(book_urls, destination, max_workers=2, language="en"):
    """Download multiple books concurrently.

    Skips PDF-only URLs up front. After all downloads finish, opens each saved
    epub and deletes any whose dc:language doesn't contain `language`
    (case-insensitive substring; e.g. 'en' matches 'en', 'en-US', 'eng'). Pass
    language=None to skip the post-download check.
    Prints progress per finished item.
    Returns a list of (url, path_or_None, error_or_None) tuples.
    """
    book_urls = list(book_urls)
    results = []
    skipped = [u for u in book_urls if is_pdf_only_url(u)]
    book_urls = [u for u in book_urls if not is_pdf_only_url(u)]
    for u in skipped:
        print(f"skipped (PDF-only URL): {u}")
        results.append((u, None, RuntimeError("skipped: PDF-only URL")))
    if not book_urls:
        return results
    workers = min(max_workers, len(book_urls)) or 1
    print(f"downloading {len(book_urls)} book(s) with {workers} worker(s)")
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

    if language:
        needle = language.lower()
        for i, (url, path, err) in enumerate(results):
            if not path:
                continue
            lang = epub_language(path)
            if lang is None:
                print(f"kept (no dc:language tag): {path}")
                continue
            if needle in lang.lower():
                continue
            try:
                os.remove(path)
                print(f"deleted (lang={lang!r}, wanted {language!r}): {path}")
                results[i] = (url, None, RuntimeError(f"wrong language: {lang}"))
            except OSError as e:
                print(f"failed to delete {path}: {e}")
    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python downloader.py <destination> <book_url> [<book_url> ...]")
        sys.exit(1)
    download_many(sys.argv[2:], sys.argv[1])
