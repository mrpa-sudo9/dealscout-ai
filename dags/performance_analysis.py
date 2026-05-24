from prefect import flow, task

from agents.monitor import PerformanceMonitor


@task(retries=1)
async def run_monitor():
    monitor = PerformanceMonitor()
    await monitor.run()


@flow(name="performance_analysis", log_prints=True, cron="0 6 * * *")
async def performance_flow():
    await run_monitor()


if __name__ == "__main__":
    import asyncio
    asyncio.run(performance_flow())
