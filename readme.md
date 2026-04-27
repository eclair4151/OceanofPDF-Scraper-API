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
python3 search.py "My Husband's Wife" --language english
python3 search.py "My Husband's Wife" --download ./books
```

Programmatic use:

```python
from search import search

results = search("My Husband's Wife")                         # english only
results = search("My Husband's Wife", language=None)          # no filter
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

Takes one or more book page URLs (the `href` from a search/author result, e.g. `https://oceanofpdf.com/authors/alice-feeney/pdf-epub-my-husbands-wife-download/`), finds the epub form on each page, posts it to `Fetching_Resource.php`, follows the meta-refresh to the CDN, and writes the file to disk.

Two filters are applied:

- **Pre-download**: any URL without `epub` in its path is skipped (PDF-only listing).
- **Post-download**: each saved epub is opened and its `dc:language` tag is checked. Files whose language doesn't contain the requested code are deleted. Default is `"en"` (matches `en`, `en-US`, `en-UK`, `eng`, …). Files missing a language tag are kept. Pass `language=None` to disable.

```shell
python3 downloader.py <destination_dir> <book_url> [<book_url> ...]
```

Programmatic use:

```python
from downloader import download, download_many, epub_language

path = download(book_url, "/path/to/dir")               # one book, returns saved path
results = download_many(urls, "/path/to/dir")           # default lang='en'
results = download_many(urls, "/path/to/dir", language="es")
results = download_many(urls, "/path/to/dir", language=None)  # no language check
lang = epub_language("/path/to/file.epub")              # 'en', 'en-US', None, ...
```

Errors during a `download_many` run don't abort the batch — they're logged per-URL and recorded in the returned `(url, path, error)` tuples.

### `parser.py` — shared internals

`parse_page`, `paginate`, `filter_language`, `print_results`. Used by `search.py` and `author.py`.

### `check_languages.py` — audit downloaded epubs

Walks a folder and prints each epub's `dc:language` value. Useful for spot-checking a directory of downloads.

```shell
python3 check_languages.py            # defaults to ./Books
python3 check_languages.py ./somedir
```

## Typical flow

1. Call `search(...)` or `by_author(...)` to get candidates.
2. Either pick specific `href`s and pass them to `download_many(...)`, or pass `download_to=<dir>` to grab every result in one shot.

## License

[MIT](LICENSE.md)

---

Inspired by https://github.com/Krishna-Sivakumar/opdf-scraper
