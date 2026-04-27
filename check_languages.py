import os
import re
import sys
import zipfile


def epub_language(path):
    try:
        with zipfile.ZipFile(path) as z:
            container = z.read("META-INF/container.xml").decode("utf-8", "ignore")
            m = re.search(r'full-path="([^"]+)"', container)
            if not m:
                return None
            opf = z.read(m.group(1)).decode("utf-8", "ignore")
            lang = re.search(r"<dc:language[^>]*>([^<]+)</dc:language>", opf, re.I)
            return lang.group(1).strip() if lang else None
    except (zipfile.BadZipFile, KeyError) as e:
        return f"<error: {e}>"


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "Books"
    if not os.path.isdir(folder):
        print(f"not a directory: {folder}")
        sys.exit(1)
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith(".epub"):
            continue
        path = os.path.join(folder, name)
        print(f"{epub_language(path) or '<none>':<10}  {name}")
