from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.units import inch

BRAND_DARK = colors.HexColor("#0f0f1a")
BRAND_RED = colors.HexColor("#e94560")
BRAND_GREY = colors.HexColor("#555555")
BRAND_LIGHT = colors.HexColor("#f5f5f5")
WHITE = colors.white

OUTPUT_PATH = "/home/user/Claude/Grit_Business_Document.pdf"


def header_footer(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(BRAND_DARK)
    canvas.rect(0, A4[1] - 1.2 * cm, A4[0], 1.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(2 * cm, A4[1] - 0.85 * cm, "GRIT — AI Accountability Coach")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 0.85 * cm, "Confidential Business Document — June 2026")
    # Footer
    canvas.setFillColor(BRAND_DARK)
    canvas.rect(0, 0, A4[0], 0.9 * cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, 0.3 * cm, "Confidential — Not for Distribution")
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

    styles = getSampleStyleSheet()

    cover_title = ParagraphStyle("CoverTitle", fontSize=42, textColor=WHITE,
        alignment=TA_CENTER, fontName="Helvetica-Bold", leading=50, spaceAfter=8)
    cover_sub = ParagraphStyle("CoverSub", fontSize=16, textColor=BRAND_RED,
        alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=6)
    cover_meta = ParagraphStyle("CoverMeta", fontSize=11, textColor=colors.HexColor("#aaaaaa"),
        alignment=TA_CENTER, fontName="Helvetica")

    h1 = ParagraphStyle("H1", fontSize=20, textColor=WHITE, fontName="Helvetica-Bold",
        spaceBefore=6, spaceAfter=10, leading=26, backColor=BRAND_DARK,
        leftIndent=-0.5*cm, rightIndent=-0.5*cm, borderPad=8)
    h2 = ParagraphStyle("H2", fontSize=14, textColor=BRAND_DARK, fontName="Helvetica-Bold",
        spaceBefore=14, spaceAfter=6, borderPadding=(0, 0, 2, 0))
    h3 = ParagraphStyle("H3", fontSize=11, textColor=BRAND_RED, fontName="Helvetica-Bold",
        spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("Body", fontSize=10, textColor=colors.HexColor("#222222"),
        fontName="Helvetica", leading=16, spaceAfter=8, alignment=TA_JUSTIFY)
    bullet = ParagraphStyle("Bullet", fontSize=10, textColor=colors.HexColor("#222222"),
        fontName="Helvetica", leading=15, spaceAfter=4, leftIndent=16, bulletIndent=4)
    caption = ParagraphStyle("Caption", fontSize=8, textColor=BRAND_GREY,
        fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=6)
    footer_note = ParagraphStyle("FooterNote", fontSize=8, textColor=BRAND_GREY,
        fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceBefore=20)

    TABLE_HEADER = [BRAND_DARK, WHITE, ("Helvetica-Bold", 9)]
    TABLE_ROW_A = colors.HexColor("#f9f9f9")
    TABLE_ROW_B = WHITE

    def table(data, col_widths=None):
        t = Table(data, colWidths=col_widths, repeatRows=1)
        row_colors = []
        for i in range(1, len(data)):
            c = TABLE_ROW_A if i % 2 == 1 else TABLE_ROW_B
            row_colors.append(("BACKGROUND", (0, i), (-1, i), c))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ROWBACKGROUND", (0, 1), (-1, -1), [TABLE_ROW_A, TABLE_ROW_B]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            *row_colors,
        ]))
        return t

    def divider():
        return HRFlowable(width="100%", thickness=1.5, color=BRAND_RED, spaceAfter=10, spaceBefore=4)

    def section_title(text):
        return Paragraph(f"&nbsp;&nbsp;{text}", h1)

    story = []

    # ── COVER PAGE ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 3.5 * cm))

    cover_block = Table(
        [[Paragraph("GRIT", cover_title)],
         [Paragraph("AI Accountability Coach", cover_sub)],
         [Spacer(1, 0.3 * cm)],
         [Paragraph("Business Overview &amp; Investment Case", cover_meta)],
         [Paragraph("Confidential Document — June 2026", cover_meta)]],
        colWidths=[A4[0] - 4.4 * cm],
    )
    cover_block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("LEFTPADDING", (0, 0), (-1, -1), 30),
        ("RIGHTPADDING", (0, 0), (-1, -1), 30),
    ]))
    story.append(cover_block)
    story.append(Spacer(1, 1.5 * cm))
    story.append(HRFlowable(width="100%", thickness=3, color=BRAND_RED))
    story.append(Spacer(1, 1 * cm))

    taglines = [
        "WhatsApp-native · AI-powered · Zero app download required",
        "Built on Claude AI · Deployed globally · Profitable from month 2",
    ]
    for t in taglines:
        story.append(Paragraph(t, ParagraphStyle("Tag", fontSize=11, textColor=BRAND_GREY,
            alignment=TA_CENTER, fontName="Helvetica", spaceAfter=6)))

    story.append(Spacer(1, 3 * cm))

    kpi_data = [
        ["85%\nGross Margin", "£9.99\nPrimary Price Point", "£279K\nYear 1 Profit (Conservative)", "5:1\nLTV:CAC Ratio"],
    ]
    kpi_table = Table(kpi_data, colWidths=[(A4[0] - 4.4*cm)/4]*4)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 13),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("LINEAFTER", (0, 0), (2, -1), 1, BRAND_RED),
    ]))
    story.append(kpi_table)
    story.append(PageBreak())

    # ── PAGE 1 — WHAT GRIT IS ───────────────────────────────────────────────
    story.append(section_title("PAGE 1 — WHAT GRIT IS AND WHY IT EXISTS"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("The Problem", h2))
    story.append(divider())
    story.append(Paragraph(
        "Millions of people set goals and never achieve them. Not because they lack desire — but because they lack "
        "consistent accountability. The self-improvement industry is worth over $13 billion globally and growing, "
        "yet the single most common reason people fail their goals remains unchanged: no one is checking on them.", body))

    story.append(Paragraph("Existing solutions fall into three categories, all with fundamental flaws:", body))

    problems = [
        ("<b>Personal trainers and life coaches</b>", "Cost £40–£150 per session. Inaccessible to the majority. Professional accountability is a privilege reserved for those who can afford it."),
        ("<b>Habit-tracking apps</b>", "Require the user to self-report and return to the app voluntarily. No external nudge. 80% of users stop using them within 30 days."),
        ("<b>Social accountability</b>", "Telling a friend your goals works only when that friend remembers and follows up. In practice, it fades within weeks."),
    ]
    for title, desc in problems:
        story.append(Paragraph(f"• {title} — {desc}", bullet))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("The Opportunity", h2))
    story.append(divider())
    story.append(Paragraph(
        "WhatsApp has 2.7 billion active users globally. It is the most opened app on most people's phones. "
        "It requires no new download, no new login, no new habit. People already check it reflexively, multiple times a day.", body))
    story.append(Paragraph(
        "Grit puts an AI accountability coach directly inside WhatsApp — making professional-grade accountability "
        "available to anyone, anywhere, for less than the cost of a single coffee per week.", body))

    story.append(Paragraph("What Grit Does", h2))
    story.append(divider())

    steps = [
        ("Step 1", "User discovers Grit via a creator, ad, or word of mouth and taps a WhatsApp link"),
        ("Step 2", "10-question onboarding conversation via Claude AI — takes under 5 minutes"),
        ("Step 3", "Personalised 90-day plan generated and delivered as a branded PDF into their WhatsApp chat"),
        ("Step 4", "7-day free trial begins — morning motivation image + quote daily, 2x daily check-ins"),
        ("Step 5", "Streak tracking starts. Milestones celebrated. AI tone adapts based on their responses"),
        ("Step 6", "Stripe payment link sent at end of trial. Subscription activates. Coaching continues"),
    ]
    step_data = [["Step", "What Happens"]] + [[s, d] for s, d in steps]
    story.append(table(step_data, col_widths=[2.5*cm, 13*cm]))
    story.append(PageBreak())

    # ── PAGE 2 — WHY IT WILL WORK ───────────────────────────────────────────
    story.append(section_title("PAGE 2 — WHY THIS WILL WORK"))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Five Reasons Grit Succeeds Where Others Have Failed", h2))
    story.append(divider())

    reasons = [
        ("1. Zero Friction Onboarding",
         "Every competitor requires app download, account creation, profile setup, and interface navigation before any value is delivered. Grit's onboarding is a WhatsApp conversation. The user is already in the app. Five minutes later they have a PDF plan — before spending a single penny. This makes Grit's cost of acquisition structurally lower than every app-based competitor."),
        ("2. WhatsApp's 98% Open Rate",
         "Email open rates average 20–25%. Push notification click rates sit at 4–8%. WhatsApp message open rates exceed 98%. When Grit sends a morning message, users see it. When it sends a check-in, users respond. The channel does what no app notification can."),
        ("3. AI Makes It Genuinely Personal",
         "Generic apps fail because users feel like a number. Grit uses Claude AI to remember every onboarding answer, every check-in reply, and every conversation. The AI adjusts tone, language, and suggestions based on what it knows about that specific person. This personalisation is the core product — not a feature."),
        ("4. Streak Psychology Drives Retention",
         "Duolingo built a $6 billion business largely on streak mechanics. The fear of losing a streak built over weeks is one of the most powerful retention tools in consumer technology. Grit embeds this from day one. Users do not cancel because cancelling means losing their streak, their history, and their plan."),
        ("5. Business Model Aligns With User Success",
         "Grit only makes money when users stay subscribed. Users only stay when the product works. This alignment means the incentive is always to make the AI better and the outcomes more real. There is no dark pattern here — no addictive scroll feed, no engagement farming. The product succeeds when the user succeeds."),
    ]

    for title, desc in reasons:
        story.append(KeepTogether([
            Paragraph(title, h3),
            Paragraph(desc, body),
        ]))

    story.append(PageBreak())

    # ── PAGE 3 — BUSINESS MODEL ─────────────────────────────────────────────
    story.append(section_title("PAGE 3 — THE BUSINESS MODEL"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Subscription Tiers", h2))
    story.append(divider())

    tier_data = [
        ["Tier", "Monthly Price", "Annual Equivalent", "Target User"],
        ["Core", "£4.99/month", "£59.88", "Casual users, price-sensitive"],
        ["Pro ★", "£9.99/month", "£119.88", "Committed users — primary tier"],
        ["Elite", "£19.99/month", "£239.88", "Power users, high-income"],
        ["Annual", "£59.99/year", "£5.00/month", "Users wanting best value"],
    ]
    story.append(table(tier_data, col_widths=[3*cm, 3.5*cm, 3.5*cm, 6.5*cm]))
    story.append(Paragraph("★ Pro at £9.99/month is the anchor tier. Cheaper than one gym class, one PT session, or most streaming services.", caption))

    story.append(Paragraph("Trial Model", h2))
    story.append(divider())
    story.append(Paragraph(
        "Every new user receives 7 days completely free with no card required. During those 7 days they experience "
        "the full product. At the end of 7 days, Grit sends a payment link directly in WhatsApp. The conversion "
        "happens in the channel where the relationship has already been built.", body))

    story.append(Paragraph("Gross Margins Per Tier", h2))
    story.append(divider())

    margin_data = [
        ["Tier", "Revenue", "Cost Per User", "Gross Profit", "Margin"],
        ["Core (£4.99)", "£4.99", "£1.25", "£3.74", "75%"],
        ["Pro (£9.99)", "£9.99", "£1.50", "£8.49", "85%"],
        ["Elite (£19.99)", "£19.99", "£1.75", "£18.24", "91%"],
        ["Annual (£59.99)", "£5.00 equiv", "£1.25", "£3.75", "75%"],
    ]
    story.append(table(margin_data, col_widths=[4*cm, 3*cm, 3*cm, 3*cm, 2.5*cm]))
    story.append(Paragraph("SaaS businesses typically target 70–80% gross margin. Grit exceeds this at the Pro tier from day one.", caption))

    story.append(Paragraph("Additional Revenue Streams (Phase 2)", h2))
    story.append(divider())

    addl = [
        ["Streak Freeze Packs", "£0.99 each / £3.99 for 5", "High-engagement users pay to protect long streaks"],
        ["90-Day Challenge Package", "£49.99 one-time", "Defined programme for users wanting a clear endpoint"],
        ["Affiliate Commissions", "Variable", "Recommend relevant products (supplements, apps, courses)"],
        ["Grit for Teams (B2B)", "£7.99/employee/month", "Corporate wellness — annual contracts, zero churn risk"],
    ]
    addl_data = [["Revenue Stream", "Price", "Notes"]] + addl
    story.append(table(addl_data, col_widths=[4.5*cm, 4*cm, 7*cm]))
    story.append(PageBreak())

    # ── PAGE 4 — FINANCIALS ─────────────────────────────────────────────────
    story.append(section_title("PAGE 4 — COSTS AND FINANCIAL PROJECTIONS"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Cost Per User Per Month", h2))
    story.append(divider())

    cost_data = [
        ["Item", "Cost", "Notes"],
        ["WhatsApp conversations", "£0.90–£1.50", "Meta Cloud API utility pricing"],
        ["Claude AI (Haiku + Sonnet)", "£0.05–£0.15", "Haiku for check-ins, Sonnet for onboarding"],
        ["Server and database", "£0.01–£0.05", "Railway, scales linearly with users"],
        ["PDF storage and delivery", "£0.01", "Cloudflare R2, near zero cost"],
        ["Total COGS per user", "£1.00–£1.75", "Blended average £1.25 — falls to £0.80 at scale"],
    ]
    story.append(table(cost_data, col_widths=[5*cm, 3.5*cm, 7*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Fixed Monthly Costs at Launch", h2))
    story.append(divider())

    fixed_data = [
        ["Item", "Monthly Cost"],
        ["Railway hosting and PostgreSQL", "£5"],
        ["Cloudflare R2 storage", "£0 (free tier)"],
        ["Domain and SSL", "£1"],
        ["Total fixed costs", "£6/month"],
    ]
    story.append(table(fixed_data, col_widths=[10*cm, 5.5*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("12-Month Financial Projections", h2))
    story.append(divider())
    story.append(Paragraph(
        "Assumptions: Launch month 1, creator outreach month 2, 4–6 micro-influencer partnerships by month 3. "
        "Mix: 65% Pro, 25% Core, 10% Elite.", body))

    proj_data = [
        ["Month", "New Signups", "Paying Users", "MRR", "Costs", "Profit"],
        ["1", "50", "25", "£225", "£350", "-£125"],
        ["2", "200", "150", "£1,350", "£550", "£800"],
        ["3", "500", "500", "£4,500", "£1,200", "£3,300"],
        ["4", "800", "1,000", "£9,000", "£2,200", "£6,800"],
        ["6", "1,200", "2,500", "£22,500", "£4,800", "£17,700"],
        ["9", "1,500", "4,800", "£43,200", "£8,500", "£34,700"],
        ["12", "2,500", "8,200", "£73,800", "£13,500", "£60,300"],
    ]
    story.append(table(proj_data, col_widths=[2*cm, 2.5*cm, 3*cm, 3*cm, 2.5*cm, 2.5*cm]))
    story.append(Paragraph("Year 1 Total Profit: ~£279,000 | Month 12 ARR: £885,600", caption))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Unit Economics", h2))
    story.append(divider())

    unit_data = [
        ["Metric", "Value"],
        ["Average Revenue Per User (ARPU)", "£9.00/month"],
        ["Customer Acquisition Cost (CAC) via creators", "£10–18"],
        ["Average Customer Lifetime", "11 months"],
        ["Lifetime Value (LTV)", "£85–£99"],
        ["LTV:CAC Ratio", "5:1–7:1 (target minimum 3:1)"],
        ["Payback Period", "6–8 weeks"],
    ]
    story.append(table(unit_data, col_widths=[9*cm, 6.5*cm]))
    story.append(PageBreak())

    # ── PAGE 5 — MARKETING ──────────────────────────────────────────────────
    story.append(section_title("PAGE 5 — MARKETING AND GO-TO-MARKET PLAN"))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Why Creator Marketing Is the Primary Channel", h2))
    story.append(divider())
    story.append(Paragraph(
        "Traditional digital advertising requires significant testing budgets and targets users with intent signals "
        "that are difficult to define for a novel product. Creator marketing solves both problems: pre-built "
        "audiences who trust the recommendation, and a product that demonstrates itself — 'I let an AI text me "
        "every day for 30 days' is a video concept creators will want to make.", body))

    story.append(Paragraph("Three-Phase Creator Strategy", h2))
    story.append(divider())

    phases = [
        ["Phase", "Timeline", "Creator Size", "Budget", "Target Outcome"],
        ["1 — Seeding", "Months 1–3", "10K–100K followers", "£2,000–£5,000", "15–20 creators, 20% affiliate"],
        ["2 — Amplify", "Months 3–6", "100K–500K followers", "£500–£2,000/video", "3–5 dedicated videos"],
        ["3 — Scale", "Month 6+", "All tiers + paid ads", "Budget from revenue", "Meta + TikTok retargeting"],
    ]
    story.append(table(phases, col_widths=[2.5*cm, 2.5*cm, 3.5*cm, 3*cm, 4*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Affiliate Commission Structure", h2))
    story.append(divider())

    aff_data = [
        ["Creator Tier", "Followers", "Commission", "Earnings per 300 Users"],
        ["Standard Affiliate", "Any", "15% recurring", "£450/month ongoing"],
        ["Partner Creator", "50K–500K", "20% recurring", "£600/month ongoing"],
        ["Anchor Partner", "1M+", "25% + flat fee", "£750/month + upfront"],
    ]
    story.append(table(aff_data, col_widths=[3.5*cm, 3*cm, 3.5*cm, 5.5*cm]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Built-In Viral Mechanics", h2))
    story.append(divider())

    viral = [
        ("<b>The Screenshot Loop</b>", "Every morning motivation image is watermarked with the Grit brand and short link. Users screenshot and share to Stories — free impressions at zero cost."),
        ("<b>Milestone Shareable Graphics</b>", "At 7, 14, 30, and 90-day streaks, Grit sends a branded shareable card. 'I just hit 30 days with Grit' creates authentic social proof no paid ad can replicate."),
        ("<b>Referral Programme</b>", "Users refer a friend via personal link — both get one free month. Social accountability is twice as powerful as solo accountability."),
        ("<b>Challenge a Friend</b>", "Invite one friend to a shared 30-day challenge. Two users acquired for the cost of one. Paired users have substantially lower churn."),
    ]
    for title, desc in viral:
        story.append(Paragraph(f"• {title} — {desc}", bullet))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("What Would Not Work — and Why", h2))
    story.append(divider())

    wont_work = [
        ("App Store launch without WhatsApp",
         "Minimum £50–150K development cost, 3–6 month build time, £25–50 per install acquisition cost versus £10–18 via creators. The no-download advantage is Grit's single most powerful competitive moat."),
        ("Targeting all demographics equally before data",
         "Spending marketing budget broadly before retention data exists burns capital. Identify which goal category retains best and double down before expanding."),
        ("Building features before proving retention",
         "Adding community feeds or video content before the core check-in loop is proven drives complexity without answering the fundamental question: do users stick?"),
    ]
    for title, desc in wont_work:
        story.append(KeepTogether([
            Paragraph(title, h3),
            Paragraph(desc, body),
        ]))

    story.append(PageBreak())

    # ── PAGE 6 — RECOMMENDATIONS ────────────────────────────────────────────
    story.append(section_title("PAGE 6 — RECOMMENDATIONS"))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Six Things That Would Meaningfully Accelerate This Business", h2))
    story.append(divider())

    recs = [
        ("1. Build a Founding Members Offer Before Launch",
         "Reach out personally to 50–100 people in your network. Offer a Founding Member rate — £4.99/month locked for life — in exchange for honest feedback and a testimonial. This generates early revenue, creates invested beta testers, builds social proof before approaching creators, and creates a compelling story for partnerships."),
        ("2. Choose One Niche for Launch and Own It",
         "Grit is built to serve all goal categories, but launching as everything to everyone is the fastest way to be nothing to anyone. Fitness is the strongest launch niche: visceral and visual progress, enormous creator ecosystem, binary check-in compliance, and the PDF plan is a high-perceived-value deliverable that justifies the trial immediately."),
        ("3. Publish Retention Data Publicly From Month 2",
         "Most apps hide their retention numbers because they are poor. If Grit works — and the design gives it every reason to — publish monthly cohort data openly. '65% of Grit users still active at 60 days versus the 20% industry average' is a headline that journalists, newsletters, and potential investors find irresistible."),
        ("4. Create a Coach Persona With a Name and Personality",
         "Consider developing a named AI coach character rather than a faceless app. Users form attachments to characters faster than to brands. Examples: Duolingo's Duo, Replika, Woebot. A coach with a defined backstory gives creators a character to introduce and gives users a relationship to invest in. Cost to implement: zero."),
        ("5. Approach One Corporate Employer Partnership in Month 4",
         "Employee wellness is a £4.2 billion industry in the UK alone. A B2B 'Grit for Teams' offer at £7.99 per employee per month, invoiced annually, opens a revenue channel with zero churn risk and no per-user acquisition cost. Five companies at 50 employees each equals 250 guaranteed paying users and £23,970 guaranteed annual revenue from a single sales conversation."),
        ("6. Register the Business and IP Correctly Before Scale",
         "Before approaching investors or large creators: register a limited company, publish terms of service and privacy policy (required for WhatsApp Business API approval and GDPR compliance), file a trademark application in key markets, and document data processing agreements with all sub-processors. None of these are glamorous. All become urgent at exactly the wrong moment if not handled in advance."),
    ]

    for title, desc in recs:
        story.append(KeepTogether([
            Paragraph(title, h3),
            Paragraph(desc, body),
            Spacer(1, 0.2*cm),
        ]))

    story.append(PageBreak())

    # ── PAGE 7 — EXECUTIVE SUMMARY ──────────────────────────────────────────
    story.append(section_title("PAGE 7 — EXECUTIVE SUMMARY AND INVESTMENT CASE"))
    story.append(Spacer(1, 0.3*cm))

    summary_items = [
        ("What it is",
         "Grit is a WhatsApp-native AI accountability coaching service. Users define their goals, receive a personalised 90-day PDF plan, and get daily check-ins, morning motivation, and streak tracking — entirely through WhatsApp, with no app to download."),
        ("Why now",
         "Three trends converge at this moment: AI language models have crossed the quality threshold where conversation is genuinely useful; WhatsApp Business API has matured and become accessible to independent developers; and post-pandemic culture has created a generational wave of people seeking self-improvement tools, with app fatigue making the no-download approach more valuable than ever."),
        ("Why it will work",
         "Zero friction onboarding. A channel with 98% open rates. AI personalisation that makes every user feel individually coached. Streak psychology that makes cancellation feel costly. Pricing accessible to nearly anyone at £9.99/month. And a creator marketing channel that allows rapid, measurable, cost-controlled growth."),
        ("Why it is defensible",
         "The moat is not the technology — any competitor can access Claude's API. The moat is the data. Every user conversation, every check-in response, every streak pattern becomes proprietary data that improves the product over time. A competitor starting today starts without that data. The longer Grit runs, the harder it becomes to replicate."),
        ("The numbers",
         "Launch cost under £500. Monthly running cost under £10 until first 50 paying users. Gross margin 85% at Pro tier. Conservative 12-month profit of £279,000. Moderate scenario £420,000. A single viral creator moment makes both figures look conservative."),
    ]

    for title, desc in summary_items:
        story.append(KeepTogether([
            Paragraph(title, h3),
            Paragraph(desc, body),
        ]))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("What Is Needed to Succeed", h2))
    story.append(divider())

    needs = [
        ["Requirement", "Status"],
        ["Technical infrastructure (full backend)", "✅ Built and on GitHub"],
        ["API accounts (Meta, Anthropic, Stripe, Railway, Cloudflare)", "⏳ In progress — cost £6/month"],
        ["Launch budget for creator partnerships", "£2,000–£10,000"],
        ["Retention-first discipline before scaling spend", "Strategic decision"],
        ["One niche focus at launch (recommended: fitness)", "Strategic decision"],
    ]
    story.append(table(needs, col_widths=[11*cm, 4.5*cm]))

    story.append(Spacer(1, 0.5*cm))

    closing = Table(
        [[Paragraph(
            "The question is not whether this business can work.<br/>"
            "The question is how fast it can grow.",
            ParagraphStyle("Closing", fontSize=14, textColor=WHITE, fontName="Helvetica-Bold",
                alignment=TA_CENTER, leading=22)
        )]],
        colWidths=[A4[0] - 4.4*cm],
    )
    closing.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    story.append(closing)

    story.append(Paragraph(
        "Document prepared June 2026. All financial projections are estimates based on comparable market data "
        "and are not guarantees of future performance. Technical infrastructure built on the brettyryangit/Claude "
        "GitHub repository.",
        footer_note
    ))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
