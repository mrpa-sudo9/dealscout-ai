from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent
from database.repositories import PerformanceRepository


class PerformanceMonitor(BaseAgent):
    name = "PerformanceMonitor"

    async def execute(self, session: AsyncSession):
        perf_repo = PerformanceRepository(session)
        self.log.info("Running performance analysis...")

        stats = await perf_repo.get_stats(days=7)

        if not stats:
            self.log.info("No performance data for the last 7 days")
            return

        total_clicks = sum(s.clicks for s in stats)
        total_conversions = sum(s.conversions for s in stats)
        total_revenue = sum(float(s.revenue) for s in stats)
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0

        self.log.info("=== PERFORMANCE SUMMARY (7 days) ===")
        self.log.info(f"Clicks: {total_clicks}")
        self.log.info(f"Conversions: {total_conversions} ({conversion_rate:.2f}%)")
        self.log.info(f"Revenue: {total_revenue:.2f}€")

        await session.execute(text("""
            INSERT INTO performance_logs (id, channel, clicks, conversions, revenue, commission, logged_at)
            SELECT
                gen_random_uuid(),
                channel,
                SUM(clicks),
                SUM(conversions),
                SUM(revenue),
                SUM(commission),
                NOW()
            FROM performance_logs
            WHERE logged_at >= NOW() - INTERVAL '24 hours'
            GROUP BY channel
            ON CONFLICT DO NOTHING
        """))
        await session.commit()
