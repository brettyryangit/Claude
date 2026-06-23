from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

BRAND_DARK = colors.HexColor("#0f0f1a")
BRAND_RED = colors.HexColor("#e94560")
BRAND_GREY = colors.HexColor("#555555")
BRAND_LIGHT = colors.HexColor("#f5f5f5")
BRAND_GREEN = colors.HexColor("#27ae60")
WHITE = colors.white

OUTPUT_PATH = "/home/user/Claude/Grit_Marketing_Plan.pdf"


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BRAND_DARK)
    canvas.rect(0, A4[1] - 1.2 * cm, A4[0], 1.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(2 * cm, A4[1] - 0.85 * cm, "GRIT — Full Marketing Plan")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 0.85 * cm, "Confidential — June 2026")
    canvas.setFillColor(BRAND_DARK)
    canvas.rect(0, 0, A4[0], 0.9 * cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, 0.3 * cm, "Grit AI Accountability Coach — Marketing Strategy")
    canvas.drawRightString(A4[0] - 2 * cm, 0.3 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        rightMargin=2.2 * cm,
        leftMargin=2.2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=1.8 * cm,
    )

    # ── STYLES ───────────────────────────────────────────────────────────────
    cover_title = ParagraphStyle("CT", fontSize=40, textColor=WHITE,
        alignment=TA_CENTER, fontName="Helvetica-Bold", leading=48, spaceAfter=8)
    cover_sub = ParagraphStyle("CS", fontSize=15, textColor=BRAND_RED,
        alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=6)
    cover_meta = ParagraphStyle("CM", fontSize=10, textColor=colors.HexColor("#aaaaaa"),
        alignment=TA_CENTER, fontName="Helvetica")

    h1 = ParagraphStyle("H1", fontSize=18, textColor=WHITE, fontName="Helvetica-Bold",
        spaceBefore=4, spaceAfter=10, leading=24, backColor=BRAND_DARK,
        leftIndent=-0.5*cm, rightIndent=-0.5*cm, borderPad=8)
    h2 = ParagraphStyle("H2", fontSize=13, textColor=BRAND_DARK, fontName="Helvetica-Bold",
        spaceBefore=12, spaceAfter=5)
    h3 = ParagraphStyle("H3", fontSize=11, textColor=BRAND_RED, fontName="Helvetica-Bold",
        spaceBefore=8, spaceAfter=3)
    h4 = ParagraphStyle("H4", fontSize=10, textColor=BRAND_DARK, fontName="Helvetica-Bold",
        spaceBefore=6, spaceAfter=2)
    body = ParagraphStyle("Body", fontSize=10, textColor=colors.HexColor("#222222"),
        fontName="Helvetica", leading=15, spaceAfter=7, alignment=TA_JUSTIFY)
    bullet = ParagraphStyle("Bullet", fontSize=10, textColor=colors.HexColor("#222222"),
        fontName="Helvetica", leading=14, spaceAfter=3, leftIndent=16, bulletIndent=4)
    caption = ParagraphStyle("Cap", fontSize=8, textColor=BRAND_GREY,
        fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=6)
    number_style = ParagraphStyle("Num", fontSize=28, textColor=BRAND_RED,
        fontName="Helvetica-Bold", alignment=TA_CENTER, leading=32)
    tag_style = ParagraphStyle("Tag", fontSize=10, textColor=BRAND_GREY,
        alignment=TA_CENTER, fontName="Helvetica", spaceAfter=5)
    footer_note = ParagraphStyle("FN", fontSize=8, textColor=BRAND_GREY,
        fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceBefore=16)

    def tbl(data, col_widths=None):
        t = Table(data, colWidths=col_widths, repeatRows=1)
        row_colors = []
        for i in range(1, len(data)):
            c = colors.HexColor("#f9f9f9") if i % 2 == 1 else WHITE
            row_colors.append(("BACKGROUND", (0, i), (-1, i), c))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            *row_colors,
        ]))
        return t

    def divider():
        return HRFlowable(width="100%", thickness=1.5, color=BRAND_RED, spaceAfter=8, spaceBefore=2)

    def section(text):
        return Paragraph(f"&nbsp;&nbsp;{text}", h1)

    def highlight_box(text, bg=BRAND_DARK, fg=WHITE, size=11):
        t = Table([[Paragraph(text, ParagraphStyle("HB", fontSize=size, textColor=fg,
            fontName="Helvetica-Bold", alignment=TA_CENTER, leading=size+4))]],
            colWidths=[A4[0] - 4.4*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("TOPPADDING", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ]))
        return t

    def suggestion_block(number, title, body_text, how_paid, difficulty, impact):
        num_cell = Paragraph(str(number), number_style)
        title_para = Paragraph(title, ParagraphStyle("ST", fontSize=12, textColor=BRAND_DARK,
            fontName="Helvetica-Bold", leading=16))
        body_para = Paragraph(body_text, ParagraphStyle("SB", fontSize=9.5,
            textColor=colors.HexColor("#333333"), fontName="Helvetica", leading=14))
        meta = Paragraph(
            f"<b>How you get paid:</b> {how_paid}<br/>"
            f"<b>Difficulty:</b> {difficulty} &nbsp;&nbsp; <b>Impact:</b> {impact}",
            ParagraphStyle("SM", fontSize=9, textColor=BRAND_GREY, fontName="Helvetica", leading=13)
        )
        inner = Table(
            [[title_para], [body_para], [Spacer(1, 4)], [meta]],
            colWidths=[12.3*cm]
        )
        inner.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        outer = Table(
            [[num_cell, inner]],
            colWidths=[2.2*cm, 12.3*cm]
        )
        outer.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), BRAND_LIGHT),
            ("BACKGROUND", (1, 0), (1, 0), WHITE),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e0e0e0")),
            ("LINEAFTER", (0, 0), (0, -1), 2, BRAND_RED),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (1, 0), (1, 0), 12),
        ]))
        return KeepTogether([outer, Spacer(1, 0.25*cm)])

    story = []

    # ── COVER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*cm))
    cover = Table(
        [[Paragraph("GRIT", cover_title)],
         [Paragraph("Full Marketing Plan", cover_sub)],
         [Spacer(1, 0.2*cm)],
         [Paragraph("20 Strategies · Revenue Models · Free Trial System", cover_meta)],
         [Paragraph("Yearly Pricing · Creator Playbook · Launch Timeline", cover_meta)],
         [Spacer(1, 0.2*cm)],
         [Paragraph("Confidential — June 2026", cover_meta)]],
        colWidths=[A4[0] - 4.4*cm]
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 28),
        ("RIGHTPADDING", (0, 0), (-1, -1), 28),
    ]))
    story.append(cover)
    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=3, color=BRAND_RED))
    story.append(Spacer(1, 0.8*cm))

    kpis = [
        ["20\nStrategies", "£0\nLaunch Cost*", "98%\nWhatsApp Open Rate", "85%\nGross Margin"],
    ]
    kpi_t = Table(kpis, colWidths=[(A4[0]-4.4*cm)/4]*4)
    kpi_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 13),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LINEAFTER", (0, 0), (2, 0), 1, BRAND_RED),
    ]))
    story.append(kpi_t)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("*First 5 strategies require zero budget — organic and affiliate only.", caption))
    story.append(PageBreak())

    # ── HOW YOU GET PAID ─────────────────────────────────────────────────────
    story.append(section("HOW YOU GET PAID — EVERY REVENUE STREAM"))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Grit generates revenue through six distinct streams. The subscription is the engine — "
        "everything else stacks on top. Here is every way money flows into the business.", body))

    streams = [
        ["#", "Revenue Stream", "How It Works", "Monthly Potential"],
        ["1", "Monthly Subscriptions",
         "Core £4.99 / Pro £9.99 / Elite £19.99 — recurring Stripe billing",
         "£9 avg × users"],
        ["2", "Annual Subscriptions",
         "£59.99/year upfront — paid in full, zero monthly churn risk",
         "£5/mo equiv per user"],
        ["3", "Streak Freeze Add-ons",
         "£0.99 each or £3.99 for 5 — impulse buy to protect a streak",
         "£0.50–£2 per active user"],
        ["4", "90-Day Challenge Pack",
         "£49.99 one-time — full structured programme with defined end date",
         "Upsell at onboarding"],
        ["5", "Grit for Teams (B2B)",
         "£7.99/employee/month invoiced annually to HR departments",
         "£480/yr per 5-person team"],
        ["6", "Affiliate Commissions",
         "Recommend supplements, apps, courses — earn 5–30% on purchases",
         "Passive, scales with users"],
    ]
    story.append(tbl(streams, col_widths=[0.8*cm, 3.5*cm, 7.2*cm, 4*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Stripe Payment Flow — How the Money Actually Moves", h2))
    story.append(divider())
    steps = [
        ("User completes onboarding", "WhatsApp conversation → plan delivered → trial starts automatically"),
        ("Day 7 — payment prompt", "Grit sends a Stripe checkout link directly in WhatsApp — one tap to pay"),
        ("Card saved in Stripe", "Stripe handles all billing, retries, receipts, and currency conversion"),
        ("Monthly / annual charge", "Automatic recurring charge — you receive funds in your bank 2–7 days later"),
        ("Failed payment", "Grit auto-messages the user in WhatsApp with a billing update link"),
        ("Cancellation", "User replies CANCEL → Stripe webhook fires → subscription ends at period close"),
    ]
    step_data = [["Step", "What Happens"]] + [[s, d] for s, d in steps]
    story.append(tbl(step_data, col_widths=[4.5*cm, 11*cm]))

    story.append(Spacer(1, 0.4*cm))
    story.append(highlight_box(
        "At 1,000 paying users on Pro: £9,990/month revenue · £1,500 costs · £8,490 profit · 85% margin",
        bg=BRAND_DARK, fg=WHITE
    ))
    story.append(PageBreak())

    # ── FREE TRIAL SYSTEM ────────────────────────────────────────────────────
    story.append(section("FREE TRIAL SYSTEM — HOW TO CONVERT BROWSERS INTO BUYERS"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("The 7-Day Trial Architecture", h2))
    story.append(divider())
    story.append(Paragraph(
        "The trial is not a demo — it is the product. By the time a user reaches day 7, "
        "they have received a personalised PDF plan, 14 check-ins, 7 morning motivation messages, "
        "and started building a streak. They are not being asked to pay for something they haven't "
        "tried. They are being asked to keep something they already rely on.", body))

    trial_days = [
        ["Day", "What Happens", "Purpose"],
        ["Day 0", "User texts the number → onboarding begins immediately", "Hook — zero delay between discovery and value"],
        ["Day 0", "10-question Claude conversation completes in ~5 minutes", "Investment — they've told you everything"],
        ["Day 0", "Personalised 90-day PDF plan lands in their WhatsApp", "WOW moment — tangible value before paying a penny"],
        ["Day 1", "First morning motivation (image + quote) at their local time", "Habit formation begins"],
        ["Day 1", "First daily check-in sent morning and evening", "Accountability loop activated"],
        ["Days 2–6", "Morning motivation + 2 check-ins per day continue", "Streak builds — psychological ownership grows"],
        ["Day 5", "Soft payment nudge: 'Your trial ends in 2 days'", "Early reminder — no pressure"],
        ["Day 7", "Payment link sent with all 4 tier options", "Conversion moment in trusted channel"],
        ["Day 7+", "If no payment — 3-day grace with daily gentle reminder", "Recover hesitant users"],
        ["Day 10", "Final message: 'Your coaching pauses today'", "Loss aversion trigger — FOMO on streak"],
    ]
    story.append(tbl(trial_days, col_widths=[1.8*cm, 8*cm, 5.7*cm]))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Trial Conversion Benchmarks to Target", h2))
    story.append(divider())

    bench = [
        ["Metric", "Industry Average", "Grit Target", "Why Grit Can Beat It"],
        ["Trial → Paid conversion", "15–25%", "35–45%",
         "Value delivered upfront (PDF plan) before paywall"],
        ["Day-7 payment rate", "20%", "40%",
         "Streak psychology + WhatsApp trust + low price point"],
        ["Annual plan uptake", "10–15%", "20–25%",
         "Offer discount framing: 'Save £60 vs monthly'"],
        ["Grace period recovery", "5%", "15%",
         "Personal AI follow-up feels human, not automated"],
    ]
    story.append(tbl(bench, col_widths=[3.5*cm, 3*cm, 2.5*cm, 6.5*cm]))
    story.append(PageBreak())

    # ── YEARLY PRICING ───────────────────────────────────────────────────────
    story.append(section("YEARLY PRICING — THE SINGLE BEST RETENTION TOOL"))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Annual subscribers churn at 5–15% versus 30–40% for monthly. Converting even 20% of your "
        "user base to annual fundamentally transforms your cashflow, your LTV, and your stress level. "
        "Here is how to sell it.", body))

    story.append(Paragraph("Pricing Structure", h2))
    story.append(divider())
    pricing = [
        ["Tier", "Monthly", "Annual", "Annual Saving", "Effective Monthly", "Best For"],
        ["Core", "£4.99", "£39.99", "£19.89 (33%)", "£3.33", "Budget-conscious, long-term committed"],
        ["Pro ★", "£9.99", "£59.99", "£59.89 (50%)", "£5.00", "Primary upsell — best value story"],
        ["Elite", "£19.99", "£149.99", "£89.89 (37%)", "£12.50", "High-income, serious users"],
    ]
    story.append(tbl(pricing, col_widths=[2*cm, 2*cm, 2.2*cm, 3*cm, 3*cm, 4.3*cm]))
    story.append(Paragraph("★ Pro Annual at £59.99 is the anchor offer. Position it as 'less than £1.20 a week.'", caption))

    story.append(Paragraph("When and How to Offer Annual", h2))
    story.append(divider())
    annual_moments = [
        ("End of 7-day trial", "Primary offer moment. 'Lock in your year before the price goes up — £59.99 vs £119.88 monthly.' Urgency + saving."),
        ("30-day streak milestone", "'You've been consistent for 30 days. Lock in another year at half price.' Reward loyalty with a discount."),
        ("Price increase announcement", "'We're increasing prices next month. Lock in current rates for a full year now.' Creates urgency without feeling pushy."),
        ("January / New Year", "'New year, full year. Start 2027 with a committed 12 months.' Seasonal hook with cultural relevance."),
        ("After a missed streak", "'Get back on track. Commit to a full year and we'll give you 3 bonus streak freezes.' Turns a low point into a recommitment."),
    ]
    for moment, desc in annual_moments:
        story.append(KeepTogether([
            Paragraph(f"<b>{moment}</b>", h4),
            Paragraph(desc, body),
        ]))

    story.append(highlight_box(
        "1,000 monthly users × 20% annual conversion = 200 users paying £59.99 upfront = £11,998 cash in one week",
        bg=BRAND_DARK, fg=WHITE
    ))
    story.append(PageBreak())

    # ── 20 MARKETING SUGGESTIONS ─────────────────────────────────────────────
    story.append(section("20 MARKETING STRATEGIES — FROM ZERO TO SCALE"))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "These 20 strategies are ordered from lowest cost to highest cost. "
        "Start at the top. Only move down once the strategy above is working. "
        "Every strategy includes exactly how it makes you money.", body))
    story.append(Spacer(1, 0.2*cm))

    suggestions = [
        (1, "Your Personal Network — The First 50",
         "Message 50 people you know personally. Tell them what you built and offer them a Founding Member rate (£4.99/month locked forever). These first users become your testimonials, your bug reporters, and your first word-of-mouth engine. Don't skip this. Every big consumer product started with a founder texting their contacts.",
         "Direct Stripe payment at £4.99/month. 50 people = £250 MRR from day one with zero marketing spend.",
         "⬤ Easy", "⬤⬤⬤ High"),

        (2, "Reddit — Free Targeted Reach",
         "Post in r/getdisciplined, r/productivity, r/loseit, r/personalfinance, r/Fitness. Don't advertise — share the story. 'I built an AI accountability coach that texts you on WhatsApp. Here's what I learned.' Redditors respond to authenticity and hate ads. Give value first, mention the product second. One good Reddit post can drive 500–2,000 sign-ups in 48 hours.",
         "Free trial sign-ups convert to £9.99/month Pro subscriptions at 35–45% rate.",
         "⬤ Easy", "⬤⬤⬤⬤ Very High"),

        (3, "TikTok — Build Your Own Account",
         "Create a Grit TikTok account. Post daily content: share a user's streak screenshot (with permission), show a morning motivation message, reveal what a 90-day plan looks like, do a '30-day accountability challenge' series where you document your own goal. TikTok's algorithm rewards consistency and authenticity. You need 30 videos before judging results.",
         "Profile link drives WhatsApp trial sign-ups → subscriptions. Zero cost except your time.",
         "⬤⬤ Medium", "⬤⬤⬤⬤ Very High"),

        (4, "Instagram Reels — Screenshot Content",
         "Post weekly 'streak screenshots' from real users — blurred name, big streak number, their reaction. Post morning motivation images from the product with your branding watermark. Create 'before/after accountability' content. Reels showing 'what Grit sent me this morning' are highly shareable and drive organic discovery.",
         "Bio link to WhatsApp trial. Each viral Reel can drive hundreds of free trial sign-ups.",
         "⬤ Easy", "⬤⬤⬤ High"),

        (5, "Micro-Influencer Seeding (Free Product)",
         "Identify 30 creators with 5,000–50,000 followers in fitness, finance, or wellness. DM them offering free Pro access for 30 days in exchange for honest content if they find it useful. No obligation to post. About 30–40% will post organically if the product genuinely helps them — and organic creator content converts 3x better than paid because it is authentic.",
         "20% affiliate commission on every subscriber they refer — ongoing recurring revenue for them and you.",
         "⬤⬤ Medium", "⬤⬤⬤⬤ Very High"),

        (6, "YouTube Creators — Long-Form Reviews",
         "Target YouTube creators in the self-improvement, productivity, and fitness spaces with 20,000–500,000 subscribers. Offer a paid sponsorship slot (£200–£1,500 per video depending on size) plus 20% affiliate commission. YouTube viewers have longer attention spans and higher intent — they watch a 10-minute review and then immediately try the product.",
         "Flat fee per video (your cost) + 20% affiliate on all subscribers they drive (ongoing income for creator, reduced CAC for you).",
         "⬤⬤⬤ Hard", "⬤⬤⬤⬤ Very High"),

        (7, "Podcast Sponsorships",
         "Sponsor 3–5 podcasts in the fitness, personal development, or entrepreneurship space. Podcast audiences are loyal and trust host recommendations more than almost any other channel. Negotiate a host-read ad with a unique discount code (GRIT30 = 30 days free instead of 7). Track performance per podcast. Average podcast CPM (cost per thousand listeners) is £15–£25 — cheaper than most digital channels.",
         "Unique promo codes track conversions. Pay per episode or negotiate performance-based deals with smaller shows.",
         "⬤⬤ Medium", "⬤⬤⬤ High"),

        (8, "Challenge a Friend — Built-In Viral Loop",
         "When a user completes day 7 of their trial, Grit automatically sends them a WhatsApp message: 'You've been consistent for a week. Know someone who needs this? Send them this link — you both get an extra free week.' Each user who refers one friend doubles the value of that acquisition. The product has this mechanic built in already.",
         "New users enter the same trial funnel → convert at 35–45% → become recurring subscribers.",
         "⬤ Easy", "⬤⬤⬤⬤ Very High"),

        (9, "Milestone Shareable Graphics — Passive Virality",
         "Every time a user hits 7, 14, 30, or 90 days, Grit sends them a branded shareable graphic in WhatsApp: 'I just hit 30 days straight with Grit.' The image has your brand, a short link, and their streak number. When they post it to Stories or TikTok — and they will — every follower who sees it is a potential free trial sign-up. This costs you nothing and happens automatically.",
         "Organic referrals into the free trial funnel → subscription conversions at 35–45%.",
         "⬤ Easy", "⬤⬤⬤⬤ Very High"),

        (10, "Product Hunt Launch",
         "Submit Grit to Product Hunt on a Tuesday or Wednesday (highest traffic days). Prepare a compelling description, screenshots of the WhatsApp conversation flow, and the PDF plan example. Rally your founding members and network to upvote on launch day. A top-5 Product Hunt finish drives 500–3,000 sign-ups in 24 hours and gets you covered by tech newsletters globally.",
         "Free trial sign-ups from a highly engaged, early-adopter audience who talk about products they love.",
         "⬤⬤ Medium", "⬤⬤⬤ High"),

        (11, "Email Newsletter Sponsorships",
         "Newsletters in the productivity, fitness, and finance spaces (Morning Brew, Ali Abdaal's newsletter, Finimize) have highly engaged audiences who click and act on recommendations. Sponsor a single issue. Negotiate a flat fee (£200–£2,000 depending on list size) and track clicks with a unique URL. Newsletter audiences convert at 2–4x the rate of social media because they opted in to read content.",
         "Unique URL tracks sign-ups. Flat sponsorship fee is your cost — ongoing subscription revenue is your return.",
         "⬤⬤ Medium", "⬤⬤⬤ High"),

        (12, "SEO Content Marketing — Long Game",
         "Create a simple blog or resource page targeting search terms like 'best accountability app', 'how to stick to your goals', 'AI life coach', 'WhatsApp productivity tools'. Write genuinely useful content — 'How to build a habit that actually sticks (the 90-day science)' — and link to Grit naturally. SEO takes 3–6 months to gain traction but then drives free sign-ups indefinitely.",
         "Organic Google traffic → WhatsApp trial sign-ups → subscriptions. Zero ongoing cost once content is published.",
         "⬤⬤⬤ Hard", "⬤⬤⬤ High (long-term)"),

        (13, "TikTok Paid Ads — Amplify What Works Organically",
         "Once you have TikTok organic content that performs well (100K+ views), put paid budget behind it. TikTok ads on already-proven content convert significantly better than purpose-made ad creative. Start with £10–£20/day, target 18–35, interests: fitness, self-improvement, productivity, journaling. Scale only what has a proven CAC below £15.",
         "Paid trial sign-ups → subscription conversions. Track CAC per ad set. Scale profitable sets, kill everything else.",
         "⬤⬤⬤ Hard", "⬤⬤⬤⬤ Very High (at scale)"),

        (14, "Meta (Facebook/Instagram) Retargeting",
         "Install a Meta pixel on your landing page (if you build one) or use UTM links. Retarget people who clicked your WhatsApp link but didn't complete sign-up. These are warm leads — they showed intent. Retargeting CPCs are typically 60–70% cheaper than cold prospecting. Show them a testimonial ad or a '30-day streak' screenshot. Bring them back.",
         "Retargeted trial sign-ups → subscriptions. Retargeting ROI is typically 3–5x better than cold ads.",
         "⬤⬤ Medium", "⬤⬤⬤ High"),

        (15, "January 'New Year' Campaign",
         "January is the single best month in the year for accountability and habit products. 'New Year's resolution' search volume spikes 400%. Plan a dedicated January campaign: 'New Year Challenge — 90 days with Grit, starting January 1st.' Push this through every channel simultaneously: creators go live first week of January, TikTok content scheduled, Reddit posts, email newsletter sponsorships. Offer the annual plan heavily in January — people are motivated to commit.",
         "Subscription spike in January. Push annual plans hard — lock users in for 12 months when motivation is highest.",
         "⬤⬤ Medium", "⬤⬤⬤⬤⬤ Exceptional"),

        (16, "Corporate Wellness Partnerships",
         "Approach HR managers and People teams at companies with 50–500 employees. Position Grit as an employee wellness benefit: 'Give your team an AI accountability coach for less than a daily coffee per person.' Companies have dedicated wellness budgets and make annual purchasing decisions. One deal with a 100-person company at £7.99/employee/month = £799/month guaranteed with zero churn for 12 months.",
         "Annual B2B contracts invoiced directly. No per-user acquisition cost. Revenue is guaranteed for 12 months.",
         "⬤⬤⬤ Hard", "⬤⬤⬤⬤ Very High"),

        (17, "Gym and PT Partnerships",
         "Approach personal trainers and gyms directly. Offer them a white-label or co-branded version: 'Your clients get Grit check-ins between sessions — branded as your coaching.' The PT charges their clients more for the enhanced service. You split revenue 50/50. The PT has no tech work to do. You get a distribution channel with zero marketing spend.",
         "Revenue split with PT/gym partner. You take 50% of the subscription per client they bring on. Partner takes 50%.",
         "⬤⬤ Medium", "⬤⬤⬤ High"),

        (18, "App Store Launch (Phase 2 Only)",
         "At 5,000+ users, build a companion web app or lightweight iOS/Android app. NOT a replacement for WhatsApp — a supplement. Users who want to see their streak history, update their goals, or view their 90-day plan in a visual dashboard. The app drives engagement and reduces churn but is NOT the primary onboarding channel. Build this only after core product is proven.",
         "App drives retention which increases LTV. Does not generate direct revenue — protects subscription revenue already earned.",
         "⬤⬤⬤⬤ Very Hard", "⬤⬤⬤ Medium (retention focus)"),

        (19, "Press and Earned Media",
         "Pitch your story to journalists at the Guardian, Forbes, Business Insider, Wired, and trade publications covering AI and wellness. The angle writes itself: 'The AI coach that texts you every day on WhatsApp — and why 10,000 people say it changed their life.' Include your retention data (if strong), real user testimonials, and the 'no app download' angle as the hook. Journalists love contrarian stories — this one challenges the app-first assumption.",
         "Earned media drives awareness and trial sign-ups at zero cost. A single Forbes article can drive 2,000–10,000 new sign-ups.",
         "⬤⬤⬤ Hard", "⬤⬤⬤⬤ Very High"),

        (20, "Accountability Partner Matching — Community Revenue",
         "At scale (10,000+ users), launch an opt-in 'Accountability Partner' matching service. Grit pairs two users with similar goals and timezone. They receive anonymous weekly updates about each other's progress via Claude. Charge £2/month extra for this feature as an add-on. Social accountability dramatically improves retention — paired users churn at half the rate of solo users. This feature pays for itself many times over.",
         "£2/month add-on per paired user. At 10,000 users with 30% uptake = £6,000 additional MRR from zero extra infrastructure cost.",
         "⬤⬤ Medium", "⬤⬤⬤⬤ Very High"),
    ]

    for num, title, body_text, how_paid, diff, impact in suggestions:
        story.append(suggestion_block(num, title, body_text, how_paid, diff, impact))

    story.append(PageBreak())

    # ── LAUNCH TIMELINE ──────────────────────────────────────────────────────
    story.append(section("LAUNCH TIMELINE — ZERO TO LIVE IN 30 DAYS"))
    story.append(Spacer(1, 0.3*cm))

    timeline = [
        ["Week", "Your Actions", "Marketing Actions", "Revenue Target"],
        ["Week 1\n(Now)",
         "Sign up: Stripe, Meta, Anthropic, Railway, Cloudflare. Get SIM card. Paste API keys.",
         "Message 50 personal contacts. Offer Founding Member rate.",
         "£250 MRR\n(50 users)"],
        ["Week 2",
         "Test full product flow. Fix any issues. Set up Stripe products and pricing.",
         "Post first TikTok and Instagram content. Submit to Product Hunt. Post on Reddit.",
         "£500 MRR\n(100 users)"],
        ["Week 3",
         "Onboard first 10 micro-influencers with free Pro access. Set up affiliate tracking.",
         "First creator content goes live. Reddit posts in 3 subreddits. Email 5 newsletters.",
         "£1,500 MRR\n(150 users)"],
        ["Week 4",
         "Review retention data. Identify top-performing channels. Double down.",
         "Annual plan push to all trial users. Second wave of creator outreach.",
         "£3,000 MRR\n(300 users)"],
        ["Month 2",
         "Add streak freeze upsell. Set up referral mechanics.",
         "First paid creator deal. TikTok ad test with £10/day. Podcast outreach.",
         "£7,500 MRR\n(750 users)"],
        ["Month 3",
         "Review all unit economics. Prepare B2B deck.",
         "Mid-tier creator outreach. First corporate wellness pitch.",
         "£15,000 MRR\n(1,500 users)"],
        ["Month 6",
         "Annual plan campaign. Consider press outreach.",
         "Full paid social. Multiple creators live. PR pitch drafted.",
         "£45,000 MRR\n(4,500 users)"],
        ["Month 12",
         "App Store companion app scoped. Accountability partner feature.",
         "January campaign live. Press coverage targeted.",
         "£90,000 MRR\n(9,000 users)"],
    ]
    story.append(tbl(timeline, col_widths=[1.8*cm, 4.5*cm, 5.5*cm, 3.7*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Priority Stack — What to Do First", h2))
    story.append(divider())
    priority = [
        ["Priority", "Action", "Why First"],
        ["#1", "Get API keys live and product working", "Nothing else matters until this works"],
        ["#2", "Sign up 50 founding members from your network", "Real users, real feedback, real revenue immediately"],
        ["#3", "Post on Reddit (r/getdisciplined, r/Fitness)", "Free, targeted, high-intent audience, immediate results"],
        ["#4", "Seed 10 micro-influencers with free access", "Organic creator content is your highest-converting channel"],
        ["#5", "Set up annual pricing in Stripe", "One conversation with an existing user can lock in £59.99 upfront"],
        ["#6", "Build TikTok account with daily content", "Compounding organic reach — takes time but costs nothing"],
        ["#7", "Referral mechanic active in the product", "Every user becomes a potential acquisition channel"],
    ]
    story.append(tbl(priority, col_widths=[1.8*cm, 6*cm, 7.7*cm]))
    story.append(PageBreak())

    # ── SUMMARY ──────────────────────────────────────────────────────────────
    story.append(section("FINAL SUMMARY — THE MARKETING IN ONE PAGE"))
    story.append(Spacer(1, 0.3*cm))

    story.append(highlight_box("The Rule: Prove Retention Before Spending Money.", bg=BRAND_RED, fg=WHITE, size=13))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        "The single biggest mistake early consumer subscription businesses make is spending money on "
        "acquisition before they know users stick. If you acquire 1,000 users and 900 cancel in month 1, "
        "every pound you spent was wasted. Grit's design makes retention highly achievable — but prove it "
        "first with your founding members before scaling spend.", body))

    story.append(Paragraph("Your Marketing Stack by Phase", h2))
    story.append(divider())

    phases = [
        ["Phase", "Duration", "Channels Active", "Monthly Budget", "Target MRR"],
        ["Prove", "Months 1–2", "Network, Reddit, TikTok organic, Product Hunt", "£0–£500", "£0–£3,000"],
        ["Build", "Months 3–4", "+ Micro-influencers, Instagram, Referral loop", "£500–£2,000", "£3,000–£15,000"],
        ["Scale", "Months 5–8", "+ Mid-tier creators, Paid social, Podcasts", "£2,000–£8,000", "£15,000–£60,000"],
        ["Dominate", "Months 9–12", "+ PR, Corporate, App launch, January campaign", "£8,000–£20,000", "£60,000–£100,000+"],
    ]
    story.append(tbl(phases, col_widths=[2*cm, 2.5*cm, 5.5*cm, 2.8*cm, 2.7*cm]))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("The Five Numbers That Matter", h2))
    story.append(divider())

    numbers_data = [
        ["Metric", "Target", "If You Hit This..."],
        ["Month-2 retention", ">55%", "Your LTV exceeds £80 and paid ads become viable"],
        ["Trial-to-paid conversion", ">35%", "Your CAC stays below £18 even with paid channels"],
        ["Annual plan uptake", ">20%", "Your cashflow becomes predictable and stress-free"],
        ["LTV:CAC ratio", ">4:1", "You can scale paid acquisition confidently"],
        ["NPS score (ask at day 30)", ">50", "Word of mouth becomes a meaningful acquisition channel"],
    ]
    story.append(tbl(numbers_data, col_widths=[4*cm, 2.5*cm, 9*cm]))

    story.append(Spacer(1, 0.5*cm))
    story.append(highlight_box(
        "The infrastructure is built. The plan is written. The only thing left is execution.\n"
        "Start with your network. Post on Reddit tonight. The rest follows.",
        bg=BRAND_DARK, fg=WHITE, size=11
    ))

    story.append(Paragraph(
        "Document prepared June 2026 · Grit AI Accountability Coach · brettyryangit/Claude on GitHub",
        footer_note
    ))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
