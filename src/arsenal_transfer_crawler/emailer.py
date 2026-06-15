from __future__ import annotations

import os
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage
from html import escape

from .crawler import NewsItem

STYLE = """
body { margin:0; padding:0; background:#f4f5f7; font-family:Arial, Helvetica, sans-serif; color:#17202a; }
.wrap { max-width:760px; margin:0 auto; padding:24px; }
.hero { background:#db0007; color:white; border-radius:18px; padding:28px; }
.hero h1 { margin:0 0 8px; font-size:28px; }
.card { background:white; margin-top:18px; border-radius:16px; padding:20px; box-shadow:0 6px 20px rgba(0,0,0,.08); }
.meta { color:#667085; font-size:13px; }
.badge { display:inline-block; background:#fbe9ea; color:#b00020; border-radius:999px; padding:5px 10px; font-weight:bold; font-size:12px; }
a { color:#db0007; text-decoration:none; font-weight:bold; }
ol { padding-left:22px; }
li { margin-bottom:18px; }
.summary { line-height:1.55; margin:8px 0; }
.footer { color:#667085; font-size:12px; margin-top:18px; text-align:center; }
"""


def render_report(items: list[NewsItem], errors: list[str]) -> str:
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    if items:
        rows = []
        for item in items:
            published = f" · {item.published.strftime('%Y-%m-%d %H:%M %Z')}" if item.published else ""
            rows.append(
                "<li>"
                f'<div><a href="{escape(item.link, quote=True)}">{escape(item.title)}</a></div>'
                f'<div class="meta">{escape(item.source)} · credibility {item.credibility}/100{published}</div>'
                f'<p class="summary">{escape(item.summary or "No summary provided by source feed.")}</p>'
                f'<span class="badge">rank score {item.score}</span>'
                "</li>"
            )
        content = f"<ol>{''.join(rows)}</ol>"
    else:
        content = "<p>No Arsenal transfer items were found in the configured lookback window.</p>"

    warnings = ""
    if errors:
        warnings = "<div class=\"card\"><strong>Source warnings</strong><ul>" + "".join(f"<li>{escape(error)}</li>" for error in errors) + "</ul></div>"

    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><style>{STYLE}</style></head>
<body><div class="wrap"><div class="hero"><h1>Arsenal Transfer Digest</h1><div>Sorted by source credibility and transfer relevance.</div></div><div class="card">{content}</div>{warnings}<div class="footer">Generated at {generated_at}.</div></div></body>
</html>"""


def build_message(recipient: str, html: str) -> EmailMessage:
    message = EmailMessage()
    sender = os.environ["SMTP_FROM"]
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = "Arsenal transfer news digest"
    message.set_content("Your email client does not support HTML. Please view this report in an HTML-capable client.")
    message.add_alternative(html, subtype="html")
    return message


def send_email(recipient: str, html: str) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    use_ssl = os.environ.get("SMTP_SSL", "false").casefold() == "true"

    message = build_message(recipient, html)
    smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_cls(host, port, timeout=30) as server:
        if not use_ssl:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(message)
