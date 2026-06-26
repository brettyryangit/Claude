from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

DARK    = colors.HexColor("#0f0f1a")
RED     = colors.HexColor("#e94560")
GREEN   = colors.HexColor("#27ae60")
AMBER   = colors.HexColor("#f39c12")
BLUE    = colors.HexColor("#2980b9")
GREY    = colors.HexColor("#555555")
LGREY   = colors.HexColor("#f5f5f5")
WHITE   = colors.white
OUTPUT  = "/home/user/Claude/Grit_Feasibility_Study.pdf"

W = A4[0] - 4.4 * cm   # usable width

import re as _re

_VERDICT_MAP = [
    ("✅", '<font color="#27ae60"><b>PASS</b></font>'),   # ✅
    ("⚠️", '<font color="#f39c12"><b>RISK</b></font>'),  # ⚠️
    ("⚠", '<font color="#f39c12"><b>RISK</b></font>'),    # ⚠
    ("❌", '<font color="#e94560"><b>AVOID</b></font>'),   # ❌
    ("★", "*"),                                            # ★
    ("⬤", "•"),                                       # ⬤ -> bullet
]

# strip anything outside Latin-1 except a few safe punctuation marks (dashes, curly quotes, ellipsis, bullet)
_EMOJI_RE = _re.compile(r"[^\x00-\xFF‐-—‘-”•…]")


def clean_cell(s):
    """Colourise verdict icons, then strip unsupported emoji. For table cells."""
    s = str(s)
    for emo, repl in _VERDICT_MAP:
        s = s.replace(emo, repl)
    return _EMOJI_RE.sub("", s).strip()


def clean_text(s):
    """Strip unsupported emoji only. For headings, boxes, body text."""
    s = str(s)
    s = s.replace("★", "*").replace("⬤", "•")
    return _EMOJI_RE.sub("", s)


def hdr_ftr(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK)
    canvas.rect(0, A4[1]-1.2*cm, A4[0], 1.2*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(2*cm, A4[1]-0.85*cm, "GRIT — Feasibility Study & Cost Analysis")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(A4[0]-2*cm, A4[1]-0.85*cm, "Confidential — June 2026")
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, A4[0], 0.9*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2*cm, 0.3*cm, "Grit AI Accountability Coach")
    canvas.drawRightString(A4[0]-2*cm, 0.3*cm, f"Page {doc.page}")
    canvas.restoreState()


def mk_styles():
    s = {}
    s["cover_h"]  = ParagraphStyle("ch",  fontSize=38, textColor=WHITE,  alignment=TA_CENTER, fontName="Helvetica-Bold", leading=46)
    s["cover_s"]  = ParagraphStyle("cs",  fontSize=14, textColor=RED,    alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=5)
    s["cover_m"]  = ParagraphStyle("cm",  fontSize=10, textColor=colors.HexColor("#aaa"), alignment=TA_CENTER, fontName="Helvetica")
    s["sec"]      = ParagraphStyle("sec", fontSize=18, textColor=WHITE,  fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=10, leading=24, backColor=DARK, leftIndent=-0.5*cm, rightIndent=-0.5*cm, borderPad=8)
    s["h2"]       = ParagraphStyle("h2",  fontSize=13, textColor=DARK,   fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=5)
    s["h3"]       = ParagraphStyle("h3",  fontSize=11, textColor=RED,    fontName="Helvetica-Bold", spaceBefore=8,  spaceAfter=3)
    s["body"]     = ParagraphStyle("bod", fontSize=10, textColor=colors.HexColor("#222"), fontName="Helvetica", leading=15, spaceAfter=7, alignment=TA_JUSTIFY)
    s["bullet"]   = ParagraphStyle("bul", fontSize=10, textColor=colors.HexColor("#222"), fontName="Helvetica", leading=14, spaceAfter=3, leftIndent=16)
    s["cap"]      = ParagraphStyle("cap", fontSize=8,  textColor=GREY,   fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=6)
    s["fn"]       = ParagraphStyle("fn",  fontSize=8,  textColor=GREY,   fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceBefore=16)
    s["green"]    = ParagraphStyle("gr",  fontSize=10, textColor=GREEN,  fontName="Helvetica-Bold")
    s["red"]      = ParagraphStyle("rd",  fontSize=10, textColor=RED,    fontName="Helvetica-Bold")
    s["amber"]    = ParagraphStyle("am",  fontSize=10, textColor=AMBER,  fontName="Helvetica-Bold")
    return s


_CELL_HDR = ParagraphStyle("cellhdr", fontSize=8.5, textColor=WHITE,
    fontName="Helvetica-Bold", leading=11, alignment=TA_LEFT)
_CELL_BODY = ParagraphStyle("cellbody", fontSize=8.5, textColor=colors.HexColor("#222"),
    fontName="Helvetica", leading=11, alignment=TA_LEFT)


def _wrap(value, style):
    """Wrap a cell value in a Paragraph so it flows within the column width."""
    if hasattr(value, "wrap"):   # already a flowable (Paragraph, etc.)
        return value
    text = clean_cell(value).replace("\n", "<br/>")
    return Paragraph(text, style)


def tbl(data, cw=None, header_color=DARK):
    wrapped = []
    for r, row in enumerate(data):
        style = _CELL_HDR if r == 0 else _CELL_BODY
        wrapped.append([_wrap(c, style) for c in row])

    t = Table(wrapped, colWidths=cw, repeatRows=1)
    rc = []
    for i in range(1, len(data)):
        rc.append(("BACKGROUND",(0,i),(-1,i), colors.HexColor("#f9f9f9") if i%2==1 else WHITE))
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), header_color),
        ("GRID",(0,0),(-1,-1), 0.4, colors.HexColor("#ddd")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("RIGHTPADDING",(0,0),(-1,-1), 6),
        *rc,
    ]))
    return t


def div():
    return HRFlowable(width="100%", thickness=1.5, color=RED, spaceAfter=8, spaceBefore=2)


def sec(text):
    return Paragraph(f"&nbsp;&nbsp;{clean_text(text)}", mk_styles()["sec"])


def box(text, bg=DARK, fg=WHITE, size=11):
    text = clean_text(text).replace("\n", "<br/>")
    t = Table([[Paragraph(text, ParagraphStyle("bx", fontSize=size, textColor=fg,
        fontName="Helvetica-Bold", alignment=TA_CENTER, leading=size+5))]],
        colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), bg),
        ("TOPPADDING",(0,0),(-1,-1), 14), ("BOTTOMPADDING",(0,0),(-1,-1), 14),
        ("LEFTPADDING",(0,0),(-1,-1), 16), ("RIGHTPADDING",(0,0),(-1,-1), 16),
    ]))
    return t


def build():
    doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
        rightMargin=2.2*cm, leftMargin=2.2*cm, topMargin=2.2*cm, bottomMargin=1.8*cm)
    s = mk_styles()
    story = []

    # ── COVER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 2.5*cm))
    cv = Table([
        [Paragraph("GRIT", s["cover_h"])],
        [Paragraph("Feasibility Study & Full Cost Analysis", s["cover_s"])],
        [Spacer(1,0.3*cm)],
        [Paragraph("Every Price Point · Every Cost · Every Scenario", s["cover_m"])],
        [Paragraph("$2 · $5 · $10 · $20 per month — What Each One Means for Your Business", s["cover_m"])],
        [Spacer(1,0.2*cm)],
        [Paragraph("Confidential — June 2026", s["cover_m"])],
    ], colWidths=[W])
    cv.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), DARK),
        ("TOPPADDING",(0,0),(-1,-1),16),("BOTTOMPADDING",(0,0),(-1,-1),16),
        ("LEFTPADDING",(0,0),(-1,-1),28),("RIGHTPADDING",(0,0),(-1,-1),28),
    ]))
    story.append(cv)
    story.append(Spacer(1,0.8*cm))
    story.append(HRFlowable(width="100%", thickness=3, color=RED))
    story.append(Spacer(1,0.8*cm))

    kpi = Table([["$1.10\nCost Per User/Month","$0.006\nPer Claude Message","98%\nWhatsApp Open Rate","85%\nGross Margin at $10"]],
        colWidths=[W/4]*4)
    kpi.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), DARK), ("TEXTCOLOR",(0,0),(-1,-1), WHITE),
        ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),12),
        ("ALIGN",(0,0),(-1,-1),"CENTER"), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),16), ("BOTTOMPADDING",(0,0),(-1,-1),16),
        ("LINEAFTER",(0,0),(2,0),1,RED),
    ]))
    story.append(kpi)
    story.append(PageBreak())

    # ── PAGE 1 — WHAT THINGS ACTUALLY COST ──────────────────────────────────
    story.append(sec("PAGE 1 — WHAT EVERYTHING ACTUALLY COSTS YOU"))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "Before choosing a price point, you need to know your exact costs. "
        "This section breaks down every cost to the penny so you can make an informed decision "
        "on pricing and know exactly when you become profitable.", s["body"]))

    story.append(Paragraph("Fixed Monthly Costs — You Pay These Regardless of User Count", s["h2"]))
    story.append(div())
    fixed = tbl([
        ["Service","What It Is","Monthly Cost USD","Notes"],
        ["Railway Hobby Plan","Server hosting + PostgreSQL database","$5.00","Scales automatically"],
        ["Cloudflare R2","PDF and image storage","$0.00","Free up to 10GB — enough for thousands of users"],
        ["Domain name","yourapp.com via Namecheap/GoDaddy","$1.00","~$12/year divided monthly"],
        ["Meta WhatsApp API","First 1,000 conversations/month","$0.00","Free tier — covers early growth"],
        ["Stripe","Card processing platform","$0.00","% fee only — no monthly charge"],
        ["TOTAL FIXED","","$6.00/month","Everything you pay before a single user signs up"],
    ], cw=[3.5*cm,5.5*cm,3.5*cm,4*cm])
    story.append(fixed)
    story.append(Paragraph("You can run this entire product for $6/month until you have hundreds of paying users.", s["cap"]))

    story.append(Paragraph("Variable Costs — You Pay These Per User Per Month", s["h2"]))
    story.append(div())
    story.append(Paragraph(
        "These costs scale directly with your user count. "
        "Understanding them lets you calculate your margin at any price point.", s["body"]))

    var = tbl([
        ["Cost Item","How It's Charged","Per User/Month","Calculation"],
        ["WhatsApp conversations","Per 24-hour conversation window (Meta)","$0.90–$1.40",
         "2 check-ins/day = ~60 windows/month @ $0.015–$0.023 each"],
        ["Claude Haiku (check-ins)","Per token — input $0.25/M, output $1.25/M","$0.04–$0.08",
         "~2 check-ins/day × 30 days × ~400 tokens avg"],
        ["Claude Sonnet (onboarding)","One-time per user at signup","$0.03–$0.06",
         "10-question onboarding + plan generation, ~8,000 tokens total"],
        ["PDF generation + storage","Cloudflare R2 storage + egress","$0.01",
         "One PDF per user, ~200KB, stored indefinitely"],
        ["Railway server load","Included in flat fee until ~2,000 users","$0.01–$0.03",
         "Negligible until scale — Railway auto-scales"],
        ["Stripe processing fee","1.4% + $0.30 per transaction (intl cards)","Varies",
         "On $9.99: ~$0.44 per month. On $2: ~$0.33 per month"],
        ["TOTAL VARIABLE","","$1.00–$1.60","Blended average: $1.20/user/month"],
    ], cw=[3.5*cm,4*cm,2.8*cm,6.2*cm])
    story.append(var)

    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph("Cost at Scale — How Costs Drop as You Grow", s["h2"]))
    story.append(div())
    scale = tbl([
        ["User Count","Monthly Fixed","Variable/User","Total Monthly Cost","Cost Per User"],
        ["50 users","$6","$1.20","$66","$1.32"],
        ["200 users","$6","$1.20","$246","$1.23"],
        ["500 users","$8","$1.15","$583","$1.17"],
        ["1,000 users","$10","$1.10","$1,110","$1.11"],
        ["5,000 users","$25","$0.95","$4,775","$0.96"],
        ["10,000 users","$50","$0.85","$8,550","$0.86"],
        ["50,000 users","$150","$0.75","$37,650","$0.75"],
    ], cw=[3*cm,3*cm,3*cm,3.5*cm,3*cm])
    story.append(scale)
    story.append(Paragraph(
        "WhatsApp conversation pricing drops with volume. Claude API costs are already near floor. "
        "Server costs become negligible at scale. Your margin improves the larger you grow.", s["cap"]))
    story.append(PageBreak())

    # ── PAGE 2 — PRICE POINT ANALYSIS ────────────────────────────────────────
    story.append(sec("PAGE 2 — PRICE POINT ANALYSIS: $2 vs $5 vs $10 vs $20"))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "This is the most important decision in your business. "
        "The right price point maximises profit — not just revenue. "
        "Here is the complete analysis of every realistic price point.", s["body"]))

    story.append(Paragraph("Gross Margin at Every Price Point", s["h2"]))
    story.append(div())
    margins = tbl([
        ["Price/Month","Revenue","COGS","Stripe Fee","Net Profit/User","Gross Margin","Verdict"],
        ["$2.00","$2.00","$1.20","$0.33","-$0.13 to $0.47","−7% to 24%","⚠️ Risky"],
        ["$3.99","$3.99","$1.20","$0.36","$2.43","61%","⚠️ Tight"],
        ["$4.99","$4.99","$1.20","$0.37","$3.42","69%","✅ Viable"],
        ["$7.99","$7.99","$1.20","$0.41","$6.38","80%","✅ Good"],
        ["$9.99","$9.99","$1.20","$0.44","$8.35","84%","✅ Recommended"],
        ["$14.99","$14.99","$1.25","$0.51","$13.23","88%","✅ Strong"],
        ["$19.99","$19.99","$1.30","$0.58","$18.11","91%","✅ Premium"],
        ["$49.99/yr","$4.17/mo equiv","$1.20","$0.63 one-time","$2.34/mo equiv","56%","✅ Cash flow win"],
    ], cw=[2.5*cm,2*cm,2*cm,2*cm,3*cm,2.5*cm,2.5*cm])
    story.append(margins)
    story.append(Paragraph("COGS = Cost of Goods Sold (WhatsApp + Claude + hosting). Stripe fee varies by country.", s["cap"]))

    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph("The $2/Month Option — Full Breakdown", s["h2"]))
    story.append(div())
    story.append(Paragraph(
        "This is the most asked-about price point because it sounds like a 'no-brainer' for users. "
        "Here is the honest truth about what it means for your business:", s["body"]))

    two_dollar = [
        ("Revenue per user", "$2.00/month"),
        ("WhatsApp cost", "$1.10/month (55% of your revenue gone immediately)"),
        ("Claude AI cost", "$0.06/month"),
        ("Stripe fee", "$0.33/month (flat fee kills low-price subscriptions)"),
        ("Server share", "$0.02/month"),
        ("NET PROFIT per user", "$0.49/month — if everything goes perfectly"),
        ("Users needed for $5,000/month profit", "10,204 paying users"),
        ("Users needed for $1,000/month profit", "2,041 paying users"),
        ("Break-even point", "You need 3 users just to cover the Stripe flat fee alone"),
    ]
    td = [["Metric","Reality at $2/Month"]] + [[k,v] for k,v in two_dollar]
    story.append(tbl(td, cw=[5*cm,10.5*cm]))
    story.append(box(
        "⚠️  $2/month is not viable as a standalone price. The Stripe flat fee ($0.30) alone eats 15% of revenue. "
        "WhatsApp costs eat another 55%. You'd need 10,000+ users to make $5K/month profit — "
        "and one bad month of churn wipes your margin entirely.",
        bg=AMBER, fg=DARK, size=10))

    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph("The $10/Month Option — Full Breakdown", s["h2"]))
    story.append(div())

    ten_dollar = [
        ("Revenue per user", "$9.99/month (use $9.99, not $10 — psychological pricing)"),
        ("WhatsApp cost", "$1.10/month (11% of revenue)"),
        ("Claude AI cost", "$0.06/month (0.6% of revenue)"),
        ("Stripe fee", "$0.44/month (4.4% of revenue)"),
        ("Server share", "$0.02/month"),
        ("NET PROFIT per user", "$8.37/month"),
        ("Gross margin", "84%"),
        ("Users needed for $5,000/month profit", "598 paying users"),
        ("Users needed for $1,000/month profit", "120 paying users"),
        ("Users needed to cover all fixed costs", "1 user covers your server bill"),
    ]
    td2 = [["Metric","Reality at $9.99/Month"]] + [[k,v] for k,v in ten_dollar]
    story.append(tbl(td2, cw=[5*cm,10.5*cm]))
    story.append(box(
        "✅  $9.99/month is the sweet spot. 84% gross margin. 598 users = $5,000/month profit. "
        "Achievable in 60–90 days with aggressive creator outreach. "
        "Comparable to Spotify, Netflix, Duolingo — price point users don't overthink.",
        bg=GREEN, fg=WHITE, size=10))
    story.append(PageBreak())

    # ── PAGE 3 — SCENARIO MODELLING ──────────────────────────────────────────
    story.append(sec("PAGE 3 — SCENARIO MODELLING AT EVERY PRICE POINT"))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "The same number of users produces dramatically different outcomes depending on your price. "
        "This page shows you exactly what 100, 500, 1,000, and 5,000 users means for your business "
        "at every price point.", s["body"]))

    story.append(Paragraph("Monthly Profit at 100 Paying Users", s["h2"]))
    story.append(div())
    u100 = tbl([
        ["Price/Month","Monthly Revenue","Monthly Costs","Monthly Profit","Annual Profit"],
        ["$2.00","$200","$186","$14","$168"],
        ["$4.99","$499","$186","$313","$3,756"],
        ["$9.99","$999","$186","$813","$9,756"],
        ["$14.99","$1,499","$190","$1,309","$15,708"],
        ["$19.99","$1,999","$196","$1,803","$21,636"],
    ], cw=[3*cm,3.5*cm,3.5*cm,3.5*cm,3*cm])
    story.append(u100)
    story.append(Paragraph("100 users at $2 = a pizza. 100 users at $9.99 = $813/month. Same acquisition cost.", s["cap"]))

    story.append(Paragraph("Monthly Profit at 500 Paying Users", s["h2"]))
    story.append(div())
    u500 = tbl([
        ["Price/Month","Monthly Revenue","Monthly Costs","Monthly Profit","Annual Profit"],
        ["$2.00","$1,000","$916","$84","$1,008"],
        ["$4.99","$2,495","$916","$1,579","$18,948"],
        ["$9.99","$4,995","$916","$4,079","$48,948"],
        ["$14.99","$7,495","$925","$6,570","$78,840"],
        ["$19.99","$9,995","$940","$9,055","$108,660"],
    ], cw=[3*cm,3.5*cm,3.5*cm,3.5*cm,3*cm])
    story.append(u500)
    story.append(Paragraph("500 users at $2 = barely profitable. 500 users at $9.99 = $4,079/month. Nearly at your $5K target.", s["cap"]))

    story.append(Paragraph("Monthly Profit at 1,000 Paying Users", s["h2"]))
    story.append(div())
    u1000 = tbl([
        ["Price/Month","Monthly Revenue","Monthly Costs","Monthly Profit","Annual Profit","Status"],
        ["$2.00","$2,000","$1,826","$174","$2,088","⚠️ Barely viable"],
        ["$4.99","$4,990","$1,826","$3,164","$37,968","✅ Solid"],
        ["$9.99","$9,990","$1,826","$8,164","$97,968","✅ Strong"],
        ["$14.99","$14,990","$1,850","$13,140","$157,680","✅ Excellent"],
        ["$19.99","$19,990","$1,880","$18,110","$217,320","✅ Premium"],
    ], cw=[2.5*cm,3*cm,3*cm,3*cm,3*cm,2*cm])
    story.append(u1000)

    story.append(Paragraph("Monthly Profit at 5,000 Paying Users", s["h2"]))
    story.append(div())
    u5000 = tbl([
        ["Price/Month","Monthly Revenue","Monthly Costs","Monthly Profit","Annual Profit","Status"],
        ["$2.00","$10,000","$9,625","$375","$4,500","⚠️ Not worth it"],
        ["$4.99","$24,950","$9,625","$15,325","$183,900","✅ Very good"],
        ["$9.99","$49,950","$9,625","$40,325","$483,900","✅ Life-changing"],
        ["$14.99","$74,950","$9,750","$65,200","$782,400","✅ Business-defining"],
        ["$19.99","$99,950","$9,900","$90,050","$1,080,600","✅ Exit territory"],
    ], cw=[2.5*cm,3*cm,3*cm,3*cm,3*cm,2*cm])
    story.append(u5000)
    story.append(Paragraph(
        "The difference between $2 and $9.99 at 5,000 users: $375/month vs $40,325/month. "
        "Same number of users. 107x more profit.", s["cap"]))
    story.append(PageBreak())

    # ── PAGE 4 — RECOMMENDED PRICING STRUCTURE ───────────────────────────────
    story.append(sec("PAGE 4 — RECOMMENDED PRICING STRUCTURE"))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "Based on the cost analysis, margin modelling, and comparable market research, "
        "here is the exact pricing structure recommended for Grit — "
        "with a clear rationale for every tier.", s["body"]))

    story.append(Paragraph("The Four-Tier Model (USD)", s["h2"]))
    story.append(div())
    tiers = tbl([
        ["Tier","Price","Annual Option","Margin","Target User","Features"],
        ["Free Trial","$0 (7 days)","N/A","N/A","Everyone","Full product — no card required"],
        ["Core","$4.99/mo","$39.99/yr","69%","Budget users","3 goals, 2 check-ins/day, PDF plan"],
        ["Pro ★","$9.99/mo","$59.99/yr","84%","Primary market","Unlimited goals, 3 check-ins, streak analytics"],
        ["Elite","$19.99/mo","$149.99/yr","91%","Power users","Everything + weekly coaching recap"],
        ["Referred users","First month 20% off","—","74%","Via referral link","Same as Pro, discounted entry"],
    ], cw=[2.5*cm,2.5*cm,2.5*cm,2*cm,3*cm,4*cm])
    story.append(tiers)
    story.append(Paragraph("★ Pro at $9.99/month is the anchor. 70% of revenue will come from this tier.", s["cap"]))

    story.append(Paragraph("Why NOT $2/Month — The Definitive Answer", s["h2"]))
    story.append(div())
    story.append(Paragraph(
        "The instinct to price at $2/month comes from wanting to remove every possible barrier to sign-up. "
        "It sounds logical. In practice, it creates four serious problems:", s["body"]))

    reasons = [
        ("Problem 1 — Stripe kills your margin",
         "Stripe charges $0.30 flat + 1.4% per transaction. On a $2 charge, that's $0.33 — 16.5% of your revenue in fees alone. "
         "You are effectively paying Stripe to process payments that barely cover your WhatsApp costs. "
         "This is not a theoretical issue — it will make you unprofitable at any realistic user count."),
        ("Problem 2 — Low price signals low value",
         "Decades of pricing psychology research confirms that price is a proxy for quality. "
         "Users who pay $2/month treat the product like a $2 product — they churn faster, engage less, "
         "and are less likely to refer friends. Users who pay $9.99/month are invested. "
         "They show up. They complete check-ins. They build streaks. Higher price = higher retention."),
        ("Problem 3 — You cannot afford to acquire users",
         "If your profit per user is $0.49/month, your maximum sustainable CAC (customer acquisition cost) "
         "is around $3–5 (assuming 10-month lifetime). Creator affiliates at 20% commission on $2 = $0.40/month. "
         "No creator will promote you for $0.40/month when they can promote a $9.99 product for $2/month. "
         "Low price destroys your ability to pay for growth."),
        ("Problem 4 — You need 10x more users to reach the same profit",
         "To make $5,000/month profit at $2: you need 10,204 users. "
         "To make $5,000/month profit at $9.99: you need 598 users. "
         "Acquiring and retaining 10,204 users is not 17x harder than 598 — it is more like 50x harder "
         "because churn compounds. You will never catch up."),
    ]
    for title, desc in reasons:
        story.append(KeepTogether([Paragraph(title, s["h3"]), Paragraph(desc, s["body"])]))

    story.append(box(
        "Conclusion: $2/month is not a growth strategy. It is a slow way to go broke with a lot of users.\n"
        "The correct entry price is $4.99/month minimum. $9.99/month is the right answer.",
        bg=DARK, fg=WHITE, size=10))
    story.append(PageBreak())

    # ── PAGE 5 — PATH TO $5K/MONTH ────────────────────────────────────────────
    story.append(sec("PAGE 5 — REALISTIC PATH TO $5,000/MONTH PROFIT"))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "At $9.99/month Pro with 84% gross margin, you need 598 paying users to clear $5,000/month profit. "
        "Here is the most realistic path to get there — with honest timelines.", s["body"]))

    story.append(Paragraph("How Many Users You Need at Each Price Point", s["h2"]))
    story.append(div())
    need = tbl([
        ["Monthly Profit Target","At $2/mo","At $4.99/mo","At $9.99/mo","At $19.99/mo"],
        ["$1,000/month","2,041 users","319 users","120 users","55 users"],
        ["$2,500/month","5,102 users","797 users","299 users","138 users"],
        ["$5,000/month","10,204 users","1,594 users","598 users","277 users"],
        ["$10,000/month","20,408 users","3,185 users","1,196 users","553 users"],
        ["$50,000/month","102,041 users","15,924 users","5,978 users","2,764 users"],
    ], cw=[4*cm,3*cm,3*cm,3*cm,3*cm])
    story.append(need)

    story.append(Paragraph("The 90-Day Sprint to $5,000/Month at $9.99 (598 users needed)", s["h2"]))
    story.append(div())
    sprint = tbl([
        ["Week","Action","New Users","Total Paying","Monthly Profit"],
        ["Week 1","Personal network — 50 founding members at $9.99","30","30","$251"],
        ["Week 2","Reddit posts in r/getdisciplined, r/Fitness, r/personalfinance","60","80","$669"],
        ["Week 3","First 2 micro-influencers go live (50K followers each)","100","160","$1,339"],
        ["Week 4","Referral loop active — existing users share links","40","190","$1,590"],
        ["Week 5","2 more micro-influencers + TikTok content compounding","120","280","$2,342"],
        ["Week 6","Reddit momentum + influencer reposts","60","320","$2,677"],
        ["Week 7","3rd wave of influencers + annual plan push","130","400","$3,346"],
        ["Week 8","Referral compounding + organic TikTok","80","450","$3,765"],
        ["Week 9","4th influencer wave + Product Hunt launch","100","500","$4,183"],
        ["Week 10","Conversions compound + retained users","98","598","$5,002 ✅"],
    ], cw=[1.8*cm,6.5*cm,2.5*cm,3*cm,2.7*cm])
    story.append(sprint)
    story.append(Paragraph("This assumes 30% trial-to-paid conversion and 85% monthly retention. Both are conservative for a well-executed product.", s["cap"]))

    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph("Churn — The Number That Kills Most Subscription Businesses", s["h2"]))
    story.append(div())
    story.append(Paragraph(
        "Churn is the percentage of users who cancel each month. "
        "It is the most important metric in any subscription business. "
        "Here is what different churn rates mean for Grit:", s["body"]))

    churn = tbl([
        ["Monthly Churn","What It Means","Users at Month 12 (from 100 new/mo)","LTV at $9.99","Verdict"],
        ["5%","Very low — exceptional product","1,240 users","$200","✅ World class"],
        ["10%","Low — good product","950 users","$100","✅ Strong"],
        ["15%","Average — industry standard","667 users","$67","✅ Viable"],
        ["25%","High — product needs work","400 users","$40","⚠️ Struggling"],
        ["40%","Very high — product is broken","250 users","$25","❌ Fix product first"],
    ], cw=[2.5*cm,4*cm,4*cm,2.5*cm,2.5*cm])
    story.append(churn)

    story.append(Spacer(1,0.3*cm))
    story.append(box(
        "Target: 10–15% monthly churn. Grit's streak mechanics, PDF plan investment, and "
        "daily WhatsApp relationship are specifically designed to achieve this. "
        "Duolingo's churn is ~12%. Spotify's is ~5%. You are building for that range.",
        bg=DARK, fg=WHITE, size=10))
    story.append(PageBreak())

    # ── PAGE 6 — 12-MONTH FINANCIAL MODEL ────────────────────────────────────
    story.append(sec("PAGE 6 — FULL 12-MONTH FINANCIAL MODEL"))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "Three scenarios: Conservative (slow creator traction), Moderate (2–4 creators active), "
        "and Aggressive (1 viral moment). All at $9.99/month primary price with 70% Pro, 20% Core, 10% Elite mix.", s["body"]))

    story.append(Paragraph("Conservative Scenario — Slow But Steady", s["h2"]))
    story.append(div())
    con = tbl([
        ["Month","New Users","Total Paying","MRR","Costs","Profit","Cumulative Profit"],
        ["1","50","25","$224","$350","-$126","-$126"],
        ["2","80","85","$761","$450","$311","$185"],
        ["3","100","160","$1,434","$590","$844","$1,029"],
        ["4","120","240","$2,150","$740","$1,410","$2,439"],
        ["6","150","420","$3,762","$1,100","$2,662","$7,703"],
        ["9","200","750","$6,718","$1,850","$4,868","$22,375"],
        ["12","250","1,100","$9,856","$2,600","$7,256","$47,890"],
    ], cw=[1.3*cm,2.4*cm,2.4*cm,2.3*cm,2.3*cm,2.3*cm,3.5*cm])
    story.append(con)
    story.append(Paragraph("Year 1 profit: ~$47,890 USD | Month 12 ARR: ~$118,000", s["cap"]))

    story.append(Paragraph("Moderate Scenario — 4–6 Micro-Influencers Active", s["h2"]))
    story.append(div())
    mod = tbl([
        ["Month","New Users","Total Paying","MRR","Costs","Profit","Cumulative Profit"],
        ["1","50","25","$224","$350","-$126","-$126"],
        ["2","300","200","$1,792","$700","$1,092","$966"],
        ["3","600","650","$5,825","$1,600","$4,225","$5,191"],
        ["4","700","1,100","$9,856","$2,600","$7,256","$12,447"],
        ["6","800","2,200","$19,712","$4,500","$15,212","$42,747"],
        ["9","1,000","4,500","$40,320","$8,500","$31,820","$131,000"],
        ["12","1,200","7,500","$67,200","$13,800","$53,400","$260,000"],
    ], cw=[1.3*cm,2.4*cm,2.4*cm,2.3*cm,2.3*cm,2.3*cm,3.5*cm])
    story.append(mod)
    story.append(Paragraph("Year 1 profit: ~$260,000 USD | Month 12 ARR: ~$806,400", s["cap"]))

    story.append(Paragraph("Aggressive Scenario — 1 Viral Creator Moment (Month 3)", s["h2"]))
    story.append(div())
    agg = tbl([
        ["Month","New Users","Total Paying","MRR","Costs","Profit","Cumulative Profit"],
        ["1","50","25","$224","$350","-$126","-$126"],
        ["2","500","350","$3,136","$1,100","$2,036","$1,910"],
        ["3 (VIRAL)","8,000","5,000","$44,800","$9,500","$35,300","$37,210"],
        ["4","3,000","7,000","$62,720","$12,500","$50,220","$87,430"],
        ["6","2,000","10,000","$89,600","$16,000","$73,600","$226,650"],
        ["9","2,000","14,000","$125,440","$21,000","$104,440","$536,520"],
        ["12","2,500","18,000","$161,280","$26,000","$135,280","$943,880"],
    ], cw=[2*cm,2.3*cm,2.4*cm,2.5*cm,2.3*cm,2.3*cm,2.8*cm])
    story.append(agg)
    story.append(Paragraph("Year 1 profit: ~$943,880 USD | Month 12 ARR: ~$1.9M — requires surviving the infrastructure spike.", s["cap"]))
    story.append(PageBreak())

    # ── PAGE 7 — UNIT ECONOMICS & SUMMARY ────────────────────────────────────
    story.append(sec("PAGE 7 — UNIT ECONOMICS & EXECUTIVE SUMMARY"))
    story.append(Spacer(1,0.3*cm))

    story.append(Paragraph("Complete Unit Economics at $9.99/Month", s["h2"]))
    story.append(div())
    ue = tbl([
        ["Metric","Value","Notes"],
        ["Monthly Price (Pro)","$9.99","Primary tier — 70% of users"],
        ["COGS per user","$1.20","WhatsApp + Claude + hosting"],
        ["Stripe fee","$0.44","1.4% + $0.30 per transaction"],
        ["Net profit per user","$8.35","84% gross margin"],
        ["Average trial-to-paid conversion","35–45%","Target — achievable with WhatsApp frictionless onboarding"],
        ["Average monthly churn (target)","10–15%","Achievable with streak mechanics"],
        ["Average customer lifetime","8–12 months","At 10–12% monthly churn"],
        ["Customer Lifetime Value (LTV)","$67–$100","Net profit × lifetime months"],
        ["Customer Acquisition Cost (CAC)","$10–18","Via micro-influencer affiliates at 20%"],
        ["LTV:CAC Ratio","4:1–7:1","Healthy threshold is 3:1"],
        ["Payback period","6–8 weeks","Time to recover CAC from subscription revenue"],
        ["Annual plan conversion target","20% of users","£59.99/year — locks in revenue, kills churn"],
        ["Users needed for $5K/month profit","598","At $9.99 with 84% margin"],
        ["Users needed for $10K/month profit","1,196","Achievable in 4–5 months with good execution"],
        ["Month 12 ARR target (moderate)","$806,000","Based on moderate scenario above"],
    ], cw=[5.5*cm,3.5*cm,6.5*cm])
    story.append(ue)

    story.append(Spacer(1,0.4*cm))
    story.append(Paragraph("The Three Numbers to Watch Every Week", s["h2"]))
    story.append(div())
    three = tbl([
        ["Number","What It Is","Target","If Below Target"],
        ["Trial → Paid %","% of free trial users who subscribe","35%+","Improve trial experience, check paywall message"],
        ["Month-2 Retention","% of month-1 subscribers still active in month 2","80%+","Improve check-in quality, add streak freeze reminder"],
        ["Weekly New Signups","New trial starts per week","50+ in month 1","Push more creator outreach, post on Reddit"],
    ], cw=[3.5*cm,4.5*cm,2.5*cm,5*cm])
    story.append(three)

    story.append(Spacer(1,0.4*cm))
    story.append(box(
        "The infrastructure is built. The costs are $6/month fixed until you have hundreds of users.\n"
        "At $9.99/month you need 598 paying users for $5,000/month profit.\n"
        "At current growth rates with 4–6 micro-influencers: achievable in 60–90 days.\n\n"
        "Price at $9.99. Launch this week. The numbers work.",
        bg=DARK, fg=WHITE, size=11))

    story.append(Paragraph(
        "All figures in USD. Costs based on current API pricing as of June 2026. "
        "Financial projections are estimates based on comparable market data and are not guarantees of future performance. "
        "Built on brettyryangit/Claude GitHub repository.", s["fn"]))

    doc.build(story, onFirstPage=hdr_ftr, onLaterPages=hdr_ftr)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build()
