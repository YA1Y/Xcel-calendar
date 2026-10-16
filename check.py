"""Check swimxcel.org/calendar for new or changed month images.

Usage: python3 -I check.py OUT_DIR
Downloads every calendar-looking image into OUT_DIR and prints one line per image:
  UNCHANGED <month> <url>   same file and hash as recorded in events.json
  CHANGED   <month> <url>   recorded month, but the url or file contents differ
  NEW       <guess> <url>   not recorded yet (guess is the month read from the filename)
  GONE      <month> <url>   recorded but no longer on the page (keep its events)
Exit code 0 when everything is UNCHANGED/GONE, 1 when something needs reading.
"""
import hashlib, json, pathlib, re, sys, urllib.request

PAGE = "https://swimxcel.org/calendar/"
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
UA = {"User-Agent": "Mozilla/5.0 (xcel-calendar updater)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()

def guess_month(url):
    name = url.rsplit("/", 1)[-1].lower()
    m = re.match(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[_-]?(\d{4}|\d{2})", name)
    if not m:
        return None
    year = int(m.group(2)) + (2000 if len(m.group(2)) == 2 else 0)
    return f"{year}-{MONTHS[m.group(1)]:02d}"

out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
data = json.loads((pathlib.Path(__file__).parent / "events.json").read_text())
recorded = data["source_images"]
by_url = {v["url"]: k for k, v in recorded.items()}

html = get(PAGE).decode("utf-8", "replace")
urls = sorted(set(re.findall(r'src="(https://swimxcel\.org/wp-content/uploads/[^"]+\.(?:jpe?g|png))"', html)))
urls = [u for u in urls if guess_month(u) and not re.search(r"-\d+x\d+\.", u)]

seen, needs_reading = set(), False
for url in urls:
    body = get(url)
    (out / url.rsplit("/", 1)[-1]).write_bytes(body)
    digest = hashlib.sha256(body).hexdigest()
    month = by_url.get(url) or guess_month(url)
    seen.add(month)
    if month in recorded and recorded[month]["url"] == url and recorded[month]["sha256"] == digest:
        status = "UNCHANGED"
    else:
        status = "CHANGED" if month in recorded else "NEW"
        needs_reading = True
    print(f"{status:9} {month} {url} sha256={digest}")
for month, v in recorded.items():
    if month not in seen:
        print(f"{'GONE':9} {month} {v['url']}")
sys.exit(1 if needs_reading else 0)
