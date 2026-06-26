#!/usr/bin/env python3
"""Generate Grit WhatsApp Growth Plan PDF."""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import re

PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm
USABLE = PAGE_W - 2 * MARGIN

# Brand colours
GRIT_BLACK  = colors.HexColor("#0D0D0D")
GRIT_WHITE  = colors.HexColor("#FFFFFF")
GRIT_ORANGE = colors.HexColor("#FF6B00")
GRIT_DARK   = colors.HexColor("#1A1A1A")
GRIT_GREY   = colors.HexColor("#F5F5F5")
GRIT_MID    = colors.HexColor("#666666")
GRIT_GREEN  = colors.HexColor("#00A651")
GRIT_BLUE   = colors.HexColor("#0066CC")

def clean(text):
    """Strip unsupported Unicode, replace common emoji with ASCII equivalents."""
    replacements = {
        "✅": "[YES]", "❌": "[NO]", "⚠": "[!]",
        "⭐": "*", "\U0001f525": ">>", "\U0001f4aa": "[STRONG]",
        "\U0001f4b0": "$", "\U0001f3af": "[TARGET]", "\U0001f4f1": "[PHONE]",
        "\U0001f4e2": "[ANNOUNCE]", "\U0001f4ac": "[CHAT]", "\U0001f4ca": "[STATS]",
        "\U0001f3c6": "[WIN]", "\U0001f91d": "[DEAL]", "\U0001f4dd": "[NOTE]",
        "✔": "OK", "●": "-", "→": "->", "•": "-",
    }
    for emoji, sub in replacements.items():
        text = text.replace(emoji, sub)
    text = re.sub(r'[^\x00-\xFF‐-—‘-”•…]', '', text)
    return text

def _wrap(data, normal_style, bold_style=None):
    """Convert all table cells to Paragraph objects."""
    result = []
    for row in data:
        new_row = []
        for cell in row:
            if isinstance(cell, str):
                style = bold_style if bold_style and row.index(cell) == 0 and data.index(row) == 0 else normal_style
                new_row.append(Paragraph(clean(cell), normal_style))
            else:
                new_row.append(cell)
        result.append(new_row)
    return result

def make_styles():
    base = getSampleStyleSheet()

    styles = {}
    styles["body"] = ParagraphStyle("body", parent=base["Normal"],
        fontName="Helvetica", fontSize=9.5, leading=14,
        textColor=GRIT_BLACK, spaceAfter=6)

    styles["body_white"] = ParagraphStyle("body_white", parent=base["Normal"],
        fontName="Helvetica", fontSize=9.5, leading=14,
        textColor=GRIT_WHITE, spaceAfter=4)

    styles["h1"] = ParagraphStyle("h1", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=26, leading=32,
        textColor=GRIT_WHITE, spaceAfter=6, alignment=TA_CENTER)

    styles["h2"] = ParagraphStyle("h2", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=15, leading=20,
        textColor=GRIT_ORANGE, spaceBefore=14, spaceAfter=6)

    styles["h3"] = ParagraphStyle("h3", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=11, leading=15,
        textColor=GRIT_BLACK, spaceBefore=8, spaceAfter=4)

    styles["sub"] = ParagraphStyle("sub", parent=base["Normal"],
        fontName="Helvetica", fontSize=8.5, leading=12,
        textColor=GRIT_MID, spaceAfter=4)

    styles["tag"] = ParagraphStyle("tag", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8, leading=12,
        textColor=GRIT_WHITE, spaceAfter=2, alignment=TA_CENTER)

    styles["table_hdr"] = ParagraphStyle("table_hdr", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9, leading=12,
        textColor=GRIT_WHITE)

    styles["table_cell"] = ParagraphStyle("table_cell", parent=base["Normal"],
        fontName="Helvetica", fontSize=8.5, leading=12,
        textColor=GRIT_BLACK)

    styles["table_cell_bold"] = ParagraphStyle("table_cell_bold", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8.5, leading=12,
        textColor=GRIT_BLACK)

    styles["orange_label"] = ParagraphStyle("orange_label", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9, leading=12,
        textColor=GRIT_ORANGE, spaceAfter=2)

    styles["caption"] = ParagraphStyle("caption", parent=base["Normal"],
        fontName="Helvetica-Oblique", fontSize=8, leading=11,
        textColor=GRIT_MID, spaceAfter=4, alignment=TA_CENTER)

    styles["cover_sub"] = ParagraphStyle("cover_sub", parent=base["Normal"],
        fontName="Helvetica", fontSize=13, leading=18,
        textColor=GRIT_WHITE, alignment=TA_CENTER, spaceAfter=4)

    styles["bullet"] = ParagraphStyle("bullet", parent=base["Normal"],
        fontName="Helvetica", fontSize=9.5, leading=14,
        textColor=GRIT_BLACK, leftIndent=12, spaceAfter=3,
        bulletIndent=0, bulletFontName="Helvetica-Bold")

    return styles


def section_header(title, styles):
    return [
        Paragraph(title, styles["h2"]),
        HRFlowable(width=USABLE, thickness=1.5, color=GRIT_ORANGE, spaceAfter=8),
    ]


def dark_table(data, col_widths, styles):
    """Table with dark header row."""
    wrapped = []
    for i, row in enumerate(data):
        new_row = []
        for cell in row:
            if isinstance(cell, str):
                s = styles["table_hdr"] if i == 0 else styles["table_cell"]
                new_row.append(Paragraph(clean(cell), s))
            else:
                new_row.append(cell)
        wrapped.append(new_row)

    t = Table(wrapped, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), GRIT_BLACK),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [GRIT_WHITE, GRIT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#DDDDDD")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return t


def highlight_box(lines, styles, bg=None, label=None):
    """Coloured callout box."""
    bg = bg or GRIT_GREY
    content = []
    if label:
        content.append(Paragraph(clean(label), styles["orange_label"]))
    for line in lines:
        content.append(Paragraph(clean(line), styles["body"]))

    t = Table([[content]], colWidths=[USABLE])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def build_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN)

    styles = make_styles()
    story = []

    # ── COVER ─────────────────────────────────────────────────────────────────
    cover_bg = Table(
        [[
            Paragraph("GRIT", styles["h1"]),
            Spacer(1, 6),
            Paragraph("WhatsApp Growth Playbook", styles["cover_sub"]),
            Paragraph("Zero-to-1,000 Subscribers via WhatsApp-Only Marketing", styles["cover_sub"]),
            Spacer(1, 12),
            Paragraph("Confidential  |  June 2026", ParagraphStyle("cov_date",
                fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#AAAAAA"),
                alignment=TA_CENTER)),
        ]],
        colWidths=[USABLE]
    )
    cover_bg.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GRIT_BLACK),
        ("LEFTPADDING", (0,0), (-1,-1), 24),
        ("RIGHTPADDING", (0,0), (-1,-1), 24),
        ("TOPPADDING", (0,0), (-1,-1), 48),
        ("BOTTOMPADDING", (0,0), (-1,-1), 48),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(cover_bg)
    story.append(Spacer(1, 18))

    story.append(Paragraph(
        "This playbook is your complete WhatsApp-first go-to-market strategy for Grit. "
        "Every tactic, message template, and milestone lives inside WhatsApp itself — "
        "no ads, no website, no app store. Just conversations that convert.",
        styles["body"]))
    story.append(Spacer(1, 10))

    # Key metrics row
    kpi_data = [
        ["Target", "Timeline", "CAC Goal", "Avg LTV"],
        ["1,000 paying users", "12 months", "< $5 USD", "$120 USD"],
    ]
    kpi_t = Table(
        _wrap(kpi_data, styles["table_cell"], styles["table_hdr"]),
        colWidths=[USABLE/4]*4
    )
    kpi_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), GRIT_ORANGE),
        ("BACKGROUND", (0,1), (-1,1), GRIT_GREY),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#DDDDDD")),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(kpi_t)
    story.append(Spacer(1, 4))
    story.append(Paragraph("All figures in USD. Pricing model: $9.99/month Pro tier as primary offer.", styles["caption"]))
    story.append(PageBreak())

    # ── 1. WHY WHATSAPP-FIRST ─────────────────────────────────────────────────
    story += section_header("1. Why WhatsApp-First Makes Sense", styles)
    story.append(Paragraph(
        "Most SaaS products fight for attention inside crowded app stores or social feeds. "
        "Grit's advantage is that the product IS the channel. "
        "Users get coached inside the same app they use to text their friends — "
        "no install, no login, no friction. That unlocks a marketing strategy most competitors can't copy.", styles["body"]))
    story.append(Spacer(1, 8))

    adv_data = [
        ["Advantage", "What It Means for Growth"],
        ["No app download", "Share link opens a chat — zero install drop-off. Typical app install rate from a link is 15-25%. WhatsApp chat open rate is 95%+."],
        ["Already trusted", "WhatsApp is the world's #1 messaging app. Users don't fear clicking a wa.me link from a friend."],
        ["Share-native", "The referral mechanic is built into the product. Users forward their personalised link the same way they share a meme."],
        ["Global reach", "Works in Australia, UK, US, India, Nigeria — any WhatsApp market — with zero additional infrastructure."],
        ["Low cost to serve", "One WhatsApp Business API account reaches millions. Meta charges per conversation (~$0.05 AUD), not per message."],
        ["Organic proof", "Coaching conversations appear in the same thread the user scrolls daily. Progress screenshots get shared naturally."],
    ]
    story.append(dark_table(adv_data, [5*cm, USABLE - 5*cm], styles))
    story.append(Spacer(1, 12))
    story.append(PageBreak())

    # ── 2. THE FUNNEL ─────────────────────────────────────────────────────────
    story += section_header("2. The WhatsApp Acquisition Funnel", styles)

    funnel_stages = [
        ("AWARENESS", GRIT_ORANGE, [
            "Person sees a WhatsApp screenshot posted by a friend, influencer, or in a Facebook Group.",
            "Or they receive a personal referral message from an existing Grit user.",
            "Or they spot a short-form video (Reels/TikTok) where the coach is inside WhatsApp.",
        ]),
        ("INTEREST", colors.HexColor("#0077B6"), [
            "They tap the wa.me link or scan the QR code.",
            "WhatsApp opens instantly — no app store, no email signup.",
            "Grit sends: 'Hi! I'm Grit — your personal accountability coach. What's your name?'",
        ]),
        ("ONBOARDING (10 mins)", GRIT_GREEN, [
            "10 short questions establish goal, timeline, schedule, tone preference.",
            "Grit generates a personalised 90-day plan and sends it as a PDF.",
            "Trial starts — 7 days free (30 days if referred).",
        ]),
        ("CONVERSION", GRIT_ORANGE, [
            "Daily check-ins build habit and emotional investment.",
            "On Day 5 (or Day 28 if referred), pricing menu is sent.",
            "One-tap reply selects tier — Stripe checkout link sent automatically.",
        ]),
        ("REFERRAL", GRIT_DARK, [
            "After payment confirmed, user receives their unique share link.",
            "Prompted to share via WhatsApp to contacts, groups, or status.",
            "Every converted referral earns 20% recurring commission — paid monthly.",
        ]),
    ]

    for stage, colour, bullets in funnel_stages:
        stage_content = [Paragraph(stage, ParagraphStyle("stage_lbl",
            fontName="Helvetica-Bold", fontSize=9, textColor=GRIT_WHITE))]
        for b in bullets:
            stage_content.append(Paragraph("- " + b, styles["body_white"]))

        t = Table([[stage_content]], colWidths=[USABLE])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colour),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 8))
    story.append(highlight_box([
        "The entire funnel — awareness through payment — can complete in under 15 minutes. "
        "A referred friend taps a link at 8pm, completes onboarding, and receives their first "
        "check-in by 8am the next morning. No human sales touchpoint required."
    ], styles, label="KEY INSIGHT"))
    story.append(PageBreak())

    # ── 3. 30-DAY LAUNCH PLAN ────────────────────────────────────────────────
    story += section_header("3. Day-by-Day: 30-Day WhatsApp Launch Plan", styles)
    story.append(Paragraph(
        "This plan assumes you are starting from zero — no subscribers, no audience, no ad budget. "
        "All activities are free or use the built-in referral programme.", styles["body"]))
    story.append(Spacer(1, 8))

    plan_data = [
        ["Days", "Focus", "Daily Actions", "Target Outcome"],
        ["1-3", "Foundation",
         "- Register WhatsApp Business number\n- Set display name to 'Grit'\n- Set profile photo & description\n- Create your personal referral link\n- Test the full onboarding flow yourself",
         "System live. Your link works."],
        ["4-7", "Warm Network",
         "- Message 20 people you know personally\n- Send: 'Testing my new AI accountability coach — want to try it free for 7 days?'\n- Include your wa.me link\n- Follow up with anyone who doesn't reply",
         "10-20 trial signups from warm contacts"],
        ["8-14", "Facebook Groups",
         "- Find 5 active groups: fitness, finance, personal dev (AU-based)\n- Post genuine value (tip or insight) every 2 days\n- On Day 3 in each group, share your story + Grit link\n- Respond to every comment personally",
         "20-40 new trial signups"],
        ["15-21", "Referral Engine",
         "- Identify your most engaged trial users\n- Send: 'Reply SHARE and I'll send you your referral link + earn 20% every month'\n- Help them craft their own personal share message\n- Celebrate every referral publicly (with permission)",
         "First 5-10 referral-generated users"],
        ["22-28", "Content Leverage",
         "- Screenshot 3 real check-in conversations (anonymised or with consent)\n- Post to personal Facebook, Instagram Stories, LinkedIn\n- Caption: 'This is what accountability looks like in 2026'\n- Add wa.me link in bio and post caption",
         "20-50 inbound link clicks"],
        ["29-30", "Review & Double Down",
         "- Identify top 3 acquisition channels from analytics\n- Double outreach in winning channel\n- Personally message every user who didn't convert from trial\n- Offer 1-month extension for feedback call",
         "50-100 total trialists, 15-30 paying"],
    ]
    plan_t = dark_table(plan_data, [1.6*cm, 2.4*cm, 7.5*cm, USABLE - 11.5*cm], styles)
    story.append(plan_t)
    story.append(Spacer(1, 8))
    story.append(PageBreak())

    # ── 4. WHATSAPP MESSAGE TEMPLATES ────────────────────────────────────────
    story += section_header("4. WhatsApp Message Templates (Copy-Paste Ready)", styles)
    story.append(Paragraph(
        "Use these exact templates. They are written the way people actually text — short, "
        "direct, no corporate language. Edit the [brackets] to personalise.", styles["body"]))
    story.append(Spacer(1, 10))

    templates = [
        ("WARM OUTREACH (send to contacts you know)", [
            "Hey [name] - I just launched something and you're one of the first people I thought of.",
            "It's an AI accountability coach on WhatsApp - no app to download, just texts you daily.",
            "Free for 7 days. Tap this and it'll introduce itself:",
            "[wa.me link]",
            "Would love your honest feedback.",
        ]),
        ("FACEBOOK GROUP POST", [
            "Anyone else find it impossible to stay consistent without someone checking in on you?",
            "I've been building an AI coach that does exactly that - texts you daily on WhatsApp,",
            "tracks your streaks, sends you a personalised plan.",
            "Testing it free for the next 7 days if anyone wants to try it:",
            "[wa.me link]",
            "No app to download. Just opens a chat.",
        ]),
        ("FOLLOW-UP TO NON-RESPONDER (send 3 days later)", [
            "Hey - just checking in. Did you get a chance to try Grit?",
            "No worries if not - totally free to start. Only takes 10 minutes.",
            "Here's the link again: [wa.me link]",
        ]),
        ("REFERRAL PROMPT (send to active users)", [
            "Hey [name] - quick one.",
            "If you know anyone who's been trying to stick to [fitness/finance/their goal] -",
            "you can send them your personal link and they get 30 days free instead of 7.",
            "And you earn 20% of whatever they pay, every month they stay.",
            "Reply SHARE and I'll send your link now.",
        ]),
        ("REFERRAL SHARE MESSAGE (user sends to their contacts)", [
            "Have you heard of Grit? It's an AI coach on WhatsApp - no app.",
            "Checks in with you every day, tracks your goals, sends you a proper plan.",
            "I've been using it and it actually works.",
            "Use my link and you get 30 days free (instead of 7):",
            "[their referral link]",
        ]),
        ("INFLUENCER COLD OUTREACH (DM on Instagram)", [
            "Hey [name] - I follow your [fitness/finance] content and it's genuinely good.",
            "I've built an AI accountability coach that lives inside WhatsApp.",
            "Your audience is exactly who it's for - people who want to stay consistent but need a push.",
            "Would you try it free and give me feedback? If you like it, I'd love to chat about",
            "a partnership - you'd earn 20% recurring on every subscriber you refer.",
            "No obligation. Let me know.",
        ]),
    ]

    for title, lines in templates:
        story.append(Paragraph(title, styles["h3"]))
        msg_content = [Paragraph(clean(line), styles["body"]) for line in lines]
        t = Table([[msg_content]], colWidths=[USABLE])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F0F4FF")),
            ("LEFTPADDING", (0,0), (-1,-1), 12),
            ("RIGHTPADDING", (0,0), (-1,-1), 12),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LINEAFTER", (0,0), (0,-1), 3, GRIT_BLUE),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    story.append(PageBreak())

    # ── 5. INFLUENCER STRATEGY ───────────────────────────────────────────────
    story += section_header("5. Influencer & Creator Strategy", styles)
    story.append(Paragraph(
        "Forget expensive macro-influencers. WhatsApp converts best when it feels personal. "
        "Target micro-creators (2K-50K followers) whose audiences have a specific goal — "
        "exactly what Grit solves.", styles["body"]))
    story.append(Spacer(1, 8))

    inf_data = [
        ["Creator Tier", "Followers", "Approach", "Commission", "Expected Signups"],
        ["Friends & Family", "0", "Personal ask — 'I built this, would you try it?'", "None (goodwill)", "5-20"],
        ["Micro-Influencer", "2K-20K", "Free 30-day access + 20% recurring affiliate", "20% recurring", "20-100/month"],
        ["Mid-Tier Creator", "20K-200K", "Free access + 20% recurring + rev share on first 100", "20% + bonus", "100-500/month"],
        ["Niche Community Manager", "500-5K group members", "Exclusive group discount code + 20% recurring", "20% recurring", "10-50/month"],
        ["Podcast Host", "Any size", "30-second promo + unique code + 20% commission", "20% recurring", "5-30/month"],
    ]
    story.append(dark_table(inf_data, [3.2*cm, 2.2*cm, 5.5*cm, 2.8*cm, USABLE - 13.7*cm], styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("How to Find Micro-Creators (Free)", styles["h3"]))
    find_tips = [
        "Search Instagram hashtags: #australianfitness #moneygoals #personaldevelopment #gymlife",
        "Search TikTok: 'accountability challenge', 'goal tracker', '75 hard', 'money journey'",
        "Facebook Groups: search '[city] fitness', 'Australian personal finance', 'side hustle Australia'",
        "Reddit: r/fitness, r/personalfinance, r/ausfinance — look for top commenters with history",
        "LinkedIn: search 'accountability coach', 'productivity consultant' — DM with specific pitch",
    ]
    for tip in find_tips:
        story.append(Paragraph("- " + tip, styles["bullet"]))
    story.append(Spacer(1, 8))

    story.append(highlight_box([
        "The single best creator partnership: find a fitness or finance creator who posts daily habits content. "
        "They share their Grit referral link once in Stories. Their audience trusts them. "
        "The link opens WhatsApp instantly. Even a 1% conversion on 10K views = 100 trials."
    ], styles, label="HIGHEST-LEVERAGE MOVE"))
    story.append(PageBreak())

    # ── 6. WHATSAPP STATUS STRATEGY ──────────────────────────────────────────
    story += section_header("6. WhatsApp Status Strategy (Organic Reach)", styles)
    story.append(Paragraph(
        "WhatsApp Status (like Stories) shows to all your contacts. "
        "Post to your personal number's Status daily during launch. "
        "It's the most underrated free channel for WhatsApp-native products.", styles["body"]))
    story.append(Spacer(1, 8))

    status_data = [
        ["Day", "Status Content", "Call-to-Action"],
        ["Mon", "Screenshot of a Grit check-in conversation (anonymised)", "Reply to this status to try it free"],
        ["Tue", "Stat graphic: 'People who track daily are 3x more likely to hit their goals'", "Link in reply — tap to start"],
        ["Wed", "Testimonial quote from a trial user (with permission)", "DM me and I'll send you their link"],
        ["Thu", "Your own streak counter — 'Day 14 streak with Grit'", "Ask how — reply to this status"],
        ["Fri", "Before/after of a week's check-ins showing progress summary", "Tap to try free for 7 days"],
        ["Sat", "Motivational graphic relevant to your niche", "No hard sell — brand awareness"],
        ["Sun", "Weekly results post — how many people started this week", "Tap the link and join them"],
    ]
    story.append(dark_table(status_data, [1.5*cm, 7.5*cm, USABLE - 9*cm], styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("QR Code Placement", styles["h3"]))
    qr_tips = [
        "Print a QR code that opens your wa.me link and stick it anywhere people stand still: gym noticeboard, cafe counter, coworking space, physiotherapy waiting room.",
        "Add the QR code to your email signature with the line: 'Trying to hit a goal? Tap this.'",
        "Create a simple Canva graphic with the QR code for Instagram bio, Facebook cover photo, and LinkedIn banner.",
        "If you do any public speaking, workshops, or group fitness classes — put the QR on the first slide.",
    ]
    for tip in qr_tips:
        story.append(Paragraph("- " + tip, styles["bullet"]))
    story.append(PageBreak())

    # ── 7. REFERRAL ENGINE ───────────────────────────────────────────────────
    story += section_header("7. The Built-In Referral Engine", styles)
    story.append(Paragraph(
        "The referral programme is the most scalable part of Grit's growth strategy. "
        "Unlike traditional affiliate programmes, Grit's referrals happen inside WhatsApp — "
        "the most trusted channel for personal recommendations.", styles["body"]))
    story.append(Spacer(1, 8))

    ref_flow = [
        ("Step 1: User types SHARE", "Grit sends their unique link: wa.me/61XXXXXXXXXX?text=START+BRETT-X7K2"),
        ("Step 2: User sends to contacts", "Pre-written message included. One tap to forward in WhatsApp."),
        ("Step 3: Friend taps link", "WhatsApp opens. Chat starts. 30-day free trial activated automatically."),
        ("Step 4: Friend subscribes", "Stripe webhook fires. 20% commission calculated and added to referrer wallet."),
        ("Step 5: Monthly payout", "1st of every month: referrer receives WhatsApp message with earnings + bank transfer."),
    ]

    for step, desc in ref_flow:
        row_t = Table(
            [[Paragraph(clean(step), styles["table_cell_bold"]),
              Paragraph(clean(desc), styles["table_cell"])]],
            colWidths=[4.5*cm, USABLE - 4.5*cm]
        )
        row_t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,0), GRIT_ORANGE),
            ("BACKGROUND", (1,0), (1,0), GRIT_GREY),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LINEBELOW", (0,0), (-1,-1), 0.5, GRIT_WHITE),
        ]))
        story.append(row_t)

    story.append(Spacer(1, 10))

    econ_data = [
        ["Referral Economics", ""],
        ["Commission rate", "20% of monthly subscription"],
        ["Referred user trial", "30 days free (vs 7 days standard)"],
        ["Referred user discount", "20% off first paid month"],
        ["Referrer earns per $9.99 sub", "$2.00/month recurring"],
        ["Referrer with 10 active referrals", "$20/month passive income"],
        ["Referrer with 50 active referrals", "$100/month passive income"],
        ["Platform cost of programme", "20% margin reduction — offset by near-zero CAC"],
    ]

    t = Table(
        _wrap(econ_data, styles["table_cell"]),
        colWidths=[USABLE * 0.55, USABLE * 0.45]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), GRIT_BLACK),
        ("TEXTCOLOR", (0,0), (-1,0), GRIT_WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [GRIT_WHITE, GRIT_GREY]),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#DDDDDD")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ── 8. GROWTH PROJECTIONS ────────────────────────────────────────────────
    story += section_header("8. Realistic Growth Projections", styles)
    story.append(Paragraph(
        "Three scenarios modelled on WhatsApp-native products with similar referral mechanics. "
        "Conservative assumes manual outreach only. Base includes 5 micro-influencer partnerships. "
        "Optimistic assumes 2 mid-tier creator partnerships in Month 4+.", styles["body"]))
    story.append(Spacer(1, 8))

    proj_data = [
        ["Month", "Conservative\n(paid users)", "Base Case\n(paid users)", "Optimistic\n(paid users)", "Base MRR (USD)"],
        ["1",  "10",   "20",   "30",    "$200"],
        ["2",  "25",   "50",   "80",    "$500"],
        ["3",  "45",   "100",  "180",   "$1,000"],
        ["4",  "70",   "170",  "350",   "$1,700"],
        ["5",  "100",  "260",  "550",   "$2,600"],
        ["6",  "135",  "380",  "800",   "$3,800"],
        ["7",  "175",  "510",  "1,050", "$5,100"],
        ["8",  "220",  "650",  "1,300", "$6,500"],
        ["9",  "270",  "800",  "1,550", "$8,000"],
        ["10", "325",  "960",  "1,800", "$9,600"],
        ["11", "385",  "1,120","2,050", "$11,200"],
        ["12", "450",  "1,300","2,300", "$13,000"],
    ]
    story.append(dark_table(proj_data, [1.8*cm, 3.2*cm, 3.2*cm, 3.2*cm, USABLE - 11.4*cm], styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Base case assumptions: 30% trial-to-paid conversion, 5% monthly churn, "
        "each paying user refers 0.3 additional users on average. "
        "Creator partnerships add ~100 trials/month from Month 3.", styles["caption"]))
    story.append(Spacer(1, 10))

    story.append(highlight_box([
        "Month 7 base case: 510 paying users x $9.99 = $5,100 MRR. Gross margin ~78% after "
        "Stripe fees, Meta API costs, Railway hosting, and referral commissions. "
        "Net profit at this scale: approximately $3,900/month USD.",
    ], styles, label="$5K/MONTH MILESTONE"))
    story.append(Spacer(1, 10))

    story.append(Paragraph("What Drives the Difference Between Scenarios", styles["h3"]))
    driver_data = [
        ["Driver", "Conservative", "Base", "Optimistic"],
        ["Referral rate (referrals per user)", "0.1", "0.3", "0.6"],
        ["Creator partnerships", "0", "5 micro", "2 mid-tier"],
        ["Trial conversion rate", "20%", "30%", "35%"],
        ["Monthly churn rate", "8%", "5%", "3%"],
        ["Outreach per week (manual)", "10 messages", "30 messages", "50 messages"],
    ]
    story.append(dark_table(driver_data, [5*cm, 3*cm, 3*cm, USABLE - 11*cm], styles))
    story.append(PageBreak())

    # ── 9. CONTENT THAT CONVERTS ─────────────────────────────────────────────
    story += section_header("9. Content That Drives WhatsApp Signups", styles)
    story.append(Paragraph(
        "You don't need a massive following. You need content that makes people "
        "immediately want to tap a link. Here's what works for WhatsApp-native products.", styles["body"]))
    story.append(Spacer(1, 8))

    content_types = [
        ("SCREENSHOT POSTS", "HIGH",
         "Post a real conversation between a user and Grit (anonymised). "
         "Show the check-in question and an honest reply. Show the streak counter. "
         "People see themselves in it — and they tap the link."),
        ("BEFORE/AFTER BEHAVIOUR", "HIGH",
         "'Before Grit: skipped gym 4 times this week. After Grit: Day 23 streak.' "
         "No transformation photos needed. Behaviour change is the proof."),
        ("FAIL POSTS", "MEDIUM",
         "Share when a user missed a day and Grit's response. Real, human, encouraging. "
         "This builds trust — people know it won't judge them."),
        ("STAT GRAPHICS", "MEDIUM",
         "'People who track daily are 42% more likely to achieve their goal.' "
         "One fact. One visual. Link in comments. Run this as a boosted post for $5/day."),
        ("SHORT REELS/TIKTOKS", "VERY HIGH",
         "Screen-record a 30-second WhatsApp conversation with Grit. "
         "No voiceover needed. Just the chat. Caption: 'My AI accountability coach just said this.' "
         "These go viral in fitness and finance niches."),
        ("TESTIMONIALS", "HIGH",
         "After Week 1, message every active trial user: 'How's it going? Mind if I share your words?' "
         "Post exact quotes. Real people. Real goals. Infinitely more powerful than any ad copy."),
    ]

    for content_type, impact, desc in content_types:
        impact_colour = GRIT_GREEN if impact == "VERY HIGH" else (GRIT_ORANGE if impact == "HIGH" else GRIT_BLUE)
        row_t = Table(
            [[
                Paragraph(clean(content_type), styles["table_cell_bold"]),
                Paragraph(impact, ParagraphStyle("impact", fontName="Helvetica-Bold",
                    fontSize=8, textColor=GRIT_WHITE, alignment=TA_CENTER)),
                Paragraph(clean(desc), styles["table_cell"]),
            ]],
            colWidths=[3.5*cm, 1.8*cm, USABLE - 5.3*cm]
        )
        row_t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,0), GRIT_GREY),
            ("BACKGROUND", (1,0), (1,0), impact_colour),
            ("BACKGROUND", (2,0), (2,0), GRIT_WHITE),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LINEBELOW", (0,0), (-1,-1), 0.5, colors.HexColor("#EEEEEE")),
            ("ALIGN", (1,0), (1,0), "CENTER"),
            ("VALIGN", (1,0), (1,0), "MIDDLE"),
        ]))
        story.append(row_t)
    story.append(Spacer(1, 8))
    story.append(PageBreak())

    # ── 10. WEEKLY OPERATING RHYTHM ──────────────────────────────────────────
    story += section_header("10. Weekly Operating Rhythm (Founder-Led Phase)", styles)
    story.append(Paragraph(
        "Until you hit 200 paying users, growth is founder-led. "
        "This is the exact weekly routine that compounds fastest.", styles["body"]))
    story.append(Spacer(1, 8))

    rhythm_data = [
        ["Day", "Time", "Activity", "Tool"],
        ["Monday", "30 min", "Review last week's trial signups. Message anyone who didn't complete onboarding.", "WhatsApp"],
        ["Monday", "15 min", "Post weekly stat or insight to Facebook Groups (3-5 groups)", "Facebook"],
        ["Tuesday", "20 min", "Cold DM 10 micro-influencers with personalised pitch", "Instagram/TikTok DMs"],
        ["Wednesday", "20 min", "Post screenshot or testimonial to personal social accounts", "Instagram/LinkedIn"],
        ["Wednesday", "15 min", "Message 5 current trial users: 'How's it going? Anything I can improve?'", "WhatsApp"],
        ["Thursday", "20 min", "Follow up with influencers who didn't reply. Engage with their content first.", "Instagram"],
        ["Friday", "15 min", "Post WhatsApp Status content for the weekend", "WhatsApp Status"],
        ["Friday", "20 min", "Send SHARE prompt to users who've been active 5+ days", "WhatsApp"],
        ["Sunday", "30 min", "Review weekly numbers: signups, trials, conversions, referrals, churn", "Railway analytics / DB"],
        ["Sunday", "15 min", "Plan next week's outreach list and content", "Notes app"],
    ]
    story.append(dark_table(rhythm_data, [2*cm, 1.5*cm, 8.5*cm, USABLE - 12*cm], styles))
    story.append(Spacer(1, 10))

    story.append(highlight_box([
        "Total weekly time commitment: approximately 3 hours. "
        "This is the minimum viable founder-led growth effort. "
        "As revenue grows, reinvest 20% back into paid acquisition (boosted posts or influencer fees) "
        "to remove the manual ceiling."
    ], styles, label="TIME COMMITMENT"))
    story.append(PageBreak())

    # ── 11. WHAT NOT TO DO ───────────────────────────────────────────────────
    story += section_header("11. What NOT to Do (WhatsApp Marketing Mistakes)", styles)
    story.append(Spacer(1, 6))

    mistakes = [
        ("Spamming broadcast lists", "AVOID",
         "Sending unsolicited WhatsApp messages to people who haven't opted in violates Meta's policy "
         "and will get your Business Account banned. Only send to people who've messaged you first."),
        ("Buying follower lists", "AVOID",
         "Fake followers don't tap links. Real micro-communities of 500 engaged people outperform "
         "50,000 bot followers every time for WhatsApp conversions."),
        ("Posting the same message everywhere", "AVOID",
         "Facebook Group admins will remove you. Personalise every outreach. "
         "Reference something specific about the group or the person's content."),
        ("Spending on ads before proving conversion", "RISK",
         "Don't run paid ads until you have evidence that 25%+ of trial users convert to paid. "
         "Prove the funnel manually first, then scale with budget."),
        ("Ignoring trial users who go quiet", "RISK",
         "A user who completes onboarding but stops responding is your most recoverable churner. "
         "A personal message from the founder ('everything okay?') has a 30-40% reactivation rate."),
        ("Setting it and forgetting it", "RISK",
         "In the first 6 months, no automation replaces founder involvement. "
         "Read every check-in reply, respond to every support message, fix every friction point personally."),
    ]

    for mistake, level, desc in mistakes:
        level_colour = colors.HexColor("#CC0000") if level == "AVOID" else colors.HexColor("#E67E00")
        row_t = Table(
            [[
                Paragraph(clean(mistake), styles["table_cell_bold"]),
                Paragraph(level, ParagraphStyle("lv", fontName="Helvetica-Bold",
                    fontSize=8, textColor=GRIT_WHITE, alignment=TA_CENTER)),
                Paragraph(clean(desc), styles["table_cell"]),
            ]],
            colWidths=[3.5*cm, 1.5*cm, USABLE - 5*cm]
        )
        row_t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (0,0), GRIT_GREY),
            ("BACKGROUND", (1,0), (1,0), level_colour),
            ("BACKGROUND", (2,0), (2,0), GRIT_WHITE),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LINEBELOW", (0,0), (-1,-1), 0.5, colors.HexColor("#EEEEEE")),
        ]))
        story.append(row_t)
    story.append(Spacer(1, 10))
    story.append(PageBreak())

    # ── 12. SUCCESS METRICS ──────────────────────────────────────────────────
    story += section_header("12. Key Metrics to Track Weekly", styles)
    story.append(Spacer(1, 6))

    metrics_data = [
        ["Metric", "How to Measure", "Healthy Target", "Red Flag"],
        ["Trial signups/week", "New users in DB with onboarding_complete=True", "> 20 by Month 2", "< 5/week for 3 weeks"],
        ["Trial-to-paid rate", "(paying / completed trials) x 100", "> 25%", "< 15%"],
        ["Day 7 retention", "Users still active after 7 days of trial", "> 60%", "< 40%"],
        ["Referral rate", "Referrals generated / paying users", "> 0.3 per user", "< 0.1 after Month 2"],
        ["Monthly churn", "(cancelled this month / active start of month)", "< 5%", "> 10%"],
        ["WhatsApp reply rate", "% of check-in messages that get a reply", "> 50%", "< 25%"],
        ["Avg streak length", "Average current_streak across active users", "> 10 days", "< 4 days"],
        ["MRR growth rate", "(this month MRR - last month) / last month", "> 20%/month", "< 10%/month"],
    ]
    story.append(dark_table(metrics_data, [3.5*cm, 4.5*cm, 3*cm, USABLE - 11*cm], styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Your Most Important Number", styles["h3"]))
    story.append(Paragraph(
        "Until Month 6, the only metric that truly matters is <b>trial-to-paid conversion rate</b>. "
        "Everything else — CAC, MRR, churn — is secondary until you know that people who try Grit "
        "are willing to pay for it. Hit 25%+ conversion before scaling any acquisition spend.", styles["body"]))
    story.append(Spacer(1, 12))

    # Final callout
    final_t = Table(
        [[
            Paragraph("THE CORE THESIS", ParagraphStyle("ct", fontName="Helvetica-Bold",
                fontSize=12, textColor=GRIT_ORANGE, spaceAfter=6)),
            Paragraph(
                "Grit wins because the product is the channel. "
                "Every satisfied user becomes a distribution node. "
                "Every referral link they share is a personalised recommendation "
                "that opens directly in WhatsApp — the highest-trust messaging platform on earth. "
                "No ad budget can replicate that. Build the habit, build the streak, build the referral. "
                "That is the entire playbook.",
                ParagraphStyle("ct_body", fontName="Helvetica", fontSize=10,
                    textColor=GRIT_WHITE, leading=15)),
        ]],
        colWidths=[USABLE]
    )
    final_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GRIT_BLACK),
        ("LEFTPADDING", (0,0), (-1,-1), 20),
        ("RIGHTPADDING", (0,0), (-1,-1), 20),
        ("TOPPADDING", (0,0), (-1,-1), 20),
        ("BOTTOMPADDING", (0,0), (-1,-1), 20),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("SPAN", (0,0), (-1,0)),
    ]))
    story.append(final_t)

    doc.build(story)
    print(f"PDF generated: {filename}")


if __name__ == "__main__":
    build_pdf("Grit_WhatsApp_Growth_Plan.pdf")
