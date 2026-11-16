"""Tests for the intentionally narrow Samsung Galaxy S product selection."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "samsung_galaxy_s_ingest.py"
SPEC = importlib.util.spec_from_file_location("samsung_galaxy_s_ingest", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GalaxySScopeTests(unittest.TestCase):
    def test_accepts_standard_generations(self):
        for slug in ("galaxy-s", "galaxy-s2", "galaxy-s10", "galaxy-s20", "galaxy-s26"):
            with self.subTest(slug=slug):
                result = MODULE.canonical_model_url(f"/ie/smartphones/{slug}/", "https://www.samsung.com/ie/smartphones/")
                self.assertIsNotNone(result)
                self.assertEqual(result[0], slug)

    def test_rejects_plus_ultra_fe_edge_and_skus(self):
        rejected = (
            "/ie/smartphones/galaxy-s26-plus/",
            "/ie/smartphones/galaxy-s26-ultra/",
            "/ie/smartphones/galaxy-s26-fe/",
            "/ie/smartphones/galaxy-s25-edge/",
            "/ie/smartphones/galaxy-s/galaxy-s26-256gb-sm-s942/",
        )
        for path in rejected:
            with self.subTest(path=path):
                self.assertIsNone(MODULE.canonical_model_url(path, "https://www.samsung.com/ie/smartphones/"))

    def test_rejects_non_samsung_hosts(self):
        self.assertIsNone(MODULE.canonical_model_url("https://example.com/ie/smartphones/galaxy-s26/", "https://www.samsung.com/ie/"))


class SamsungHtmlSpecificationExtractionTests(unittest.TestCase):
    def test_extracts_specification_sections_without_browser(self):
        html = """
        <section class="pdd32-product-spec">
          <div class="pdd32-product-spec__item">
            <h3 class="pdd32-product-spec__title">Processor</h3>
            <li class="pdd32-product-spec__content-item">
              <p class="pdd32-product-spec__content-item-title">CPU Name</p>
              <p class="pdd32-product-spec__content-item-desc">Samsung Exynos 2500</p>
            </li>
            <li class="pdd32-product-spec__content-item">
              <p class="pdd32-product-spec__content-item-title">CPU Speed</p>
              <p class="pdd32-product-spec__content-item-desc">3.3GHz</p>
            </li>
          </div>
        </section>
        """
        sections, normalized = MODULE.extract_spec_sections(html)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["heading"], "Processor")
        self.assertIn("CPU Name: Samsung Exynos 2500", sections[0]["source_text"])
        self.assertEqual(normalized["processor"]["cpu_name"]["value"], "Samsung Exynos 2500")
        self.assertEqual(normalized["processor"]["cpu_speed"]["value"], "3.3GHz")
        self.assertEqual(normalized["processor"]["cpu_speed"]["verification_status"], "source_transcribed")

    def test_returns_empty_when_page_has_no_specification_component(self):
        sections, normalized = MODULE.extract_spec_sections("<html><body>no spec panel</body></html>")
        self.assertEqual(sections, [])
        self.assertEqual(normalized, {})


if __name__ == "__main__":
    unittest.main()
