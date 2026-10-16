"""Build xcel-grp5.ics from events.json. Usage: python3 build.py"""
import json, datetime, pathlib, hashlib

here = pathlib.Path(__file__).parent
d = json.loads((here / "events.json").read_text())
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def fold(line):
    out = []
    while len(line.encode()) > 73:
        out.append(line[:73]); line = " " + line[73:]
    return "\r\n".join(out + [line])

lines = [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//xcel-swim-calendar//EN", "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH", "X-WR-CALNAME:X-Cel Swim - Group 5", "X-WR-TIMEZONE:America/New_York",
    "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H",
    "BEGIN:VTIMEZONE", "TZID:America/New_York",
    "BEGIN:DAYLIGHT", "TZOFFSETFROM:-0500", "TZOFFSETTO:-0400", "TZNAME:EDT",
    "DTSTART:19700308T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU", "END:DAYLIGHT",
    "BEGIN:STANDARD", "TZOFFSETFROM:-0400", "TZOFFSETTO:-0500", "TZNAME:EST",
    "DTSTART:19701101T020000", "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU", "END:STANDARD",
    "END:VTIMEZONE",
]

def event(uid, props):
    lines.extend(["BEGIN:VEVENT", f"UID:{uid}@xcel-swim-calendar", f"DTSTAMP:{stamp}"])
    lines.extend(fold(p) for p in props)
    lines.append("END:VEVENT")

for p in d["practices"]:
    date, start, end, pool = p[:4]
    note = p[4] if len(p) > 4 else ""
    ds = date.replace("-", "")
    desc = f"{d['group']} practice. Source: {d['source']}" + (f"\n{note}" if note else "")
    event(f"grp5-{date}-{start.replace(':', '')}", [
        f"SUMMARY:{esc('Swim practice - ' + pool + (' (Peddie meet swimmers only)' if note else ''))}",
        f"DTSTART;TZID=America/New_York:{ds}T{start.replace(':', '')}00",
        f"DTEND;TZID=America/New_York:{ds}T{end.replace(':', '')}00",
        f"LOCATION:{esc(d['pools'].get(pool, pool))}",
        f"DESCRIPTION:{esc(desc)}",
    ])

for start, end, title, pool in d["all_day"]:
    e = datetime.date.fromisoformat(end) + datetime.timedelta(days=1)
    props = [f"SUMMARY:{esc(title)}", f"DTSTART;VALUE=DATE:{start.replace('-', '')}",
             f"DTEND;VALUE=DATE:{e.strftime('%Y%m%d')}", "TRANSP:TRANSPARENT",
             f"DESCRIPTION:{esc('Source: ' + d['source'])}"]
    if pool:
        props.append(f"LOCATION:{esc(d['pools'].get(pool, pool))}")
    event("allday-" + hashlib.sha1(f"{start}{title}".encode()).hexdigest()[:10], props)

lines.append("END:VCALENDAR")
(here / "xcel-grp5.ics").write_text("\r\n".join(lines) + "\r\n", newline="")
print(len(d["practices"]), "practices,", len(d["all_day"]), "all-day events")
