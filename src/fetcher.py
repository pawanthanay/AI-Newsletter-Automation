"""
Post fetcher — retrieves posts from X (Twitter) accounts.
Supports:
  1. Official X API v2 (via Tweepy) — preferred
  2. Nitter scraping fallback — when API keys unavailable
  3. RSS feed fallback
"""

import logging
import time
import re
import hashlib
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class Post:
    """Represents a single social media post."""
    id: str
    author: str
    author_handle: str
    text: str
    timestamp: datetime
    url: str
    media_urls: List[str] = field(default_factory=list)
    likes: int = 0
    retweets: int = 0
    is_retweet: bool = False
    is_reply: bool = False
    has_commentary: bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @property
    def content_hash(self) -> str:
        """Generate hash for deduplication."""
        normalized = re.sub(r'\s+', ' ', self.text.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()


class PostFetcher:
    """Fetches posts from X accounts using available methods."""

    def __init__(self, config: dict):
        self.config = config
        self.api_config = config.get("x_api", {})
        self.scraping_config = config.get("scraping", {})
        self.rate_limit_delay = self.scraping_config.get("rate_limit_delay", 2)
        self.max_posts = self.scraping_config.get("max_posts_per_account", 50)
        self.nitter_instances = self.scraping_config.get("nitter_instances", [])
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

    def fetch_all(self, accounts: List[str]) -> List[Post]:
        """Fetch posts from all accounts."""
        all_posts = []
        method = self._determine_method()

        logger.info(f"📡 Fetching posts using: {method}")
        logger.info(f"📋 Accounts to fetch: {len(accounts)}")

        for i, account in enumerate(accounts):
            logger.info(f"  [{i+1}/{len(accounts)}] Fetching @{account}...")
            posts = []
            try:
                if method == "api":
                    try:
                        posts = self._fetch_via_api(account)
                    except Exception as e:
                        logger.warning(f"    ⚠️ API fetch failed ({e}). Falling back to web scraping...")
                        posts = self._fetch_via_nitter(account)
                elif method == "nitter":
                    posts = self._fetch_via_nitter(account)
                else:
                    posts = self._fetch_via_rss(account)

                if posts:
                    all_posts.extend(posts)
                    logger.info(f"    ✅ Got {len(posts)} posts from @{account}")
                else:
                    logger.warning(f"    ⚠️ No posts found for @{account}")

            except Exception as e:
                logger.error(f"    ❌ Error fetching @{account}: {e}")

            # Rate limiting
            if i < len(accounts) - 1:
                time.sleep(self.rate_limit_delay)

        logger.info(f"📊 Total posts fetched: {len(all_posts)}")
        return all_posts

    def _determine_method(self) -> str:
        """Determine the best fetching method available."""
        bearer = self.api_config.get("bearer_token", "")
        if bearer and bearer.strip():
            try:
                import tweepy
                return "api"
            except ImportError:
                logger.warning("Tweepy not installed, falling back to scraping")

        if self.scraping_config.get("use_nitter", True) and self.nitter_instances:
            return "nitter"

        return "rss"

    # ------------------------------------------------------------------
    # Method 1: Official X API v2
    # ------------------------------------------------------------------
    def _fetch_via_api(self, account: str) -> List[Post]:
        """Fetch tweets using the official X API v2 via Tweepy."""
        import tweepy

        client = tweepy.Client(
            bearer_token=self.api_config["bearer_token"],
            wait_on_rate_limit=True,
        )

        # Get user ID
        user = client.get_user(username=account)
        if not user or not user.data:
            logger.warning(f"User @{account} not found via API")
            return []

        user_id = user.data.id
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        tweets = client.get_users_tweets(
            id=user_id,
            max_results=min(self.max_posts, 100),
            start_time=since,
            tweet_fields=["created_at", "public_metrics", "referenced_tweets", "attachments"],
            expansions=["attachments.media_keys"],
            media_fields=["url", "preview_image_url"],
        )

        posts = []
        if tweets and tweets.data:
            media_map = {}
            if tweets.includes and "media" in tweets.includes:
                for m in tweets.includes["media"]:
                    media_map[m.media_key] = m.url or m.preview_image_url or ""

            for tweet in tweets.data:
                is_rt = False
                is_reply = False
                has_commentary = False

                if tweet.referenced_tweets:
                    for ref in tweet.referenced_tweets:
                        if ref.type == "retweeted":
                            is_rt = True
                        elif ref.type == "replied_to":
                            is_reply = True
                        elif ref.type == "quoted":
                            has_commentary = True

                media_urls = []
                if tweet.attachments and "media_keys" in tweet.attachments:
                    for mk in tweet.attachments["media_keys"]:
                        if mk in media_map and media_map[mk]:
                            media_urls.append(media_map[mk])

                metrics = tweet.public_metrics or {}
                post = Post(
                    id=str(tweet.id),
                    author=account,
                    author_handle=f"@{account}",
                    text=tweet.text,
                    timestamp=tweet.created_at,
                    url=f"https://x.com/{account}/status/{tweet.id}",
                    media_urls=media_urls,
                    likes=metrics.get("like_count", 0),
                    retweets=metrics.get("retweet_count", 0),
                    is_retweet=is_rt,
                    is_reply=is_reply,
                    has_commentary=has_commentary,
                )
                posts.append(post)

        return posts

    # ------------------------------------------------------------------
    # Method 2: Nitter scraping
    # ------------------------------------------------------------------
    def _fetch_via_nitter(self, account: str) -> List[Post]:
        """Scrape posts from Nitter instances (privacy-friendly X frontend)."""
        posts = []

        for instance in self.nitter_instances:
            try:
                url = f"{instance}/{account}"
                resp = self.session.get(url, timeout=15)

                if resp.status_code != 200:
                    logger.debug(f"Nitter instance {instance} returned {resp.status_code}")
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                timeline = soup.find_all("div", class_="timeline-item")

                if not timeline:
                    # Try alternate class names
                    timeline = soup.find_all("div", class_="tweet-body")

                if not timeline:
                    logger.debug(f"No timeline items found on {instance}")
                    continue

                cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

                for item in timeline[:self.max_posts]:
                    try:
                        post = self._parse_nitter_item(item, account, instance, cutoff)
                        if post:
                            posts.append(post)
                    except Exception as e:
                        logger.debug(f"Error parsing nitter item: {e}")
                        continue

                if posts:
                    logger.debug(f"Successfully scraped {len(posts)} posts from {instance}")
                    break

            except requests.RequestException as e:
                logger.debug(f"Nitter instance {instance} failed: {e}")
                continue

        # If nitter fails, try RSS fallback
        if not posts:
            logger.info(f"  ⚠️  Nitter unavailable for @{account}, trying RSS...")
            posts = self._fetch_via_rss(account)

        return posts

    def _parse_nitter_item(self, item, account: str, instance: str, cutoff: datetime) -> Optional[Post]:
        """Parse a single Nitter timeline item into a Post."""
        # Get tweet content
        content_el = item.find("div", class_="tweet-content") or item.find("div", class_="content")
        if not content_el:
            return None

        text = content_el.get_text(strip=True)
        if not text:
            return None

        # Get timestamp
        time_el = item.find("span", class_="tweet-date") or item.find("time")
        timestamp = datetime.now(timezone.utc)
        if time_el:
            time_link = time_el.find("a")
            if time_link and time_link.get("title"):
                try:
                    timestamp = datetime.strptime(time_link["title"], "%b %d, %Y · %I:%M %p %Z")
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                except (ValueError, KeyError):
                    pass

        # Skip old posts
        if timestamp < cutoff:
            return None

        # Check if retweet or reply
        is_rt = bool(item.find("div", class_="retweet-header"))
        is_reply = bool(item.find("div", class_="replying-to"))

        # Get tweet link
        link_el = item.find("a", class_="tweet-link") or (time_el.find("a") if time_el else None)
        tweet_path = link_el.get("href", "") if link_el else ""
        tweet_url = f"https://x.com{tweet_path}" if tweet_path else f"https://x.com/{account}"

        # Get media
        media_urls = []
        for img in item.find_all("img", class_="still-image") or []:
            src = img.get("src", "")
            if src:
                media_urls.append(f"{instance}{src}" if src.startswith("/") else src)

        # Get stats
        stat_el = item.find("div", class_="tweet-stat")
        likes = 0
        retweets = 0
        if stat_el:
            for span in stat_el.find_all("span"):
                txt = span.get_text(strip=True)
                if "like" in txt.lower():
                    likes = _parse_stat_number(txt)
                elif "retweet" in txt.lower() or "retoot" in txt.lower():
                    retweets = _parse_stat_number(txt)

        # Generate unique ID
        post_id = hashlib.md5(f"{account}:{text[:100]}:{timestamp.isoformat()}".encode()).hexdigest()[:16]

        return Post(
            id=post_id,
            author=account,
            author_handle=f"@{account}",
            text=text,
            timestamp=timestamp,
            url=tweet_url,
            media_urls=media_urls,
            likes=likes,
            retweets=retweets,
            is_retweet=is_rt,
            is_reply=is_reply,
            has_commentary=bool(is_rt and len(text) > 50),
        )

    # ------------------------------------------------------------------
    # Method 3: RSS feed fallback
    # ------------------------------------------------------------------
    def _fetch_via_rss(self, account: str) -> List[Post]:
        """Fetch posts via third-party RSS bridge services."""
        rss_sources = [f"{instance}/{account}/rss" for instance in self.nitter_instances]
        rss_sources.extend([
            f"https://rsshub.app/twitter/user/{account}",
            f"https://twiiit.com/{account}/rss"
        ])

        for rss_url in rss_sources:
            try:
                resp = self.session.get(rss_url, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.content, "lxml-xml")
                items = soup.find_all("item")

                if not items:
                    continue

                posts = []
                cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

                for item in items[:self.max_posts]:
                    try:
                        post = self._parse_rss_item(item, account, cutoff, rss_url)
                        if post:
                            posts.append(post)
                    except Exception as e:
                        logger.debug(f"Error parsing RSS item: {e}")

                if posts:
                    return posts

            except requests.RequestException as e:
                logger.debug(f"RSS source {rss_url} failed: {e}")
                continue

        return []

    def _parse_rss_item(self, item, account: str, cutoff: datetime, rss_url: str = "") -> Optional[Post]:
        """Parse a single RSS item into a Post."""
        from urllib.parse import urlsplit
        base_url = "{0.scheme}://{0.netloc}".format(urlsplit(rss_url)) if rss_url else "https://nitter.net"
        
        title = item.find("title")
        desc = item.find("description")
        link = item.find("link")
        pub_date = item.find("pubDate")

        text = ""
        media_urls = []
        if desc:
            # Parse HTML description
            desc_soup = BeautifulSoup(desc.get_text(), "html.parser")
            
            # Extract images (convert relative Nitter paths to absolute)
            for img in desc_soup.find_all("img"):
                src = img.get("src")
                if src:
                    if src.startswith("/"):
                        src = base_url + src
                    media_urls.append(src)
            
            text = desc_soup.get_text(strip=True)
        elif title:
            text = title.get_text(strip=True)

        if not text:
            return None

        # Parse timestamp
        timestamp = datetime.now(timezone.utc)
        if pub_date:
            try:
                from email.utils import parsedate_to_datetime
                timestamp = parsedate_to_datetime(pub_date.get_text())
            except (ValueError, TypeError):
                pass

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        if timestamp < cutoff:
            return None

        url = link.get_text(strip=True) if link else f"https://x.com/{account}"

        post_id = hashlib.md5(f"{account}:{text[:100]}".encode()).hexdigest()[:16]

        # Clean Nitter proxy URLs to original Twitter CDN (better for email templates)
        clean_media = []
        for m in media_urls:
            if "/pic/media%2F" in m:
                # Convert nitter.net/pic/media%2FABC.jpg -> pbs.twimg.com/media/ABC.jpg
                img_id = m.split("%2F")[-1].replace("%3F", "?")
                clean_media.append(f"https://pbs.twimg.com/media/{img_id}")
            elif "/pic/" in m:
                # Generic fallback for other nitter patterns
                clean_media.append(m)
            else:
                clean_media.append(m)

        return Post(
            id=post_id,
            author=account,
            author_handle=f"@{account}",
            text=text,
            timestamp=timestamp,
            url=url,
            media_urls=clean_media,
        )


def _parse_stat_number(text: str) -> int:
    """Parse engagement stat numbers like '1.2K', '500'."""
    text = re.sub(r'[^\d.kKmM]', '', text)
    if not text:
        return 0
    multiplier = 1
    if text[-1].lower() == 'k':
        multiplier = 1000
        text = text[:-1]
    elif text[-1].lower() == 'm':
        multiplier = 1000000
        text = text[:-1]
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return 0
