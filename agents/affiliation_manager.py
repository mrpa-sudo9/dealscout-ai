from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent
from database.models import DealStatus
from database.repositories import DealRepository


class AffiliationManager(BaseAgent):
    name = "AffiliationManager"

    async def execute(self, session: AsyncSession):
        deal_repo = DealRepository(session)

        pending_deals = await deal_repo.get_pending()
        self.log.info(f"Processing {len(pending_deals)} pending deals")

        for deal in pending_deals:
            try:
                link = deal.product.marketplace_url
                await deal_repo.update_status(deal.id, DealStatus.AFFILIATE_READY, link)
                self.log.info(f"Referral link set for deal {deal.id}: {link[:80]}...")
            except Exception as e:
                self.log.error(f"Failed to process deal {deal.id}: {e}")
                await deal_repo.update_status(deal.id, DealStatus.FAILED)
