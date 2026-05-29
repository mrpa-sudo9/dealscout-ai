from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import (
    AffiliateConfig,
    Content,
    Deal,
    DealStatus,
    Marketplace,
    PerformanceLog,
    PriceRecord,
    Product,
)


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_marketplace_sku(self, marketplace: Marketplace, sku: str) -> Product | None:
        stmt = select(Product).where(and_(Product.marketplace == marketplace, Product.sku == sku))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Product:
        product = Product(**kwargs)
        self.session.add(product)
        await self.session.flush()
        return product

    async def get_or_create(self, marketplace: Marketplace, sku: str, defaults: dict) -> Product:
        existing = await self.get_by_marketplace_sku(marketplace, sku)
        if existing:
            for key, value in defaults.items():
                setattr(existing, key, value)
            await self.session.flush()
            return existing
        return await self.create(marketplace=marketplace, sku=sku, **defaults)


class PriceRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, product_id: UUID, price: Decimal, currency: str = "EUR", source: str | None = None) -> PriceRecord:
        record = PriceRecord(product_id=product_id, price=price, currency=currency, source=source)
        self.session.add(record)
        await self.session.flush()
        return record

    async def count_recent(self, product_id: UUID, days: int = 30) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = select(func.count(PriceRecord.id)).where(
            and_(PriceRecord.product_id == product_id, PriceRecord.recorded_at >= cutoff)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_avg_price_30d(self, product_id: UUID) -> Decimal | None:
        cutoff = datetime.now(UTC) - timedelta(days=30)
        stmt = select(func.avg(PriceRecord.price)).where(
            and_(PriceRecord.product_id == product_id, PriceRecord.recorded_at >= cutoff)
        )
        result = await self.session.execute(stmt)
        val = result.scalar()
        return Decimal(str(val)) if val is not None else None

    async def get_latest_price(self, product_id: UUID) -> PriceRecord | None:
        stmt = (
            select(PriceRecord)
            .where(PriceRecord.product_id == product_id)
            .order_by(PriceRecord.recorded_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class DealRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Deal:
        deal = Deal(**kwargs)
        self.session.add(deal)
        await self.session.flush()
        return deal

    async def get_pending(self, limit: int = 50) -> list[Deal]:
        stmt = (
            select(Deal)
            .where(Deal.status == DealStatus.PENDING)
            .options(joinedload(Deal.product))
            .order_by(Deal.discount_percent.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_affiliate_ready(self, limit: int = 50) -> list[Deal]:
        stmt = (
            select(Deal)
            .where(Deal.status == DealStatus.AFFILIATE_READY)
            .options(joinedload(Deal.product))
            .order_by(Deal.discount_percent.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_recently_published(self, days: int = 30) -> list[Deal]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(Deal)
            .where(Deal.published_at >= cutoff)
            .options(joinedload(Deal.product))
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def update_status(self, deal_id: UUID, status: DealStatus, affiliate_link: str | None = None):
        stmt = select(Deal).where(Deal.id == deal_id)
        result = await self.session.execute(stmt)
        deal = result.scalar_one_or_none()
        if deal:
            deal.status = status
            if affiliate_link:
                deal.affiliate_link = affiliate_link
            await self.session.flush()

    async def exists_recent(self, product_id: UUID, days: int = 30) -> bool:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = select(Deal).where(
            and_(Deal.product_id == product_id, Deal.created_at >= cutoff, Deal.status != DealStatus.FAILED)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


class ContentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Content:
        content = Content(**kwargs)
        self.session.add(content)
        await self.session.flush()
        return content

    async def get_unpublished(self, channel: str | None = None, limit: int = 10) -> list[Content]:
        conditions = [Content.is_published.is_(False)]
        if channel:
            conditions.append(Content.channel == channel)
        stmt = (
            select(Content)
            .where(and_(*conditions))
            .options(joinedload(Content.deal))
            .order_by(Deal.discount_percent.desc().nullslast())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def mark_published(self, content_id: UUID, external_post_id: str | None = None):
        stmt = select(Content).where(Content.id == content_id)
        result = await self.session.execute(stmt)
        content = result.scalar_one_or_none()
        if content:
            content.is_published = True
            content.published_at = datetime.now(UTC)
            if external_post_id:
                content.external_post_id = external_post_id
            await self.session.flush()


class AffiliateConfigRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_marketplace(self, marketplace: Marketplace) -> AffiliateConfig | None:
        stmt = select(AffiliateConfig).where(
            and_(AffiliateConfig.marketplace == marketplace, AffiliateConfig.is_active)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class PerformanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(self, **kwargs) -> PerformanceLog:
        obj = PerformanceLog(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_stats(self, days: int = 7) -> list[PerformanceLog]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = select(PerformanceLog).where(PerformanceLog.logged_at >= cutoff).order_by(PerformanceLog.logged_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
