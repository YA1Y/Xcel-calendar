"""Scenario tests for check.py. Run: python3 -m unittest test_check"""
import hashlib, pathlib, tempfile, unittest
import check

U = "https://swimxcel.org/wp-content/uploads/"
PLACEHOLDER = "data:image/svg+xml,%3Csvg%3E%3C/svg%3E"

def page(*calendar_urls, main=True):
    """A page shaped like the real one: logo/menu images outside <main>, lazy-loaded calendars inside."""
    imgs = "".join(f'<img decoding="async" src="{PLACEHOLDER}" data-orig-src="{u}" alt="" width="969">'
                   for u in calendar_urls)
    body = f"<h2>Summer Calendar Example:</h2>{imgs}"
    header = f'<img src="{U}2023/02/XCEL-Logo-0209.png"><img src="{U}2025/06/Team-Photo-Oct2025.jpg">'
    return f"<html>{header}" + (f'<main id="main">{body}</main>' if main else body) + "</html>"

def sha(b):
    return hashlib.sha256(b).hexdigest()

FILES = {U + "2026/09/Oct2026v2.jpg": b"oct", U + "2026/10/Nov26v1.jpg": b"nov"}

def data(**extra):
    d = {"source_images": {
        "2026-10": {"url": U + "2026/09/Oct2026v2.jpg", "sha256": sha(b"oct")},
        "2026-11": {"url": U + "2026/10/Nov26v1.jpg", "sha256": sha(b"nov")}}}
    d.update(extra)
    return d

class CheckTest(unittest.TestCase):
    def run_check(self, html, d=None, files=None):
        files = {**FILES, **(files or {})}
        with tempfile.TemporaryDirectory() as out:
            lines, code = check.check(html, d or data(), files.__getitem__, pathlib.Path(out), 2026)
        return {(l.split()[0], l.split()[1]) for l in lines}, code

    def test_current_page_needs_nothing(self):
        got, code = self.run_check(page(U + "2026/09/Oct2026v2.jpg", U + "2026/10/Nov26v1.jpg"))
        self.assertEqual(got, {("UNCHANGED", "2026-10"), ("UNCHANGED", "2026-11")})
        self.assertEqual(code, 0)

    def test_monthly_turnover_old_gone_new_added(self):
        dec = U + "2026/11/Dec26v1.jpg"
        got, code = self.run_check(page(U + "2026/10/Nov26v1.jpg", dec), files={dec: b"dec"})
        self.assertEqual(got, {("GONE", "2026-10"), ("UNCHANGED", "2026-11"), ("NEW", "2026-12")})
        self.assertEqual(code, 1)

    def test_old_month_removed_only_is_not_work(self):
        got, code = self.run_check(page(U + "2026/10/Nov26v1.jpg"))
        self.assertEqual(got, {("GONE", "2026-10"), ("UNCHANGED", "2026-11")})
        self.assertEqual(code, 0)

    def test_revised_version_is_changed(self):
        v2 = U + "2026/10/Nov26v2.jpg"
        got, code = self.run_check(page(U + "2026/09/Oct2026v2.jpg", v2), files={v2: b"nov v2"})
        self.assertIn(("CHANGED", "2026-11"), got)
        self.assertEqual(code, 1)

    def test_same_url_new_contents_is_changed(self):
        got, code = self.run_check(page(U + "2026/09/Oct2026v2.jpg", U + "2026/10/Nov26v1.jpg"),
                                   files={U + "2026/10/Nov26v1.jpg": b"nov edited"})
        self.assertIn(("CHANGED", "2026-11"), got)
        self.assertEqual(code, 1)

    def test_resized_copy_maps_to_original_upload(self):
        got, code = self.run_check(page(U + "2026/09/Oct2026v2-1024x560.jpg", U + "2026/10/Nov26v1.jpg"))
        self.assertEqual(got, {("UNCHANGED", "2026-10"), ("UNCHANGED", "2026-11")})

    def test_year_rollover(self):
        jan = U + "2026/12/January-2027.jpg"
        got, _ = self.run_check(page(U + "2026/10/Nov26v1.jpg", jan), files={jan: b"jan"})
        self.assertIn(("NEW", "2027-01"), got)

    def test_filename_without_month_is_unknown_until_recorded(self):
        odd = U + "2026/11/calendar-final.jpg"
        got, code = self.run_check(page(U + "2026/10/Nov26v1.jpg", odd), files={odd: b"dec"})
        self.assertIn(("UNKNOWN", "?"), got)
        self.assertEqual(code, 1)
        d = data()
        d["source_images"]["2026-12"] = {"url": odd, "sha256": sha(b"dec")}
        got, code = self.run_check(page(U + "2026/10/Nov26v1.jpg", odd), d=d, files={odd: b"dec"})
        self.assertIn(("UNCHANGED", "2026-12"), got)
        self.assertEqual(code, 0)

    def test_wrong_year_in_filename_once_recorded_by_url(self):
        typo = U + "2026/12/Jan26v1.jpg"  # really January 2027
        d = data()
        d["source_images"]["2027-01"] = {"url": typo, "sha256": sha(b"jan")}
        got, code = self.run_check(page(U + "2026/10/Nov26v1.jpg", typo), d=d, files={typo: b"jan"})
        self.assertIn(("UNCHANGED", "2027-01"), got)
        self.assertEqual(code, 0)

    def test_two_images_for_one_month_is_unknown(self):
        v2 = U + "2026/10/Nov26v2.jpg"
        got, code = self.run_check(page(U + "2026/10/Nov26v1.jpg", v2), files={v2: b"nov v2"})
        self.assertIn(("UNKNOWN", "?"), got)
        self.assertEqual(code, 1)

    def test_ignored_content_image_is_skipped(self):
        poster = U + "2026/10/pool-map.png"
        got, code = self.run_check(page(U + "2026/09/Oct2026v2.jpg", U + "2026/10/Nov26v1.jpg", poster),
                                   d=data(ignored_images=[poster]))
        self.assertEqual(code, 0)

    def test_layout_change_is_reported(self):
        _, code = self.run_check(page(U + "2026/10/Nov26v1.jpg", main=False))
        self.assertEqual(code, 2)
        _, code = self.run_check(page())
        self.assertEqual(code, 2)

    def test_month_words_inside_other_words_are_not_months(self):
        self.assertIsNone(check.month_from_filename(U + "summary2026.png", 2026))
        self.assertIsNone(check.month_from_filename(U + "Team-Photo-2025.jpg", 2026))
        self.assertEqual(check.month_from_filename(U + "Sept_2026.jpg", 2026), "2026-09")

    def test_bot_check_page_that_persists_is_not_a_change(self):
        def fetch(url):
            raise check.NotAnImage(url)
        with tempfile.TemporaryDirectory() as out:
            lines, code = check.check(page(U + "2026/09/Oct2026v2.jpg", U + "2026/10/Nov26v1.jpg"),
                                      data(), fetch, pathlib.Path(out), 2026)
        self.assertEqual(code, 3)
        self.assertNotIn("CHANGED", " ".join(lines))

BOT_PAGE = b"<!DOCTYPE html><html><head><title>One moment, please...</title></head></html>"
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 20

class DownloadTest(unittest.TestCase):
    def setUp(self):
        self.sleeps = []
        self.orig = check.get, check.time.sleep
        check.time.sleep = self.sleeps.append

    def tearDown(self):
        check.get, check.time.sleep = self.orig

    def serve(self, *bodies):
        replies = list(bodies)
        check.get = lambda url: replies.pop(0)

    def test_is_image(self):
        self.assertTrue(check.is_image(PNG))
        self.assertTrue(check.is_image(b"\xff\xd8\xff\xe0rest"))
        self.assertTrue(check.is_image(b"RIFF\0\0\0\0WEBPVP8 "))
        self.assertFalse(check.is_image(BOT_PAGE))
        self.assertFalse(check.is_image(b""))

    def test_bot_check_page_is_retried(self):
        self.serve(BOT_PAGE, PNG)
        self.assertEqual(check.get_image(U + "x.png"), PNG)
        self.assertEqual(len(self.sleeps), 1)

    def test_bot_check_page_every_time_raises(self):
        self.serve(*[BOT_PAGE] * 4)
        with self.assertRaises(check.NotAnImage):
            check.get_image(U + "x.png", tries=4)
        self.assertEqual(len(self.sleeps), 3)

    def test_page_without_main_is_retried(self):
        self.serve(BOT_PAGE, page(U + "2026/10/Nov26v1.jpg").encode())
        self.assertIn("<main", check.get_page())
        self.assertEqual(len(self.sleeps), 1)

if __name__ == "__main__":
    unittest.main()
