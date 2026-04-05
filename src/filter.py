"""
Content filter — filters, deduplicates, and categorizes AI-related posts.
"""

import re
import json
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

from src.fetcher import Post
from src.config_loader import HISTORY_DIR

logger = logging.getLogger(__name__)


# Category definitions
CATEGORIES = {
    "breaking": {
        "emoji": "✦",
        "title": "Strategic Announcements",
        "keywords": [
            "breaking", "just announced", "launches", "released", "introducing",
            "unveils", "debuts", "new model", "rollout", "shipping",
            "available now", "just dropped", "announcement", "officially",
        ],
    },
    "research": {
        "emoji": "✦",
        "title": "Scientific Advancements",
        "keywords": [
            "paper", "arxiv", "research", "study", "findings", "published",
            "peer-reviewed", "benchmark", "sota", "state-of-the-art",
            "experiment", "hypothesis", "dataset", "ablation", "preprint",
        ],
    },
    "tools": {
        "emoji": "✦",
        "title": "Technological Implementations",
        "keywords": [
            "tool", "library", "framework", "sdk", "api", "plugin",
            "extension", "open source", "github", "pip install", "npm",
            "release", "v2", "v3", "update", "upgrade", "changelog",
        ],
    },
    "tips": {
        "emoji": "✦",
        "title": "Operational Best Practices",
        "keywords": [
            "tip", "trick", "how to", "tutorial", "guide", "learn",
            "best practice", "pro tip", "here's how", "thread",
            "step by step", "walkthrough", "explained", "cheat sheet",
        ],
    },
    "industry": {
        "emoji": "✦",
        "title": "Economic & Capital Insights",
        "keywords": [
            "funding", "acquisition", "partnership", "hire", "market",
            "regulation", "policy", "enterprise", "business", "startup",
            "valuation", "revenue", "investment", "strategy", "layoff",
        ],
    },
}


@dataclass
class ScoredPost:
    """A post with relevance score and category assignment."""
    post: Post
    score: float
    category: str
    summary: str = ""
    is_top_pick: bool = False


class ContentFilter:
    """Filters, scores, deduplicates, and categorizes posts."""

    def __init__(self, config: dict):
        self.config = config
        self.keywords = [kw.lower() for kw in config.get("keywords", [])]
        self.exclude_keywords = [kw.lower() for kw in config.get("exclude_keywords", [])]
        self.history_days = config.get("newsletter", {}).get("history_days", 7)
        self.max_per_section = config.get("newsletter", {}).get("max_items_per_section", 5)

    def process(self, posts: List[Post]) -> Dict[str, List[ScoredPost]]:
        """Full processing pipeline: filter → deduplicate → score → categorize."""
        logger.info(f"🔍 Processing {len(posts)} raw posts...")

        # Step 1: Remove replies and plain retweets
        posts = self._filter_post_types(posts)
        logger.info(f"  After type filter: {len(posts)}")

        # Step 2: Filter by AI keywords
        posts = self._filter_by_keywords(posts)
        logger.info(f"  After keyword filter: {len(posts)}")

        # Step 3: Remove excluded content
        posts = self._remove_excluded(posts)
        logger.info(f"  After exclusion filter: {len(posts)}")

        # Step 4: Deduplicate
        posts = self._deduplicate(posts)
        logger.info(f"  After deduplication: {len(posts)}")

        # Step 5: Score and categorize
        scored = self._score_and_categorize(posts)

        # Step 6: Organize by category
        categorized = self._organize_by_category(scored)

        # Step 7: Save to history for future dedup
        self._save_to_history(posts)

        total_items = sum(len(v) for v in categorized.values())
        logger.info(f"✅ Final newsletter items: {total_items} across {len(categorized)} categories")

        return categorized

    def _filter_post_types(self, posts: List[Post]) -> List[Post]:
        """Remove plain retweets and replies (keep quoted tweets with commentary)."""
        filtered = []
        for post in posts:
            # Skip plain retweets without commentary
            if post.is_retweet and not post.has_commentary:
                continue
            # Skip replies unless they are substantial
            if post.is_reply and len(post.text) < 100:
                continue
            filtered.append(post)
        return filtered

    def _filter_by_keywords(self, posts: List[Post]) -> List[Post]:
        """Keep only posts matching AI keywords."""
        filtered = []
        for post in posts:
            text_lower = post.text.lower()
            if any(kw in text_lower for kw in self.keywords):
                filtered.append(post)
        return filtered

    def _remove_excluded(self, posts: List[Post]) -> List[Post]:
        """Remove posts matching exclusion keywords."""
        filtered = []
        for post in posts:
            text_lower = post.text.lower()
            if not any(kw in text_lower for kw in self.exclude_keywords):
                filtered.append(post)
        return filtered

    def _deduplicate(self, posts: List[Post]) -> List[Post]:
        """Remove duplicate posts based on content similarity and history."""
        seen_hashes = set()
        unique_posts = []

        # Load historical hashes
        historical_hashes = self._load_history_hashes()
        seen_hashes.update(historical_hashes)

        for post in posts:
            content_hash = post.content_hash

            # Also create a shortened hash for near-duplicate detection
            words = post.text.lower().split()[:15]
            short_hash = hashlib.md5(" ".join(words).encode()).hexdigest()

            if content_hash not in seen_hashes and short_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                seen_hashes.add(short_hash)
                unique_posts.append(post)

        removed = len(posts) - len(unique_posts)
        if removed > 0:
            logger.info(f"  🗑️  Removed {removed} duplicate posts")

        return unique_posts

    def _score_and_categorize(self, posts: List[Post]) -> List[ScoredPost]:
        """Score each post by relevance and assign to a category."""
        scored_posts = []

        for post in posts:
            score = self._calculate_score(post)
            category = self._assign_category(post)
            summary = self._generate_summary(post)

            scored_posts.append(ScoredPost(
                post=post,
                score=score,
                category=category,
                summary=summary,
            ))

        # Sort by score descending
        scored_posts.sort(key=lambda sp: sp.score, reverse=True)

        # Mark top pick
        if scored_posts:
            scored_posts[0].is_top_pick = True

        return scored_posts

    def _calculate_score(self, post: Post) -> float:
        """Calculate relevance score for a post (0–100)."""
        score = 0.0
        text_lower = post.text.lower()

        # Keyword density score (0–30)
        keyword_matches = sum(1 for kw in self.keywords if kw in text_lower)
        score += min(keyword_matches * 5, 30)

        # Engagement score (0–25)
        engagement = post.likes + (post.retweets * 2)
        if engagement > 1000:
            score += 25
        elif engagement > 500:
            score += 20
        elif engagement > 100:
            score += 15
        elif engagement > 50:
            score += 10
        elif engagement > 10:
            score += 5

        # Content quality indicators (0–20)
        if any(domain in text_lower for domain in ["arxiv.org", "github.com", "huggingface.co"]):
            score += 10
        if re.search(r'https?://\S+', post.text):
            score += 5
        if len(post.text) > 100:
            score += 5

        # Freshness score (0–15)
        hours_old = (datetime.now(timezone.utc) - post.timestamp).total_seconds() / 3600
        if hours_old < 4:
            score += 15
        elif hours_old < 8:
            score += 12
        elif hours_old < 16:
            score += 8
        else:
            score += 4

        # Author credibility bonus (0–10)
        high_credibility = [
            "openai", "anthropic", "google", "deepmind", "meta",
            "huggingface", "langchain", "ylecun", "karpathy", "andrewng",
        ]
        if any(auth in post.author.lower() for auth in high_credibility):
            score += 10

        return min(score, 100)

    def _assign_category(self, post: Post) -> str:
        """Assign a post to the best-matching category."""
        text_lower = post.text.lower()
        best_category = "industry"  # default
        best_match_count = 0

        for cat_key, cat_info in CATEGORIES.items():
            match_count = sum(1 for kw in cat_info["keywords"] if kw in text_lower)
            if match_count > best_match_count:
                best_match_count = match_count
                best_category = cat_key

        return best_category

    def _generate_summary(self, post: Post) -> str:
        """Generate a clean summary of a post while retaining formatting."""
        text = post.text

        # 1. Remove Nitter's common Author Name (@handle) prefix if present
        # Pattern: "Some Name (@handle) " at the start
        text = re.sub(r'^[^\(]+\(@\w+\)\s*', '', text)
        
        # 2. Hard-remove all raw URLs from the text body to keep it "simple"
        # User has a "Read Post" button, so raw URLs in text are distracting clutter
        text = re.sub(r'https?://\S+', '', text)
        
        # 3. Remove @mentions at the start if any remain
        text = re.sub(r'^(@\w+\s*)+', '', text)
        
        # 4. Clean excessive blank lines but preserve natural spacing
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 5. Handle common messy characters
        text = text.replace('…', '...')
        
        text = text.strip()

        # If summary is empty after cleaning, fallback to original or first 150 chars
        if not text:
            return post.text[:150].strip()

        return text

    def _organize_by_category(self, scored_posts: List[ScoredPost]) -> Dict[str, List[ScoredPost]]:
        """Organize scored posts into category buckets."""
        categorized = {}

        for sp in scored_posts:
            if sp.category not in categorized:
                categorized[sp.category] = []
            if len(categorized[sp.category]) < self.max_per_section:
                categorized[sp.category].append(sp)

        # Ensure category order
        ordered = {}
        for cat_key in CATEGORIES:
            if cat_key in categorized and categorized[cat_key]:
                ordered[cat_key] = categorized[cat_key]

        return ordered

    def _load_history_hashes(self) -> set:
        """Load content hashes from history files."""
        hashes = set()
        history_dir = HISTORY_DIR

        if not history_dir.exists():
            return hashes

        for f in history_dir.glob("*.json"):
            try:
                with open(f, "r") as fh:
                    data = json.load(fh)
                    hashes.update(data.get("hashes", []))
            except (json.JSONDecodeError, IOError):
                continue

        return hashes

    def _save_to_history(self, posts: List[Post]):
        """Save content hashes to history for future deduplication."""
        today = datetime.now().strftime("%Y-%m-%d")
        history_file = HISTORY_DIR / f"{today}.json"

        existing_hashes = []
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    data = json.load(f)
                    existing_hashes = data.get("hashes", [])
            except (json.JSONDecodeError, IOError):
                pass

        new_hashes = [post.content_hash for post in posts]
        all_hashes = list(set(existing_hashes + new_hashes))

        with open(history_file, "w") as f:
            json.dump({
                "date": today,
                "count": len(all_hashes),
                "hashes": all_hashes,
            }, f, indent=2)

        # Clean old history
        self._clean_old_history()

    def _clean_old_history(self):
        """Remove history files older than configured days."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=self.history_days)

        for f in HISTORY_DIR.glob("*.json"):
            try:
                date_str = f.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    f.unlink()
                    logger.debug(f"Cleaned old history file: {f.name}")
            except (ValueError, OSError):
                continue
