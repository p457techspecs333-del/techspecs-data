"""Tests for the generic slim Samsung HTML scraper."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "samsung_slim_ingest.py"
SPEC = importlib.util.spec_from_file_location("samsung_slim_ingest", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SlimSamsungHtmlTests(unittest.TestCase):
    def test_extracts_multiple_spec_sections_and_label_value_rows(self):
        html = """
        <section class="pdd32-product-spec">
          <div class="pdd32-product-spec__item">
            <h3 class="pdd32-product-spec__title">Display</h3>
            <li class="pdd32-product-spec__content-item">
              <p class="pdd32-product-spec__content-item-title">Size (Main_Display)</p>
              <p class="pdd32-product-spec__content-item-desc">11.0 inch</p>
            </li>
          </div>
          <div class="pdd32-product-spec__item">
            <h3 class="pdd32-product-spec__title">Battery</h3>
            <li class="pdd32-product-spec__content-item">
              <p class="pdd32-product-spec__content-item-title">Capacity (mAh, Typical)</p>
              <p class="pdd32-product-spec__content-item-desc">8000</p>
            </li>
          </div>
        </section>
        """
        sections, normalized = MODULE.extract_spec_sections(html)
        self.assertEqual([x["heading"] for x in sections], ["Display", "Battery"])
        self.assertEqual(normalized["display"]["size_main_display"]["value"], "11.0 inch")
        self.assertEqual(normalized["battery"]["capacity_mah_typical"]["value"], "8000")
        self.assertEqual(normalized["battery"]["capacity_mah_typical"]["unit"], "mAh, Typical")

    def test_identifies_product_jsonld_and_canonical_url(self):
        html = '''
        <title>Galaxy Example | Samsung IE</title>
        <link rel="canonical" href="https://www.samsung.com/ie/tablets/galaxy-example-sm-x000/">
        <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Product","name":"Galaxy Example","sku":"SM-X000"}
        </script>
        '''
        result = MODULE.page_product_identity(html)
        self.assertTrue(result["product_jsonld_found"])
        self.assertEqual(result["name"], "Galaxy Example")
        self.assertEqual(result["sku"], "SM-X000")
        self.assertEqual(result["canonical_url"], "https://www.samsung.com/ie/tablets/galaxy-example-sm-x000/")

    def test_rejects_non_samsung_and_non_irish_urls(self):
        self.assertFalse(MODULE.allowed_url("https://example.com/ie/tablets/x-sm-x000/"))
        self.assertFalse(MODULE.allowed_url("https://www.samsung.com/uk/tablets/x-sm-x000/"))
        self.assertTrue(MODULE.allowed_url("https://www.samsung.com/ie/tablets/x-sm-x000/"))

    def test_returns_no_specs_when_panel_is_absent(self):
        sections, normalized = MODULE.extract_spec_sections("<html><body>no specs</body></html>")
        self.assertEqual(sections, [])
        self.assertEqual(normalized, {})


if __name__ == "__main__":
    unittest.main()
