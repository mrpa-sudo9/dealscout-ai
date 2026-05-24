from urllib.parse import urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent
from core.config import settings
from database.models import DealStatus
from database.repositories import AffiliateConfigRepository, DealRepository


class AffiliationManager(BaseAgent):
    name = "AffiliationManager"

    async def execute(self, session: AsyncSession):
        deal_repo = DealRepository(session)
        config_repo = AffiliateConfigRepository(session)

        pending_deals = await deal_repo.get_pending()
        self.log.info(f"Processing {len(pending_deals)} pending deals")

        for deal in pending_deals:
            try:
                marketplace = deal.product.marketplace
                config = await config_repo.get_by_marketplace(marketplace)
                tag = config.tag_id if config else self._default_tag(marketplace)
                affiliate_link = self._generate_link(
                    deal.product.marketplace_url,
                    marketplace,
                    tag,
                )
                await deal_repo.update_status(deal.id, DealStatus.AFFILIATE_READY, affiliate_link)
                self.log.info(f"Affiliate link set for deal {deal.id}: {affiliate_link[:80]}...")
            except Exception as e:
                self.log.error(f"Failed to process deal {deal.id}: {e}")
                await deal_repo.update_status(deal.id, DealStatus.FAILED)

    def _default_tag(self, marketplace: str) -> str | None:
        ml = marketplace.lower()
        if ml == "amazon":
            return settings.tradedoubler_amazon_tag or settings.amazon_associates_tag
        if ml == "ebay":
            return settings.ebay_partner_network_id
        return None

    def _generate_link(self, original_url: str, marketplace: str, tag: str | None) -> str:
        if not tag:
            return original_url
        parsed = urlparse(original_url)
        params = {}
        ml = marketplace.lower()
        if ml == "amazon":
            params = {"tag": tag}
        elif ml == "ebay":
            params = {"mkcid": "1", "mkrid": "707-53477-19255-0", "siteid": "23", "campid": tag}
        elif ml == "aliexpress":
            params = {"aff_platform": "true", "aff_trace_key": tag}
        elif ml == "walmart":
            params = {"veh": "aff", "wmlspartner": tag}
        if params:
            query = urlencode(params)
            new_parsed = parsed._replace(query=query)
            return urlunparse(new_parsed)
        return original_url
