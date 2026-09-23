"""Offline pipeline tests using bundled sample data (no network needed)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.salary_radar import bot, config, sources
from src.salary_radar.analyze import (
    classify_role,
    evaluate_no_code,
    is_no_code_friendly,
    resolve_tracks,
    summarize,
    track_enabled,
)
from src.salary_radar.db import RadarDB
from src.salary_radar.report import render_html, write_all_summary_artifacts


class TestSources(unittest.TestCase):
    def test_all_sources_parse_samples(self):
        fetched = sources.scrape_all(offline=True, sample=True)
        for name, jobs in fetched.items():
            self.assertGreater(len(jobs), 0, f"{name} returned nothing")
            for job in jobs:
                self.assertTrue(job.title)
                self.assertTrue(job.company)
                self.assertTrue(job.source)

    def test_salary_parsing(self):
        lo, hi = sources._parse_salary("$42,000 - $52,000")
        self.assertEqual((lo, hi), (42000, 52000))
        self.assertEqual(sources._parse_salary(None), (None, None))


class TestAnalyze(unittest.TestCase):
    def test_classify_role(self):
        self.assertEqual(classify_role("Manual QA Engineer"), "QA / Testing")
        self.assertEqual(classify_role("Data Engineer"), "Data")
        self.assertEqual(classify_role("Sales Development Representative"), "Sales / SDR")
        self.assertEqual(classify_role("Backend Developer"), "Engineering")

    def test_no_code_heuristic(self):
        self.assertTrue(is_no_code_friendly("Manual QA Analyst", "QA", ["manual"]))
        self.assertFalse(is_no_code_friendly("Senior Backend Engineer", "Software", ["go"]))


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="radar_test_")
        config.DB_PATH = os.path.join(self.tmp, "radar.db")
        config.OUTPUT_DIR = os.path.join(self.tmp, "out")
        config.REPORT_HTML = os.path.join(config.OUTPUT_DIR, "index.html")
        config.REPORT_JSON = os.path.join(config.OUTPUT_DIR, "report.json")
        config.REPORT_CSV = os.path.join(config.OUTPUT_DIR, "jobs.csv")
        config.HISTORY_JSON = os.path.join(config.OUTPUT_DIR, "history.json")

    def test_full_pipeline_offline(self):
        fetched = sources.scrape_all(offline=True, sample=True)
        store = RadarDB(config.DB_PATH)
        for jobs in fetched.values():
            for job in jobs:
                role = classify_role(job.title)
                no_code = is_no_code_friendly(job.title, job.category, job.tags)
                store.upsert(job, role, no_code)
        rows = store.all_jobs()
        self.assertGreater(len(rows), 0)
        summary = summarize(rows)
        self.assertEqual(summary["total"], len(rows))
        self.assertGreaterEqual(summary["no_code_total"], 0)
        write_all_summary_artifacts(summary, rows, [])
        self.assertTrue(os.path.exists(config.REPORT_HTML))
        self.assertTrue(os.path.exists(config.REPORT_JSON))
        store.close()


class TestVibeTracks(unittest.TestCase):
    """Vibe-coding guard + priority tracks with manual toggles."""

    def test_vibe_classification_guards_engineers(self):
        self.assertEqual(classify_role("Prompt Engineer for LLM Apps"), "AI / Vibe Dev")
        self.assertEqual(classify_role("LLM Engineer"), "Engineering")
        self.assertEqual(classify_role("AI Agent Engineer"), "Engineering")
        self.assertEqual(classify_role("AI Horse Engineer"), "Engineering")
        self.assertTrue(is_no_code_friendly("Prompt Engineer (LLM)", "AI", ["ai"]))
        self.assertFalse(is_no_code_friendly("AI Agent Engineer", "", ["ai"]))
        self.assertFalse(is_no_code_friendly("LLM Engineer", "", []))

    def test_resolve_tracks(self):
        only_vibe = resolve_tracks("vibe")
        self.assertTrue(only_vibe["vibe_ai"])
        self.assertFalse(only_vibe["support"])
        all_but_support = resolve_tracks("!support")
        self.assertTrue(all_but_support["vibe_ai"])
        self.assertFalse(all_but_support["support"])
        env_style = resolve_tracks("vibe,qa")
        self.assertTrue(env_style["vibe_ai"])
        self.assertTrue(env_style["qa"])
        self.assertFalse(env_style["data"])
        self.assertEqual(resolve_tracks(None), dict(config.TRACKS))

    def test_track_toggle_kills_nocode_count(self):
        rows = [
            {"role": "Support", "no_code": 1, "company": "A", "source": "x",
             "tags": "", "title": "t", "salary_min": None, "salary_max": None},
            {"role": "Engineering", "no_code": 0, "company": "B", "source": "x",
             "tags": "", "title": "t", "salary_min": None, "salary_max": None},
        ]
        s_all = summarize(rows, resolve_tracks(None))
        self.assertEqual(s_all["no_code_total"], 1)
        s_off = summarize(rows, resolve_tracks("!support"))
        self.assertEqual(s_off["no_code_total"], 0)
        self.assertFalse(s_off["track_counts"]["support"]["enabled"])

    def test_evaluate_no_code_respects_track(self):
        self.assertTrue(track_enabled("Support", None))
        self.assertTrue(track_enabled("Support", resolve_tracks(None)))
        self.assertFalse(track_enabled("Support", resolve_tracks("!support")))
        # even a strong no-code title must be excluded when its track is off
        self.assertFalse(evaluate_no_code("Manual QA Analyst", "", [],
                                          role="QA / Testing",
                                          tracks=resolve_tracks("!qa")))


class TestViralDashboard(unittest.TestCase):
    """The dashboard must ship the conversion-facing hooks, not just tables."""

    @staticmethod
    def _build():
        fetched = sources.scrape_all(offline=True, sample=True)
        store = RadarDB(config.DB_PATH if False else os.path.join(tempfile.mkdtemp(), "t.db"))
        for jobs in fetched.values():
            for job in jobs:
                role = classify_role(job.title)
                no_code = is_no_code_friendly(job.title, job.category, job.tags)
                store.upsert(job, role, no_code)
        rows = store.all_jobs()
        summary = summarize(rows)
        store.close()
        return summary, rows

    def test_dashboard_has_viral_hooks(self):
        summary, rows = self._build()
        page = render_html(summary, rows, [])
        for probe in [
            "What are you worth?",
            "Check my price",
            "WORTH_DATA",
            "MY WORTH",
            "loot-elf",
            "5-week quest",
            "other path",
            "shareTG",
            "copyWorth",
        ]:
            self.assertIn(probe, page, f"missing hook: {probe}")
        self.assertIn(str(summary["total"]), page)
        # priority-track section with manual toggles must render
        if summary.get("track_counts"):
            self.assertIn("Priority tracks", page)
            self.assertIn("toggleTrack", page)
            self.assertIn("recalcNoCode", page)

    def test_dashboard_passes_real_role_medians_to_calc(self):
        summary, rows = self._build()
        page = render_html(summary, rows, [])
        # the client-side widget is fed by the real scraped medians via JSON
        self.assertIn("QA / Testing", page)
        self.assertIn("fallback_min", page)


class TestBotDigest(unittest.TestCase):
    def test_digest_prefers_no_code_with_salary(self):
        summary = {"total": 3, "no_code_total": 1}
        rows = [
            {"title": "Manual QA Engineer", "company": "Testify", "role": "QA / Testing",
             "no_code": 1, "salary_min": 40000, "salary_max": 60000, "url": "https://x"},
            {"title": "Backend Engineer", "company": "R", "role": "Engineering",
             "no_code": 0, "salary_min": None, "salary_max": None, "url": "https://y"},
        ]
        text = bot.build_digest_text(summary, rows)
        self.assertIn("Loot-Elf", text)
        self.assertIn("Manual QA Engineer", text)
        self.assertIn("$40,000–$60,000", text)
        self.assertNotIn("Backend Engineer", text)

    def test_digest_handles_empty(self):
        text = bot.build_digest_text({"total": 0, "no_code_total": 0}, [])
        self.assertIn("Loot-Elf", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)