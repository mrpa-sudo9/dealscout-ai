from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from utils.logger import log


class Analytics:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_channel_performance(self, days: int = 7) -> list[dict]:
        rows = await self.session.execute(text("""
            SELECT
                channel,
                COUNT(*) as posts,
                SUM(clicks) as total_clicks,
                SUM(conversions) as total_conversions,
                SUM(revenue) as total_revenue,
                CASE WHEN SUM(clicks) > 0
                    THEN ROUND(SUM(conversions)::numeric / SUM(clicks) * 100, 2)
                    ELSE 0
                END as conversion_rate
            FROM performance_logs
            WHERE logged_at >= NOW() - :days::interval
            GROUP BY channel
            ORDER BY total_revenue DESC
        """), {"days": f"{days} days"})
        return [dict(row._mapping) for row in rows]

    async def get_best_deals(self, limit: int = 10) -> list[dict]:
        rows = await self.session.execute(text("""
            SELECT
                p.name,
                d.discount_percent,
                d.current_price,
                d.avg_market_price,
                SUM(pl.clicks) as clicks,
                SUM(pl.conversions) as conversions,
                SUM(pl.revenue) as revenue
            FROM deals d
            JOIN products p ON p.id = d.product_id
            LEFT JOIN performance_logs pl ON pl.deal_id = d.id
            GROUP BY p.name, d.discount_percent, d.current_price, d.avg_market_price
            ORDER BY revenue DESC
            LIMIT :limit
        """), {"limit": limit})
        return [dict(row._mapping) for row in rows]

    async def log_event(self, deal_id: str, channel: str, clicks: int = 0, conversions: int = 0, revenue: float = 0.0):
        await self.session.execute(text("""
            INSERT INTO performance_logs (id, deal_id, channel, clicks, conversions, revenue, logged_at)
            VALUES (gen_random_uuid(), :deal_id, :channel, :clicks, :conversions, :revenue, NOW())
        """), {
            "deal_id": deal_id,
            "channel": channel,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
        })
        await self.session.commit()
        log.info(f"Analytics logged: {channel} - {clicks} clicks, {conversions} conv, {revenue}€")
