from prefect import flow, task
from prefect.tasks import task_input_hash

from agents.deal_hunter import DealHunter
from agents.affiliation_manager import AffiliationManager
from agents.content_creator import ContentCreator
from agents.distribution_manager import DistributionManager
from utils.logger import log


@task(retries=2, retry_delay_seconds=60, cache_key_fn=task_input_hash)
async def run_deal_hunter():
    hunter = DealHunter()
    await hunter.run()
    log.info("Deal Hunter completed")


@task(retries=2, retry_delay_seconds=30)
async def run_affiliation_manager():
    manager = AffiliationManager()
    await manager.run()
    log.info("Affiliation Manager completed")


@task(retries=2, retry_delay_seconds=30)
async def run_content_creator():
    creator = ContentCreator()
    await creator.run()
    log.info("Content Creator completed")


@task(retries=3, retry_delay_seconds=60)
async def run_distribution():
    distributor = DistributionManager()
    await distributor.run()
    log.info("Distribution Manager completed")


@flow(name="deal_scan", log_prints=True)
async def deal_scan_flow():
    log.info("=== Starting Deal Scan Pipeline ===")
    await run_deal_hunter()
    await run_affiliation_manager()
    await run_content_creator()
    await run_distribution()
    log.info("=== Deal Scan Pipeline Complete ===")


if __name__ == "__main__":
    import asyncio
    asyncio.run(deal_scan_flow())
