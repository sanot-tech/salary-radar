"""Offline pipeline tests using bundled sample data (no network needed)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.salary_radar import bot, config, sources
from src.salary_radar.analyze import (
    classify_role,
    evaluate_vibe,
    is_vibe_friendly,
    resolve_tracks,
    summarize,
    track_enabled,
    vibe_subcategory,
)
from src.salary_radar.db import RadarDB
from src.salary_radar.report import render_html, write_all_summary_artifacts


class TestSources(unittest.TestCase):
    def test_all_sources_parse_samples(self):
        fetched = sources.scrape_all(offline=True, sample=True)
        self.assertIn("himalayas", fetched)
        self.assertIn("aidevboard", fetched)
        self.assertIn("nocodejobs", fetched)
        self.assertIn("workingnomads", fetched)
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

    def test_vibe_heuristic(self):
        self.assertTrue(is_vibe_friendly("Vibe Coder (AI App Builder)", "AI", ["ai"]))
        self.assertTrue(is_vibe_friendly("Prompt Engineer", "AI", ["llm"]))
        self.assertFalse(is_vibe_friendly("Senior Backend Engineer", "Software", ["go"]))


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
                vibe = is_vibe_friendly(job.title, job.category, job.tags)
                store.upsert(job, role, vibe)
        rows = store.all_jobs()
        self.assertGreater(len(rows), 0)
        summary = summarize(rows)
        self.assertEqual(summary["total"], len(rows))
        self.assertGreaterEqual(summary["vibe_total"], 0)
        write_all_summary_artifacts(summary, rows, [])
        self.assertTrue(os.path.exists(config.REPORT_HTML))
        self.assertTrue(os.path.exists(config.REPORT_JSON))
        store.close()


class TestVibeTracks(unittest.TestCase):
    """Vibe-coding guard + sub-track toggles for the super-universal."""

    def test_vibe_classification_guards_engineers(self):
        self.assertEqual(classify_role("Prompt Engineer for LLM Apps"), "AI / Vibe Dev")
        self.assertEqual(classify_role("Vibe Coder (Bubble Builder)"), "AI / Vibe Dev")
        self.assertEqual(classify_role("LLM Engineer"), "Engineering")
        self.assertEqual(classify_role("AI Agent Engineer"), "Engineering")
        self.assertTrue(is_vibe_friendly("Prompt Engineer (LLM)", "AI", ["ai"]))
        self.assertTrue(is_vibe_friendly("AI Agent Developer (Automation)", "", ["ai agent"]))
        self.assertFalse(is_vibe_friendly("AI Agent Engineer", "", ["ai"]))
        self.assertFalse(is_vibe_friendly("LLM Engineer", "", []))

    def test_vibe_subcategory(self):
        self.assertEqual(vibe_subcategory("Vibe Coder / AI App Builder"), "ai_product")
        self.assertEqual(vibe_subcategory("Prompt Engineer (LLM)"), "prompt_eng")
        self.assertEqual(vibe_subcategory("n8n Workflow Automation Builder"), "ai_agents")
        self.assertEqual(vibe_subcategory("Bubble Developer (No-Code Builder)"), "builders")
        self.assertEqual(vibe_subcategory("Generative AI Creative Designer"), "ai_creative")
        self.assertIsNone(vibe_subcategory("Backend Engineer", "Software", ["go"]))

    def test_resolve_tracks(self):
        only_agents = resolve_tracks("agents")
        self.assertTrue(only_agents["ai_agents"])
        self.assertFalse(only_agents["prompt_eng"])
        all_but_agents = resolve_tracks("!agents")
        self.assertFalse(all_but_agents["ai_agents"])
        self.assertTrue(all_but_agents["prompt_eng"])
        vibe_all = resolve_tracks("vibe")
        self.assertTrue(all(vibe_all.values()))
        env_style = resolve_tracks("agents,prompt")
        self.assertTrue(env_style["ai_agents"])
        self.assertTrue(env_style["prompt_eng"])
        self.assertFalse(env_style["builders"])
        self.assertEqual(resolve_tracks(None), dict(config.TRACKS))

    def test_track_toggle_kills_vibe_count(self):
        rows = [
            {"role": "AI / Vibe Dev", "vibe": 1, "company": "A", "source": "x",
             "tags": "", "title": "Prompt Engineer (LLM)", "category": "",
             "salary_min": None, "salary_max": None},
            {"role": "Engineering", "vibe": 0, "company": "B", "source": "x",
             "tags": "", "title": "Backend Engineer", "category": "",
             "salary_min": None, "salary_max": None},
        ]
        s_all = summarize(rows, resolve_tracks(None))
        self.assertEqual(s_all["vibe_total"], 1)
        s_off = summarize(rows, resolve_tracks("!prompt_eng"))
        self.assertEqual(s_off["vibe_total"], 0)
        self.assertFalse(s_off["track_counts"]["prompt_eng"]["enabled"])

    def test_evaluate_vibe_respects_track(self):
        self.assertTrue(track_enabled("AI / Vibe Dev", None))
        self.assertTrue(track_enabled("AI / Vibe Dev", resolve_tracks(None),
                                      title="Prompt Engineer (LLM)"))
        self.assertFalse(track_enabled("AI / Vibe Dev", resolve_tracks("!prompt_eng"),
                                       title="Prompt Engineer (LLM)"))
        self.assertFalse(evaluate_vibe(
            "Prompt Engineer", "", [], role="AI / Vibe Dev",
            tracks=resolve_tracks("!prompt_eng")))


class TestViralDashboard(unittest.TestCase):
    """The dashboard must ship the conversion-facing hooks, not just tables."""

    @staticmethod
    def _build():
        fetched = sources.scrape_all(offline=True, sample=True)
        store = RadarDB(config.DB_PATH if False else os.path.join(tempfile.mkdtemp(), "t.db"))
        for jobs in fetched.values():
            for job in jobs:
                role = classify_role(job.title)
                vibe = is_vibe_friendly(job.title, job.category, job.tags)
                store.upsert(job, role, vibe)
        rows = store.all_jobs()
        summary = summarize(rows)
        store.close()
        return summary, rows

    def test_dashboard_has_viral_hooks(self):
        summary, rows = self._build()
        page = render_html(summary, rows, [])
        for probe in [
            "Vibe Coder Salary Radar",
            "What are you worth?",
            "Check my price",
            "WORTH_DATA",
            "MY WORTH",
            "loot-elf",
            "5-week quest",
            "super-universal",
            "shareTG",
            "copyWorth",
            "vibe-total",
            "recalcVibe",
        ]:
            self.assertIn(probe, page, f"missing hook: {probe}")
        self.assertIn(str(summary["total"]), page)
        if summary.get("track_counts"):
            self.assertIn("Vibe sub-tracks", page)
            self.assertIn("toggleTrack", page)
            self.assertIn("recalcVibe", page)

    def test_dashboard_passes_real_role_medians_to_calc(self):
        summary, rows = self._build()
        page = render_html(summary, rows, [])
        self.assertIn("AI / Vibe Dev", page)
        self.assertIn("fallback_min", page)


class TestBotDigest(unittest.TestCase):
    def test_digest_prefers_vibe_with_salary(self):
        summary = {"total": 3, "vibe_total": 1}
        rows = [
            {"title": "Prompt Engineer", "company": "Cortexio", "role": "AI / Vibe Dev",
             "vibe": 1, "salary_min": 40000, "salary_max": 60000, "url": "https://x"},
            {"title": "Backend Engineer", "company": "R", "role": "Engineering",
             "vibe": 0, "salary_min": None, "salary_max": None, "url": "https://y"},
        ]
        text = bot.build_digest_text(summary, rows)
        self.assertIn("Vibe Radar", text)
        self.assertIn("Prompt Engineer", text)
        self.assertIn("$40,000–$60,000", text)
        self.assertNotIn("Backend Engineer", text)

    def test_digest_handles_empty(self):
        text = bot.build_digest_text({"total": 0, "vibe_total": 0}, [])
        self.assertIn("Vibe Radar", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)