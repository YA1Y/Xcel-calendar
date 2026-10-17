"""Check swimxcel.org/calendar for new or changed month images.

Usage: python3 -I check.py OUT_DIR
Every image in the page's main content is treated as a month calendar. Each is
downloaded into OUT_DIR and reported on one line:
  UNCHANGED <month> <url>   same file and hash as recorded in events.json
  CHANGED   <month> <url>   recorded month, but the url or file contents differ
  NEW       <month> <url>   month (read from the filename) not recorded yet
  UNKNOWN   ?       <url>   month can't be told from the filename, or two images
                            claim the same month: open the image to decide
  GONE      <month> <url>   recorded but no longer on the page (keep its events)
Exit code: 0 nothing to do, 1 something needs reading, 2 no calendar images found
(the page layout probably changed).
"""
import datetime, hashlib, json, pathlib, re, sys, urllib.request

PAGE = "https://swimxcel.org/calendar/"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
UA = {"User-Agent": "Mozilla/5.0 (xcel-calendar updater)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()

def calendar_images(html):
    """Full-size upload URLs of the images inside <main>, in page order; None if there is no <main>."""
    main = re.search(r"<main\b.*?</main>", html, re.S)
    if not main:
        return None
    urls = []
    for tag in re.findall(r"<img\b[^>]*>", main.group(0)):
        attrs = dict(re.findall(r'\s([\w-]+)="([^"]*)"', tag))
        # lazy loading keeps the real file in data-orig-src/data-src and a placeholder in src
        for key in ("data-orig-src", "data-src", "src"):
            url = attrs.get(key, "")
            if "/wp-content/uploads/" in url:
                url = re.sub(r"-\d+x\d+(?=\.\w+$)", "", url)  # resized copy -> original upload
                if url not in urls:
                    urls.append(url)
                break
    return urls

def month_from_filename(url, this_year):
    name = url.rsplit("/", 1)[-1].lower()
    m = re.search(r"(?<![a-z])(" + "|".join(MONTHS) + r")[a-z]*[ _-]?(\d{4}|\d{2})(?!\d)", name)
    if not m:
        return None
    year = int(m.group(2)) + (2000 if len(m.group(2)) == 2 else 0)
    if abs(year - this_year) > 1:
        return None
    return f"{year}-{MONTHS.index(m.group(1)) + 1:02d}"

def check(html, data, fetch, out, this_year):
    """Return (report lines, exit code)."""
    urls = calendar_images(html)
    ignored = set(data.get("ignored_images", []))
    urls = [u for u in urls or [] if u not in ignored]
    if not urls:
        return ["NO CALENDAR IMAGES FOUND on " + PAGE], 2
    recorded = data["source_images"]
    by_url = {v["url"]: k for k, v in recorded.items()}
    lines, seen, needs_reading = [], set(), False
    for url in urls:
        body = fetch(url)
        (out / url.rsplit("/", 1)[-1]).write_bytes(body)
        digest = hashlib.sha256(body).hexdigest()
        month = by_url.get(url) or month_from_filename(url, this_year)
        if month is None or month in seen:
            status, month = "UNKNOWN", "?"
        elif month in recorded and recorded[month]["url"] == url and recorded[month]["sha256"] == digest:
            status = "UNCHANGED"
        else:
            status = "CHANGED" if month in recorded else "NEW"
        seen.add(month)
        needs_reading |= status != "UNCHANGED"
        lines.append(f"{status:9} {month:7} {url} sha256={digest}")
    for month, v in recorded.items():
        if month not in seen:
            lines.append(f"{'GONE':9} {month:7} {v['url']}")
    return lines, 1 if needs_reading else 0

if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    data = json.loads((pathlib.Path(__file__).parent / "events.json").read_text())
    lines, code = check(get(PAGE).decode("utf-8", "replace"), data, get, out, datetime.date.today().year)
    print("\n".join(lines))
    sys.exit(code)
