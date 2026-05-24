
import tweepy

from core.config import settings
from database.models import Content
from distribution.base import BasePublisher


class TwitterPublisher(BasePublisher):
    name = "twitter"

    async def publish(self, content: Content) -> str | None:
        if not all([settings.twitter_api_key, settings.twitter_api_secret,
                     settings.twitter_access_token, settings.twitter_access_secret]):
            self.log.warning("Twitter credentials not configured")
            return None

        client = tweepy.Client(
            consumer_key=settings.twitter_api_key,
            consumer_secret=settings.twitter_api_secret,
            access_token=settings.twitter_access_token,
            access_token_secret=settings.twitter_access_secret,
        )

        text = content.body
        if "---" in text or "|" in text:
            tweets = [t.strip() for t in text.replace("---", "|").split("|") if t.strip()]
        else:
            tweets = [text[:280]]

        last_id = None
        for tweet_text in tweets:
            tweet_text = tweet_text.strip()
            if not tweet_text:
                continue
            resp = client.create_tweet(text=tweet_text[:280], in_reply_to_tweet_id=last_id)
            if resp.data:
                last_id = resp.data["id"]

        return str(last_id) if last_id else None
