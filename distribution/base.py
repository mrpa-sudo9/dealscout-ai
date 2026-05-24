from abc import ABC, abstractmethod

from database.models import Content
from utils.logger import log


class BasePublisher(ABC):
    name: str = "base"

    def __init__(self):
        self.log = log

    @abstractmethod
    async def publish(self, content: Content) -> str | None:
        ...
