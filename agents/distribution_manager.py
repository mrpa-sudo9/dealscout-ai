from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import BaseAgent
from database.models import ChannelType
from database.repositories import ContentRepository
from distribution.base import BasePublisher
from distribution.facebook import FacebookPublisher
from distribution.instagram import InstagramPublisher
from distribution.newsletter import NewsletterPublisher
from distribution.pinterest import PinterestPublisher
from distribution.reddit import RedditPublisher
from distribution.telegram import TelegramPublisher
from distribution.twitter import TwitterPublisher
from distribution.wordpress import WordPressPublisher


class DistributionManager(BaseAgent):
    name = "DistributionManager"

    PUBLISHER_MAP: dict[ChannelType, type[BasePublisher]] = {
        ChannelType.TWITTER: TwitterPublisher,
        ChannelType.TELEGRAM: TelegramPublisher,
        ChannelType.FACEBOOK: FacebookPublisher,
        ChannelType.PINTEREST: PinterestPublisher,
        ChannelType.INSTAGRAM: InstagramPublisher,
        ChannelType.WORDPRESS: WordPressPublisher,
        ChannelType.REDDIT: RedditPublisher,
        ChannelType.NEWSLETTER: NewsletterPublisher,
    }

    async def execute(self, session: AsyncSession):
        content_repo = ContentRepository(session)

        for channel_type, publisher_class in self.PUBLISHER_MAP.items():
            try:
                unpublished = await content_repo.get_unpublished(channel=channel_type.value, limit=30)
                if not unpublished:
                    self.log.info(f"No unpublished content for {channel_type.value}")
                    continue

                publisher = publisher_class()

                for content in unpublished:
                    try:
                        external_id = await publisher.publish(content)
                        await content_repo.mark_published(content.id, external_id)
                        self.log.info(f"Published to {channel_type.value}: {content.id} (post_id={external_id})")
                    except Exception as e:
                        self.log.error(f"Failed to publish to {channel_type.value}: {e}")

            except Exception as e:
                self.log.error(f"Publisher setup failed for {channel_type.value}: {e}")
