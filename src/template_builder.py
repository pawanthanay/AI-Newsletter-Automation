"""
Template builder — constructs the newsletter HTML inline.
Also used as fallback when Jinja2 template file is unavailable.
"""


def build_newsletter_html(date: str, sections: list, top_pick: dict,
                          total_items: int, dark_mode: bool = True) -> str:
    """Build complete newsletter HTML."""

    # Color scheme
    if dark_mode:
        bg = "#0f0f13"
        card_bg = "#1a1a24"
        card_border = "#2a2a3a"
        text_primary = "#e8e8ed"
        text_secondary = "#9898a8"
        accent = "#6c5ce7"
        accent_light = "#a29bfe"
        gradient_start = "#6c5ce7"
        gradient_end = "#00cec9"
        link_color = "#74b9ff"
        divider = "#2a2a3a"
        top_pick_bg = "#1e1638"
        top_pick_border = "#6c5ce7"
        tag_bg = "#2d2d44"
        footer_bg = "#12121a"
    else:
        bg = "#f5f5fa"
        card_bg = "#ffffff"
        card_border = "#e8e8f0"
        text_primary = "#1a1a2e"
        text_secondary = "#6b6b80"
        accent = "#6c5ce7"
        accent_light = "#a29bfe"
        gradient_start = "#6c5ce7"
        gradient_end = "#00cec9"
        link_color = "#0984e3"
        divider = "#e8e8f0"
        top_pick_bg = "#f0ecff"
        top_pick_border = "#6c5ce7"
        tag_bg = "#eeeef5"
        footer_bg = "#eaeaf0"

    # Build sections HTML
    sections_html = ""
    for section in sections:
        posts_html = ""
        for post in section["posts"]:
            media_html = ""
            if post.get("media_urls"):
                media_html = f'''
                <div style="margin-top: 12px;">
                    <img src="{post["media_urls"][0]}" alt="Post media"
                         style="max-width: 100%; border-radius: 8px; height: auto;" />
                </div>'''

            posts_html += f'''
            <div style="padding: 16px 20px; border-bottom: 1px solid {divider};">
                <div style="display: flex; align-items: flex-start;">
                    <div style="flex: 1;">
                        <p style="margin: 0 0 8px 0; color: {text_primary}; font-size: 15px; line-height: 1.5;">
                            {post["summary"]}
                        </p>
                        <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                            <span style="color: {accent_light}; font-size: 13px; font-weight: 600;">
                                {post["handle"]}
                            </span>
                            <span style="color: {text_secondary}; font-size: 12px;">
                                {post["timestamp"]}
                            </span>
                            <span style="color: {text_secondary}; font-size: 12px;">
                                ❤️ {post["likes"]} &nbsp; 🔄 {post["retweets"]}
                            </span>
                            <a href="{post["url"]}" target="_blank"
                               style="color: {link_color}; text-decoration: none; font-size: 13px; font-weight: 500;">
                                Read more →
                            </a>
                        </div>{media_html}
                    </div>
                </div>
            </div>'''

        sections_html += f'''
        <div style="margin-bottom: 28px; background: {card_bg}; border: 1px solid {card_border};
                    border-radius: 12px; overflow: hidden;">
            <div style="padding: 18px 20px; border-bottom: 1px solid {divider};
                        background: linear-gradient(135deg, {card_bg}, {tag_bg});">
                <h2 style="margin: 0; font-size: 18px; color: {text_primary}; font-weight: 700; letter-spacing: -0.3px;">
                    {section["emoji"]} {section["title"]}
                </h2>
            </div>
            {posts_html}
        </div>'''

    # Top pick HTML
    top_pick_html = ""
    if top_pick:
        top_pick_html = f'''
        <div style="margin-bottom: 28px; background: {top_pick_bg}; border: 2px solid {top_pick_border};
                    border-radius: 12px; overflow: hidden; position: relative;">
            <div style="padding: 20px 24px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                    <span style="background: linear-gradient(135deg, {gradient_start}, {gradient_end});
                                color: white; padding: 4px 14px; border-radius: 20px; font-size: 12px;
                                font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
                        ⭐ Top Pick of the Day
                    </span>
                </div>
                <p style="margin: 0 0 12px 0; color: {text_primary}; font-size: 16px; line-height: 1.6; font-weight: 500;">
                    {top_pick["summary"]}
                </p>
                <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                    <span style="color: {accent_light}; font-size: 14px; font-weight: 600;">
                        {top_pick["handle"]}
                    </span>
                    <span style="color: {text_secondary}; font-size: 13px;">
                        ❤️ {top_pick["likes"]} &nbsp; 🔄 {top_pick["retweets"]}
                    </span>
                    <a href="{top_pick["url"]}" target="_blank"
                       style="background: linear-gradient(135deg, {gradient_start}, {gradient_end});
                              color: white; text-decoration: none; padding: 6px 18px; border-radius: 20px;
                              font-size: 13px; font-weight: 600;">
                        Read Post →
                    </a>
                </div>
            </div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily AI Brief — {date}</title>
    <!--[if mso]>
    <style>table, td {{font-family: Arial, sans-serif;}}</style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
             background-color: {bg}; color: {text_primary}; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;">

    <!-- Wrapper -->
    <div style="max-width: 640px; margin: 0 auto; padding: 20px 16px;">

        <!-- Header -->
        <div style="text-align: center; padding: 40px 20px 32px; margin-bottom: 28px;">
            <div style="display: inline-block; background: linear-gradient(135deg, {gradient_start}, {gradient_end});
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                        background-clip: text; font-size: 14px; font-weight: 700; letter-spacing: 2px;
                        text-transform: uppercase; margin-bottom: 8px;">
                Daily AI Brief
            </div>
            <h1 style="margin: 8px 0 12px; font-size: 32px; font-weight: 800; color: {text_primary};
                       letter-spacing: -0.5px; line-height: 1.2;">
                Your AI Updates
            </h1>
            <p style="margin: 0; color: {text_secondary}; font-size: 15px;">
                {date} &nbsp;·&nbsp; {total_items} curated updates
            </p>
            <div style="width: 60px; height: 3px; margin: 20px auto 0;
                        background: linear-gradient(90deg, {gradient_start}, {gradient_end}); border-radius: 2px;"></div>
        </div>

        <!-- Top Pick -->
        {top_pick_html}

        <!-- Sections -->
        {sections_html}

        <!-- Footer -->
        <div style="text-align: center; padding: 32px 20px; margin-top: 20px;
                    background: {footer_bg}; border-radius: 12px;">
            <p style="margin: 0 0 8px; color: {text_secondary}; font-size: 13px;">
                Curated with 🤖 by <strong style="color: {accent_light};">AI Newsletter Bot</strong>
            </p>
            <p style="margin: 0 0 16px; color: {text_secondary}; font-size: 12px;">
                Powered by automated curation from X (Twitter)
            </p>
            <div style="border-top: 1px solid {divider}; padding-top: 16px; margin-top: 16px;">
                <p style="margin: 0; color: {text_secondary}; font-size: 11px;">
                    To unsubscribe, remove your email from config.yaml and restart the service.
                </p>
            </div>
        </div>

    </div>
</body>
</html>'''

    return html
