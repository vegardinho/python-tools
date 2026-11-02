import pytest

pytest.importorskip("pyshorteners")
pytest.importorskip("mechanicalsoup")
pytest.importorskip("bs4")

from python_tools.scraper import SiteChangedScraper


def test_scraper_validates_urls(tmp_path):
    scraper = SiteChangedScraper(
        "test",
        str(tmp_path / "secrets.yaml"),
        str(tmp_path / "elements.json"),
        str(tmp_path / "history.txt"),
        str(tmp_path / "searches.yaml"),
        "to@example.test",
    )

    assert scraper._is_valid_url("https://example.test/path")
    assert not scraper._is_valid_url("not a url")
