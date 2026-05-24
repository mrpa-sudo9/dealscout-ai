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

                if not config:
                    self.log.warning(f"No affiliate config for {marketplace}, adding default tag")
                    affiliate_link = self._fallback_link(deal.product.marketplace_url, marketplace)
                else:
                    affiliate_link = self._generate_link(
                        deal.product.marketplace_url,
                        marketplace,
                        config.tag_id or settings.amazon_associates_tag,
                    )

                await deal_repo.update_status(deal.id, DealStatus.AFFILIATE_READY, affiliate_link)
                self.log.info(f"Affiliate link generated for deal {deal.id}: {affiliate_link[:80]}...")

            except Exception as e:
                self.log.error(f"Failed to process deal {deal.id}: {e}")
                await deal_repo.update_status(deal.id, DealStatus.FAILED)

    def _generate_link(self, original_url: str, marketplace: str, tag: str) -> str:
        parsed = urlparse(original_url)
        params = {}

        if marketplace == "amazon":
            params = {"tag": tag}
        elif marketplace == "ebay":
            params = {"mkcid": "1", "mkrid": "707-53477-19255-0", "siteid": "23", "campid": tag}
        elif marketplace == "aliexpress":
            params = {"aff_platform": "true", "aff_trace_key": tag}
        elif marketplace == "walmart":
            params = {"veh": "aff", "wmlspartner": tag}

        if params:
            query = urlencode(params)
            new_parsed = parsed._replace(query=query)
            return urlunparse(new_parsed)
        return original_url

    def _fallback_link(self, original_url: str, marketplace: str) -> str:
        return self._generate_link(original_url, marketplace, settings.amazon_associates_tag)
