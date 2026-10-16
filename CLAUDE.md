# X-Cel Swim Group 5 calendar feed

`xcel-grp5.ics` on `main` is a live Apple Calendar subscription, served from
https://raw.githubusercontent.com/YA1Y/Xcel-calendar/main/xcel-grp5.ics
It is built from `events.json` by `build.py`. Never hand-edit the .ics.

Source: the monthly calendar images on https://swimxcel.org/calendar/ (one JPG per
month, e.g. `Oct2026v2.jpg`, `Nov26v1.jpg`; the July/August 2024 Google Sheets on that
page are an old example, ignore them). Only the **Grp 5** row matters.

## Daily update procedure

1. `python3 -I check.py /tmp/xcel-imgs` — exit 0 means nothing changed: stop, no commit.
2. For each NEW or CHANGED image: upscale it (2x, split into left/right halves so the
   small text is legible) and read every day's Grp 5 entry plus the pool in the day header.
   - The day header names the pool; if it lists two (e.g. "DeNunzio/MCCC"), use the pool
     written after Grp 5's time, else the first pool in the header.
   - Times are local (America/New_York); store as 24h "HH:MM".
   - Grp 5 blank = no practice that day. Meets/holidays/notes spanning the day go in
     `all_day` as [start, end, title, pool-key-or-""].
   - Footnotes (e.g. "**- practice only for swimmers going to X meet") go as the 5th
     field of the practice row.
3. Replace only that month's entries in `practices` and `all_day`; keep other months
   (including months that are GONE from the page). Keep rows sorted by date.
4. Record the image in `source_images[YYYY-MM]` with the url and sha256 printed by check.py.
   New pools: add the address from https://swimxcel.org/about-us/locations/ to `pools`.
5. `python3 build.py`, then sanity-check: parse the .ics (e.g. with `icalendar`) and
   list the month's events; compare against the image once more.
6. Commit `events.json` and `xcel-grp5.ics` directly to `main` with a message like
   "Update Grp 5 schedule: Dec 2026 added" and push. (The owner asked for daily updates
   to go straight to main; no PR for these data-only updates.)
