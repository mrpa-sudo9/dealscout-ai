import pytest

from agents.affiliation_manager import AffiliationManager


@pytest.mark.parametrize("url,marketplace,tag,expected", [
    ("https://www.amazon.it/dp/B09XYZ", "amazon", "tag-21",
     "https://www.amazon.it/dp/B09XYZ?tag=tag-21"),
    ("https://www.ebay.it/itm/123", "ebay", "camp123",
     "https://www.ebay.it/itm/123?mkcid=1&mkrid=707-53477-19255-0&siteid=23&campid=camp123"),
])
def test_link_generation(url, marketplace, tag, expected):
    manager = AffiliationManager()
    result = manager._generate_link(url, marketplace, tag)
    assert result == expected
