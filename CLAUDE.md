# X-Cel Swim Group 5 calendar feed

`xcel-grp5.ics` on `main` is a live Apple Calendar subscription, served from
https://raw.githubusercontent.com/YA1Y/Xcel-calendar/main/xcel-grp5.ics
It is built from `events.json` by `build.py`. Never hand-edit the .ics.

Source: the monthly calendar images on https://swimxcel.org/calendar/ (one JPG per
month, e.g. `Oct2026v2.jpg`, `Nov26v1.jpg`; the July/August 2024 Google Sheets on that
page are an old example, ignore them). Only the **Grp 5** row matters.

The page shows a rolling window of months: each month a new image goes up and the
oldest comes down, and a posted month is sometimes replaced by a revised version
(`v1` → `v2`). `check.py` treats every image inside the page's `<main>` as a month
calendar and compares it with `source_images`. Months that come down stay in
`events.json` and the feed, so past practices remain in the calendar.

## Daily update procedure

1. `python3 -I check.py /tmp/xcel-imgs`.
   - Exit 0: nothing to do (GONE lines are expected after a month comes down). Stop, no commit.
   - Exit 2: no calendar images found, so the page layout probably changed. Don't guess:
     tell the owner and stop.
   - Exit 1: handle each NEW, CHANGED and UNKNOWN line below.
2. Open each flagged image. The month and year are the ones **printed in the image's
   title**, not the filename (a filename can have a typo, e.g. `Jan26` for January 2027).
   - UNKNOWN that isn't a month calendar (a poster, a map): add its url to
     `ignored_images` and skip it.
   - UNKNOWN because two images claim one month: transcribe the newer version (higher
     `vN`, or the later upload folder) and add the other's url to `ignored_images`.
   - Upscale the image (2x, split into left/right halves so the small text is legible)
     and read every day's Grp 5 entry plus the pool in the day header.
   - The day header names the pool; if it lists two (e.g. "DeNunzio/MCCC"), use the pool
     written after Grp 5's time, else the first pool in the header.
   - Times are local (America/New_York); store as 24h "HH:MM".
   - Grp 5 blank = no practice that day. Meets/holidays/notes spanning the day go in
     `all_day` as [start, end, title, pool-key-or-""].
   - Footnotes (e.g. "**- practice only for swimmers going to X meet") go as the 5th
     field of the practice row.
3. Replace only that month's entries in `practices` and `all_day`; keep other months
   (including months that are GONE from the page). An `all_day` row belongs to the month
   of its start date. Keep rows sorted by date.
4. Record the image in `source_images[YYYY-MM]` (the month from the image title) with the
   url and sha256 printed by check.py, replacing that month's previous entry.
   New pools: add the address from https://swimxcel.org/about-us/locations/ to `pools`.
5. `python3 build.py`, then sanity-check: parse the .ics (e.g. with `icalendar`) and
   list the month's events; compare against the image once more. Re-run check.py: it
   should now exit 0.
6. Commit `events.json` and `xcel-grp5.ics` directly to `main` with a message like
   "Update Grp 5 schedule: Dec 2026 added" and push. (The owner asked for daily updates
   to go straight to main; no PR for these data-only updates.)

Changes to `check.py`/`build.py` go through a PR, with `python3 -m unittest test_check` passing.
