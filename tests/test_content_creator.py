import pytest

from content.generator import ContentGenerator
from database.models import ChannelType


@pytest.fixture
def sample_payload():
    return {
        "product_name": "ASUS Monitor 27\" 4K",
        "current_price": 299.99,
        "avg_price": 399.99,
        "discount": 25,
        "marketplace": "amazon",
        "description": "Monitor professionale 4K UHD",
        "key_features": {"risoluzione": "3840x2160", "pannello": "IPS"},
        "affiliate_link": "https://amazon.it/dp/B09XYZ?tag=dealscout-21",
        "image_url": "",
    }


@pytest.mark.asyncio
async def test_fallback_content(sample_payload):
    gen = ContentGenerator()
    result = await gen.generate_all(sample_payload)
    assert len(result) == len(list(ChannelType))
    for channel in ChannelType:
        assert channel in result
        assert len(result[channel]) > 0
    assert "25" in result[ChannelType.TELEGRAM]
    assert "ASUS" in result[ChannelType.TWITTER]
