import asyncio
import argparse

from utils.logger import log
from database.session import init_db


def main():
    parser = argparse.ArgumentParser(prog="dealscout", description="DealScout AI - Autonomous Income Engine")
    parser.add_argument("--version", action="version", version="0.1.0")

    sub = parser.add_subparsers(dest="command", help="Comando disponibili")

    sub.add_parser("init", help="Inizializza il database")

    scan_parser = sub.add_parser("scan", help="Esegue scansione completa (hunt → affiliation → content → distribute)")
    scan_parser.add_argument("--hunt-only", action="store_true", help="Solo deal hunting")
    scan_parser.add_argument("--affiliate-only", action="store_true", help="Solo generazione link affiliati")
    scan_parser.add_argument("--content-only", action="store_true", help="Solo generazione contenuti")
    scan_parser.add_argument("--distribute-only", action="store_true", help="Solo distribuzione")

    sub.add_parser("monitor", help="Esegue analisi performance")

    args = parser.parse_args()

    if args.command == "init":
        asyncio.run(init_db())
        log.info("Database inizializzato")
    elif args.command == "scan":
        _run_scan(args)
    elif args.command == "monitor":
        _run_monitor()
    else:
        parser.print_help()


def _run_scan(args):
    from agents.deal_hunter import DealHunter
    from agents.affiliation_manager import AffiliationManager
    from agents.content_creator import ContentCreator
    from agents.distribution_manager import DistributionManager

    async def pipeline():
        await init_db()

        if not args.affiliate_only and not args.content_only and not args.distribute_only or args.hunt_only:
            log.info("=== FASE 1: Deal Hunting ===")
            await DealHunter().run()

        if not args.hunt_only and not args.content_only and not args.distribute_only or args.affiliate_only:
            log.info("=== FASE 2: Affiliazione ===")
            await AffiliationManager().run()

        if not args.hunt_only and not args.affiliate_only and not args.distribute_only or args.content_only:
            log.info("=== FASE 3: Creazione Contenuti ===")
            await ContentCreator().run()

        if not args.hunt_only and not args.affiliate_only and not args.content_only or args.distribute_only:
            log.info("=== FASE 4: Distribuzione ===")
            await DistributionManager().run()

        log.info("=== Pipeline completata ===")

    asyncio.run(pipeline())


def _run_monitor():
    from agents.monitor import PerformanceMonitor

    async def run():
        await init_db()
        await PerformanceMonitor().run()

    asyncio.run(run())


if __name__ == "__main__":
    main()
