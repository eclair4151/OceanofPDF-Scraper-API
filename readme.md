# Ocean of PDF Scraper

Search [Ocean of PDF](https://oceanofpdf.com/), browse an author's catalog, and download epubs.

## Install

```shell
python3 -m pip install -r requirements.txt
```

## Modules

### `search.py` — search by query

Walks `https://oceanofpdf.com/?s=<query>` and follow-on pages until a page returns no results. Filters out non-English entries by default (entries with no language declared are kept).

```shell
python3 search.py "My Husband's Wife"
```

Programmatic use:

```python
from search import search

results = search("My Husband's Wife")          # english only
results = search("My Husband's Wife", language=None)  # no filter
```

Each result is a dict: `title`, `href`, `date`, `author`, `language`, `genre`.

### `author.py` — list a single author's books

Same parsing as search, but walks `https://oceanofpdf.com/category/authors/<slug>/page/N/`.

```shell
python3 author.py "Alice Feeney"
```

```python
from author import by_author

results = by_author("Alice Feeney")
```

### `downloader.py` — download an epub

Takes a book page URL (the `href` from a search/author result, e.g. `https://oceanofpdf.com/authors/alice-feeney/pdf-epub-my-husbands-wife-download/`), finds the epub form on the page, posts it to `Fetching_Resource.php`, follows the meta-refresh to the CDN, and writes the file to disk. PDF-only books raise `RuntimeError` — epub only.

```shell
python3 downloader.py <destination_dir> <book_url> [<book_url> ...]
```

Programmatic use:

```python
from downloader import download

path = download(book_url, "/path/to/dir")
```

### `parser.py` — shared internals

`parse_page`, `paginate`, `filter_language`, `print_results`. Used by `search.py` and `author.py`.

## Typical flow

1. Call `search(...)` or `by_author(...)` to get candidates.
2. Pick the `href` you want.
3. Pass it to `download(href, dest_dir)`.

## License

[MIT](LICENSE.md)
