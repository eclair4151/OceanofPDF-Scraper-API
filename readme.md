# Ocean of PDF Scraper

Search [Ocean of PDF](https://oceanofpdf.com/), browse an author's catalog, and download epubs (concurrently).

## Install

```shell
python3 -m pip install -r requirements.txt
```

## Modules

### `search.py` — search by query

Walks `https://oceanofpdf.com/?s=<query>` and follow-on pages until a page returns no results. Filters out non-English entries by default (entries with no language declared are kept).

```shell
python3 search.py "My Husband's Wife"
python3 search.py "My Husband's Wife" --language english
python3 search.py "My Husband's Wife" --download ./books
```

Programmatic use:

```python
from search import search

results = search("My Husband's Wife")                       # english only
results = search("My Husband's Wife", language=None)        # no filter
results = search("My Husband's Wife", download_to="./books")  # also downloads every hit
```

Each result is a dict: `title`, `href`, `date`, `author`, `language`, `genre` (author, language, and genre are not required).

### `author.py` — list a single author's books

Same parsing as search, but walks `https://oceanofpdf.com/category/authors/<slug>/page/N/`.

```shell
python3 author.py "Alice Feeney"
python3 author.py "Alice Feeney" --download ./books
```

```python
from author import by_author

results = by_author("Alice Feeney")
results = by_author("Alice Feeney", download_to="./books")  # grab the whole catalog
```

### `downloader.py` — download epub(s)

Takes one or more book page URLs (the `href` from a search/author result, e.g. `https://oceanofpdf.com/authors/alice-feeney/pdf-epub-my-husbands-wife-download/`), finds the epub form on each page, posts it to `Fetching_Resource.php`, follows the meta-refresh to the CDN, and writes the file to disk. PDF-only books raise `RuntimeError` — epub only.

Multiple URLs are downloaded concurrently (default 8 workers).

```shell
python3 downloader.py <destination_dir> <book_url> [<book_url> ...]
```

Programmatic use:

```python
from downloader import download, download_many

path = download(book_url, "/path/to/dir")              # one book, returns saved path
results = download_many(urls, "/path/to/dir")          # parallel; returns [(url, path, error), ...]
results = download_many(urls, "/path/to/dir", max_workers=16)
```

### `parser.py` — shared internals

`parse_page`, `paginate`, `filter_language`, `print_results`. Used by `search.py` and `author.py`.

## Typical flow

1. Call `search(...)` or `by_author(...)` to get candidates.
2. Either pick specific `href`s and pass them to `download_many(...)`, or pass `download_to=<dir>` to grab every result in one shot.

## License

[MIT](LICENSE.md)

---

Inspired by https://github.com/Krishna-Sivakumar/opdf-scraper

