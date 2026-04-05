"""
Newsletter generator — renders categorized posts into a beautiful HTML email.
Uses Jinja2 templates for flexible design.
"""

import logging
from datetime import datetime
from typing import Dict, List
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.filter import ScoredPost, CATEGORIES
from src.config_loader import TEMPLATES_DIR

logger = logging.getLogger(__name__)


class NewsletterGenerator:
    """Generates beautiful HTML newsletter emails."""

    def __init__(self, config: dict):
        self.config = config
        self.newsletter_config = config.get("newsletter", {})
        self.top_pick_enabled = self.newsletter_config.get("top_pick_enabled", True)
        self.dark_mode = self.newsletter_config.get("dark_mode", True)

        # Setup Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=True,
        )

    def generate(self, categorized: Dict[str, List[ScoredPost]]) -> str:
        """Generate the complete HTML newsletter."""
        today = datetime.now().strftime("%B %d, %Y")

        # Find top pick
        top_pick = None
        if self.top_pick_enabled:
            top_pick = self._find_top_pick(categorized)

        # Prepare sections
        sections = []
        for cat_key, posts in categorized.items():
            cat_info = CATEGORIES.get(cat_key, {})
            sections.append({
                "emoji": cat_info.get("emoji", "📌"),
                "title": cat_info.get("title", cat_key.title()),
                "posts": [self._format_post(sp) for sp in posts],
            })

        # Count total items
        total_items = sum(len(s["posts"]) for s in sections)

        # Build color palette based on dark/light mode
        colors = self._get_color_palette()

        # Try to load Jinja template, fallback to inline
        try:
            template = self.env.get_template("newsletter.html")
            html = template.render(
                date=today,
                sections=sections,
                top_pick=self._format_post(top_pick) if top_pick else None,
                total_items=total_items,
                c=colors,
            )
        except Exception as e:
            logger.warning(f"Template rendering failed ({e}), using inline template")
            html = self._render_inline(today, sections, top_pick, total_items)

        logger.info(f"📰 Newsletter generated: {total_items} items, {len(sections)} sections")
        return html

    def _get_color_palette(self) -> dict:
        """Return color palette dict for template rendering."""
        if self.dark_mode:
            return {
                "bg": "#0f0f13",
                "card_bg": "#1a1a24",
                "card_border": "#2a2a3a",
                "text_primary": "#e8e8ed",
                "text_secondary": "#9898a8",
                "accent": "#6c5ce7",
                "accent_light": "#a29bfe",
                "link_color": "#74b9ff",
                "divider": "#2a2a3a",
                "top_pick_bg": "#1e1638",
                "top_pick_border": "#6c5ce7",
                "tag_bg": "#2d2d44",
                "footer_bg": "#12121a",
            }
        else:
            return {
                "bg": "#f5f5fa",
                "card_bg": "#ffffff",
                "card_border": "#e8e8f0",
                "text_primary": "#1a1a2e",
                "text_secondary": "#6b6b80",
                "accent": "#6c5ce7",
                "accent_light": "#a29bfe",
                "link_color": "#0984e3",
                "divider": "#e8e8f0",
                "top_pick_bg": "#f0ecff",
                "top_pick_border": "#6c5ce7",
                "tag_bg": "#eeeef5",
                "footer_bg": "#eaeaf0",
            }

    def _find_top_pick(self, categorized: Dict[str, List[ScoredPost]]) -> ScoredPost:
        """Find the top-scored post across all categories."""
        all_posts = []
        for posts in categorized.values():
            all_posts.extend(posts)

        if not all_posts:
            return None

        return max(all_posts, key=lambda sp: sp.score)

    def _format_post(self, sp: ScoredPost) -> dict:
        """Format a scored post for template rendering."""
        return {
            "summary": sp.summary,
            "author": sp.post.author,
            "handle": sp.post.author_handle,
            "url": sp.post.url,
            "timestamp": sp.post.timestamp.strftime("%I:%M %p"),
            "likes": _format_number(sp.post.likes),
            "retweets": _format_number(sp.post.retweets),
            "score": round(sp.score),
            "media_urls": sp.post.media_urls,
            "is_top_pick": sp.is_top_pick,
        }

    def _render_inline(self, date: str, sections: list, top_pick, total_items: int) -> str:
        """Fallback inline HTML template if Jinja template is unavailable."""
        # This generates the same design as the Jinja template
        from src.template_builder import build_newsletter_html
        return build_newsletter_html(date, sections, top_pick, total_items, self.dark_mode)


def _format_number(n: int) -> str:
    """Format number for display (e.g., 1500 → 1.5K)."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)
