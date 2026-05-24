from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_session_factory
from utils.logger import log


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self):
        self.log = log

    async def run(self):
        self.log.info(f"[{self.name}] Starting execution")
        try:
            factory = get_session_factory()
            async with factory() as session:
                await self.execute(session)
                await session.commit()
            self.log.info(f"[{self.name}] Execution completed successfully")
        except Exception as e:
            self.log.error(f"[{self.name}] Execution failed: {e}", exc_info=True)
            raise

    @abstractmethod
    async def execute(self, session: AsyncSession):
        ...
