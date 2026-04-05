#!/usr/bin/env python3
"""
AI Newsletter Bot — Main Entry Point

A fully automated pipeline that fetches AI-related posts from X (Twitter),
curates them into a beautiful newsletter, and sends it to your Gmail inbox.

Usage:
    python main.py                  # Run once immediately
    python main.py --schedule       # Start daily scheduler
    python main.py --preview        # Generate and save preview HTML
    python main.py --test-email     # Send a test email
    python main.py --demo           # Run with sample data (no API needed)
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config_loader import load_config, get_accounts, LOGS_DIR
from src.fetcher import PostFetcher
from src.filter import ContentFilter
from src.newsletter import NewsletterGenerator
from src.emailer import EmailSender
from src.scheduler import Scheduler


def setup_logging(verbose: bool = False):
    """Configure logging with file and console output."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_file = LOGS_DIR / f"newsletter_{datetime.now().strftime('%Y-%m-%d')}.log"

    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-5s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def run_pipeline(config: dict, save_preview: bool = False) -> bool:
    """
    Execute the full newsletter pipeline:
    1. Fetch posts from X accounts
    2. Filter and categorize AI content
    3. Generate HTML newsletter
    4. Send email
    """
    logger = logging.getLogger(__name__)

    logger.info("🚀 Starting AI Newsletter Pipeline")
    logger.info(f"📅 Date: {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
    logger.info("")

    # Step 1: Fetch posts
    logger.info("=" * 50)
    logger.info("STEP 1: Fetching posts from X accounts")
    logger.info("=" * 50)
    accounts = get_accounts(config)
    fetcher = PostFetcher(config)
    posts = fetcher.fetch_all(accounts)

    if not posts:
        logger.warning("⚠️  No posts fetched. Check your configuration and internet connection.")
        logger.info("💡 Try running with --demo flag to test with sample data.")
        return False

    # Step 2: Filter and categorize
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 2: Filtering and categorizing content")
    logger.info("=" * 50)
    content_filter = ContentFilter(config)
    categorized = content_filter.process(posts)

    if not categorized:
        logger.warning("⚠️  No AI-related content found in fetched posts.")
        return False

    # Step 3: Generate newsletter
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 3: Generating newsletter")
    logger.info("=" * 50)
    generator = NewsletterGenerator(config)
    html = generator.generate(categorized)

    # Save preview if requested
    if save_preview:
        preview_path = PROJECT_ROOT / "preview.html"
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"📄 Preview saved to: {preview_path}")

    # Step 4: Send email
    logger.info("")
    logger.info("=" * 50)
    logger.info("STEP 4: Sending newsletter email")
    logger.info("=" * 50)
    sender = EmailSender(config)
    success = sender.send(html)

    if success:
        logger.info("")
        logger.info("🎉 Newsletter pipeline completed successfully!")
    else:
        logger.warning("⚠️  Newsletter generated but email sending failed.")
        logger.info("   The newsletter HTML has been saved as preview.html")
        # Save preview on failure
        preview_path = PROJECT_ROOT / "preview.html"
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(html)

    return success


def run_demo(config: dict):
    """Run with sample data to demonstrate the newsletter without API access."""
    logger = logging.getLogger(__name__)
    logger.info("🎮 Running in DEMO mode with sample data\n")

    from src.demo_data import get_demo_posts
    from src.filter import ContentFilter
    from src.newsletter import NewsletterGenerator
    from src.config_loader import HISTORY_DIR

    # Clear today's history so demo data is not deduplicated on repeat runs
    today = datetime.now().strftime("%Y-%m-%d")
    history_file = HISTORY_DIR / f"{today}.json"
    if history_file.exists():
        history_file.unlink()
        logger.info("🗑️  Cleared today's history for fresh demo")

    # Get sample posts
    posts = get_demo_posts()
    logger.info(f"📝 Loaded {len(posts)} sample posts")

    # Filter and categorize
    content_filter = ContentFilter(config)
    categorized = content_filter.process(posts)

    # Generate newsletter
    generator = NewsletterGenerator(config)
    html = generator.generate(categorized)

    # Save preview
    preview_path = PROJECT_ROOT / "preview.html"
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"\n✅ Demo newsletter saved to: {preview_path}")
    logger.info(f"   Open it in your browser to see the result!")

    # Optionally send email
    sender = EmailSender(config)
    if sender._validate():
        logger.info("\n📧 Email configuration detected. Sending demo newsletter...")
        sender.send(html)
    else:
        logger.info("\n💡 Configure email in config.yaml to send the newsletter to your inbox.")


def main():
    parser = argparse.ArgumentParser(
        description="🤖 AI Newsletter Bot — Daily curated AI updates from X (Twitter)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                  Run once immediately
  python main.py --schedule       Start daily scheduler
  python main.py --preview        Generate and save preview HTML
  python main.py --test-email     Send a test email
  python main.py --demo           Run with sample data (no API needed)
        """,
    )

    parser.add_argument("--schedule", action="store_true",
                        help="Start the daily scheduler")
    parser.add_argument("--preview", action="store_true",
                        help="Generate newsletter and save as preview.html")
    parser.add_argument("--test-email", action="store_true",
                        help="Send a test email to verify configuration")
    parser.add_argument("--demo", action="store_true",
                        help="Run with sample data (no API/scraping needed)")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to config.yaml (default: ./config.yaml)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose/debug logging")

    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("")
    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║     🤖 AI Newsletter Bot                    ║")
    logger.info("║     Daily curated AI updates from X          ║")
    logger.info("╚══════════════════════════════════════════════╝")
    logger.info("")

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Route to appropriate command
    if args.test_email:
        sender = EmailSender(config)
        success = sender.send_test()
        sys.exit(0 if success else 1)

    elif args.demo:
        run_demo(config)

    elif args.schedule:
        scheduler = Scheduler(config)
        scheduler.start(lambda: run_pipeline(config, save_preview=True))

    elif args.preview:
        run_pipeline(config, save_preview=True)

    else:
        # Default: run once
        success = run_pipeline(config, save_preview=True)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
