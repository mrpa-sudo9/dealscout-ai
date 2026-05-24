import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, JSON, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class DealStatus(str, enum.Enum):
    PENDING = "pending"
    AFFILIATE_READY = "affiliate_ready"
    CONTENT_READY = "content_ready"
    PUBLISHED = "published"
    FAILED = "failed"
    EXPIRED = "expired"


class ChannelType(str, enum.Enum):
    TWITTER = "twitter"
    TELEGRAM = "telegram"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    PINTEREST = "pinterest"
    WORDPRESS = "wordpress"
    REDDIT = "reddit"
    NEWSLETTER = "newsletter"


class Marketplace(str, enum.Enum):
    AMAZON = "amazon"
    EBAY = "ebay"
    ETSY = "etsy"
    ALIEXPRESS = "aliexpress"
    DECATHLON = "decathlon"
    ZALANDO = "zalando"
    MEDIAMARKT = "mediamarkt"
    FNAC = "fnac"
    VINTED = "vinted"
    MANOMANO = "manomano"
    WALMART = "walmart"
    RAKUTEN = "rakuten"


def utcnow():
    return datetime.now(UTC)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(256))
    marketplace: Mapped[Marketplace] = mapped_column(Enum(Marketplace), nullable=False)
    marketplace_url: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    key_features: Mapped[dict | None] = mapped_column(JSON)
    category: Mapped[str | None] = mapped_column(String(256))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="product", cascade="all, delete-orphan")
    price_records: Mapped[list["PriceRecord"]] = relationship("PriceRecord", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_products_marketplace_sku", "marketplace", "sku", unique=True),
    )


class PriceRecord(Base):
    __tablename__ = "price_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    source: Mapped[str | None] = mapped_column(String(128))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    product: Mapped[Product] = relationship("Product", back_populates="price_records")

    __table_args__ = (
        Index("ix_price_records_product_recorded", "product_id", "recorded_at"),
    )


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    avg_market_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False)
    affiliate_link: Mapped[str | None] = mapped_column(Text)
    status: Mapped[DealStatus] = mapped_column(Enum(DealStatus), default=DealStatus.PENDING)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    product: Mapped[Product] = relationship("Product", back_populates="deals")
    contents: Mapped[list["Content"]] = relationship("Content", back_populates="deal", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_deals_status_discount", "status", "discount_percent"),
        Index("ix_deals_product_status", "product_id", "status"),
    )


class Content(Base):
    __tablename__ = "contents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    deal_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[ChannelType] = mapped_column(Enum(ChannelType), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[dict | None] = mapped_column(JSON)
    seo_title: Mapped[str | None] = mapped_column(String(512))
    seo_description: Mapped[str | None] = mapped_column(String(512))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_post_id: Mapped[str | None] = mapped_column(String(256))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    deal: Mapped[Deal] = relationship("Deal", back_populates="contents")


class AffiliateConfig(Base):
    __tablename__ = "affiliate_configs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    marketplace: Mapped[Marketplace] = mapped_column(Enum(Marketplace), unique=True, nullable=False)
    network_name: Mapped[str] = mapped_column(String(128), nullable=False)
    api_key_encrypted: Mapped[str | None] = mapped_column(String(512))
    publisher_id: Mapped[str | None] = mapped_column(String(256))
    tag_id: Mapped[str | None] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    rules: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PerformanceLog(Base):
    __tablename__ = "performance_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    deal_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("deals.id", ondelete="SET NULL"), nullable=True)
    channel: Mapped[ChannelType] = mapped_column(Enum(ChannelType), nullable=False)
    clicks: Mapped[int] = mapped_column(default=0)
    conversions: Mapped[int] = mapped_column(default=0)
    revenue: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_perf_log_channel_date", "channel", "logged_at"),
    )
