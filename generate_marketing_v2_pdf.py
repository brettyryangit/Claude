from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

DARK   = colors.HexColor("#0f0f1a")
RED    = colors.HexColor("#e94560")
GREEN  = colors.HexColor("#27ae60")
AMBER  = colors.HexColor("#f39c12")
BLUE   = colors.HexColor("#2980b9")
GREY   = colors.HexColor("#555555")
LGREY  = colors.HexColor("#f5f5f5")
WHITE  = colors.white
OUTPUT = "/home/user/Claude/Grit_Marketing_Plan_v2.pdf"

import re as _re

_VERDICT_MAP = [
    ("✅", '<font color="#27ae60"><b>PASS</b></font>'),
    ("⚠️", '<font color="#f39c12"><b>RISK</b></font>'),
    ("⚠", '<font color="#f39c12"><b>RISK</b></font>'),
    ("❌", '<font color="#e94560"><b>AVOID</b></font>'),
    ("★", "*"),
    ("⬤", "•"),
]
_EMOJI_RE = _re.compile(r"[^\x00-\xFF‐-—‘-”•…]")


def clean_cell(s):
    s = str(s)
    for emo, repl in _VERDICT_MAP:
        s = s.replace(emo, repl)
    return _EMOJI_RE.sub("", s).strip()


def clean_text(s):
    s = str(s).replace("★", "*").replace("⬤", "•")
    return _EMOJI_RE.sub("", s)
W      = A4[0] - 4.4*cm


def hdr_ftr(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK)
    canvas.rect(0, A4[1]-1.2*cm, A4[0], 1.2*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(2*cm, A4[1]-0.85*cm, "GRIT — Full Marketing Plan v2")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(A4[0]-2*cm, A4[1]-0.85*cm, "Confidential — June 2026")
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, A4[0], 0.9*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2*cm, 0.3*cm, "Grit AI Accountability Coach — Marketing Strategy")
    canvas.drawRightString(A4[0]-2*cm, 0.3*cm, f"Page {doc.page}")
    canvas.restoreState()


def s():
    return {
        "cover_h": ParagraphStyle("ch", fontSize=38, textColor=WHITE, alignment=TA_CENTER, fontName="Helvetica-Bold", leading=46),
        "cover_s": ParagraphStyle("cs", fontSize=14, textColor=RED, alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=5),
        "cover_m": ParagraphStyle("cm", fontSize=10, textColor=colors.HexColor("#aaa"), alignment=TA_CENTER, fontName="Helvetica"),
        "sec":     ParagraphStyle("sc", fontSize=17, textColor=WHITE, fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=10, leading=22, backColor=DARK, leftIndent=-0.5*cm, rightIndent=-0.5*cm, borderPad=8),
        "h2":      ParagraphStyle("h2", fontSize=13, textColor=DARK, fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=5),
        "h3":      ParagraphStyle("h3", fontSize=11, textColor=RED, fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=3),
        "h4":      ParagraphStyle("h4", fontSize=10, textColor=DARK, fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=2),
        "body":    ParagraphStyle("bd", fontSize=10, textColor=colors.HexColor("#222"), fontName="Helvetica", leading=15, spaceAfter=7, alignment=TA_JUSTIFY),
        "bullet":  ParagraphStyle("bu", fontSize=10, textColor=colors.HexColor("#222"), fontName="Helvetica", leading=14, spaceAfter=3, leftIndent=16),
        "cap":     ParagraphStyle("ca", fontSize=8, textColor=GREY, fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=6),
        "num":     ParagraphStyle("nm", fontSize=26, textColor=RED, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=30),
        "fn":      ParagraphStyle("fn", fontSize=8, textColor=GREY, fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceBefore=16),
    }


ST = s()


_CELL_HDR = ParagraphStyle("cellhdr", fontSize=8.5, textColor=WHITE,
    fontName="Helvetica-Bold", leading=11, alignment=TA_LEFT)
_CELL_BODY = ParagraphStyle("cellbody", fontSize=8.5, textColor=colors.HexColor("#222"),
    fontName="Helvetica", leading=11, alignment=TA_LEFT)


def _wrap(value, style):
    if hasattr(value, "wrap"):
        return value
    text = clean_cell(value).replace("\n", "<br/>")
    return Paragraph(text, style)


def tbl(data, cw=None):
    wrapped = []
    for r, row in enumerate(data):
        style = _CELL_HDR if r == 0 else _CELL_BODY
        wrapped.append([_wrap(c, style) for c in row])

    t = Table(wrapped, colWidths=cw, repeatRows=1)
    rc = [("BACKGROUND",(0,i),(-1,i), colors.HexColor("#f9f9f9") if i%2==1 else WHITE) for i in range(1,len(data))]
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DARK),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#ddd")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6), ("RIGHTPADDING",(0,0),(-1,-1),6), *rc,
    ]))
    return t


def div():
    return HRFlowable(width="100%", thickness=1.5, color=RED, spaceAfter=8, spaceBefore=2)


def sec(text):
    return Paragraph(f"&nbsp;&nbsp;{clean_text(text)}", ST["sec"])


def box(text, bg=DARK, fg=WHITE, size=10):
    text = clean_text(text).replace("\n", "<br/>")
    t = Table([[Paragraph(text, ParagraphStyle("bx", fontSize=size, textColor=fg,
        fontName="Helvetica-Bold", alignment=TA_CENTER, leading=size+5))]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),bg),
        ("TOPPADDING",(0,0),(-1,-1),14), ("BOTTOMPADDING",(0,0),(-1,-1),14),
        ("LEFTPADDING",(0,0),(-1,-1),16), ("RIGHTPADDING",(0,0),(-1,-1),16),
    ]))
    return t


def strat(num, title, body_text, how_paid, cost, timeline, usd_potential):
    title, body_text = clean_text(title), clean_text(body_text)
    how_paid, cost = clean_text(how_paid), clean_text(cost)
    timeline, usd_potential = clean_text(timeline), clean_text(usd_potential)
    num_p = Paragraph(str(num), ST["num"])
    content = Table([
        [Paragraph(title, ParagraphStyle("st", fontSize=11, textColor=DARK, fontName="Helvetica-Bold", leading=15))],
        [Paragraph(body_text, ParagraphStyle("sb", fontSize=9.5, textColor=colors.HexColor("#333"), fontName="Helvetica", leading=14))],
        [Spacer(1,3)],
        [Paragraph(
            f"<b>Revenue model:</b> {how_paid}<br/>"
            f"<b>Cost to execute:</b> {cost} &nbsp;&nbsp; "
            f"<b>Timeline to first results:</b> {timeline} &nbsp;&nbsp; "
            f"<b>Monthly USD potential:</b> {usd_potential}",
            ParagraphStyle("sm", fontSize=9, textColor=GREY, fontName="Helvetica", leading=13)
        )],
    ], colWidths=[12*cm])
    content.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),("LEFTPADDING",(0,0),(-1,-1),0)]))
    outer = Table([[num_p, content]], colWidths=[2.2*cm, 12*cm])
    outer.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),LGREY), ("BACKGROUND",(1,0),(1,0),WHITE),
        ("BOX",(0,0),(-1,-1),1,colors.HexColor("#e0e0e0")),
        ("LINEAFTER",(0,0),(0,-1),2,RED),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(1,0),(1,0),12),
    ]))
    return KeepTogether([outer, Spacer(1,0.22*cm)])


def build():
    doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
        rightMargin=2.2*cm, leftMargin=2.2*cm, topMargin=2.2*cm, bottomMargin=1.8*cm)
    story = []

    # COVER
    story.append(Spacer(1,2.5*cm))
    cv = Table([
        [Paragraph("GRIT", ST["cover_h"])],
        [Paragraph("Complete Marketing Plan — Version 2", ST["cover_s"])],
        [Spacer(1,0.2*cm)],
        [Paragraph("20 Strategies · USD Pricing · Free Trial System · Referral Programme", ST["cover_m"])],
        [Paragraph("Yearly Fees · Creator Playbook · Zero-to-$5K Sprint · Real Numbers", ST["cover_m"])],
        [Spacer(1,0.2*cm)],
        [Paragraph("Confidential — June 2026", ST["cover_m"])],
    ], colWidths=[W])
    cv.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),DARK),
        ("TOPPADDING",(0,0),(-1,-1),16),("BOTTOMPADDING",(0,0),(-1,-1),16),
        ("LEFTPADDING",(0,0),(-1,-1),28),("RIGHTPADDING",(0,0),(-1,-1),28),
    ]))
    story.append(cv)
    story.append(Spacer(1,0.8*cm))
    story.append(HRFlowable(width="100%", thickness=3, color=RED))
    story.append(Spacer(1,0.8*cm))
    kpi = Table([["20\nStrategies","598\nUsers = $5K/mo","84%\nGross Margin at $9.99","20%\nAffiliate Commission"]],
        colWidths=[W/4]*4)
    kpi.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),DARK),("TEXTCOLOR",(0,0),(-1,-1),WHITE),
        ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),12),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),16),("BOTTOMPADDING",(0,0),(-1,-1),16),
        ("LINEAFTER",(0,0),(2,0),1,RED),
    ]))
    story.append(kpi)
    story.append(PageBreak())

    # PAGE 1 — HOW YOU GET PAID
    story.append(sec("PAGE 1 — HOW YOU GET PAID: EVERY REVENUE STREAM"))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "Grit has six distinct revenue streams. Subscriptions are the engine — everything else stacks on top. "
        "Understanding every stream before you launch means you can monetise from day one.", ST["body"]))

    story.append(Paragraph("All Revenue Streams — USD", ST["h2"]))
    story.append(div())
    streams = tbl([
        ["#","Revenue Stream","Price (USD)","How You Get Paid","Monthly Potential"],
        ["1","Monthly Subscription — Core","$4.99/mo","Stripe auto-charges monthly","$4.55 net after Stripe"],
        ["2","Monthly Subscription — Pro ★","$9.99/mo","Stripe auto-charges monthly","$9.14 net after Stripe"],
        ["3","Monthly Subscription — Elite","$19.99/mo","Stripe auto-charges monthly","$18.69 net after Stripe"],
        ["4","Annual Plan — Pro","$59.99/yr","Single Stripe charge upfront","$58.60 net, paid today"],
        ["5","Annual Plan — Elite","$149.99/yr","Single Stripe charge upfront","$147.89 net, paid today"],
        ["6","Streak Freeze Add-on","$0.99 each / $3.99 × 5","Impulse purchase via WhatsApp","$0.50–$2 per active user"],
        ["7","90-Day Challenge Pack","$49.99 one-time","Upsell at onboarding completion","One-time per user"],
        ["8","Grit for Teams (B2B)","$7.99/employee/mo","Annual invoice to HR dept","$480/yr per 5-person team"],
        ["9","Affiliate Commissions","5–30% per sale","Recommend products to users","Passive, scales with users"],
        ["10","Referral Programme","20% of referred sub","Auto-calculated via Stripe webhook","Reduces your net CAC"],
    ], cw=[0.8*cm,4*cm,2.8*cm,4*cm,3.9*cm])
    story.append(streams)

    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph("Stripe Fee Reality Check (USD)", ST["h2"]))
    story.append(div())
    story.append(Paragraph(
        "Stripe charges 2.9% + $0.30 per transaction for US cards (or 1.4% + $0.30 for European cards). "
        "This flat $0.30 fee is critical to understand — it punishes low price points severely.", ST["body"]))
    stripe_fees = tbl([
        ["Price","Stripe Fee","Net to You","% Lost to Stripe","Impact"],
        ["$2.00","$0.36","$1.64","18%","❌ Devastating — nearly 1 in 5 dollars gone"],
        ["$4.99","$0.44","$4.55","9%","⚠️ Significant but manageable"],
        ["$9.99","$0.59","$9.40","6%","✅ Acceptable"],
        ["$19.99","$0.88","$19.11","4%","✅ Minimal"],
        ["$59.99/yr","$2.04","$57.95","3%","✅ Best ratio — annual billing wins"],
    ], cw=[2.5*cm,3*cm,3*cm,3*cm,5*cm])
    story.append(stripe_fees)
    story.append(Paragraph("US card rates shown (2.9% + $0.30). International cards may vary slightly.", ST["cap"]))
    story.append(PageBreak())

    # PAGE 2 — FREE TRIAL + ANNUAL
    story.append(sec("PAGE 2 — FREE TRIAL SYSTEM & ANNUAL PRICING"))
    story.append(Spacer(1,0.3*cm))

    story.append(Paragraph("The 7-Day Trial — Day by Day", ST["h2"]))
    story.append(div())
    trial = tbl([
        ["Day","What Grit Sends","Purpose"],
        ["Day 0 — Sign up","Welcome message → 10-question onboarding begins","Hook them before they can second-guess"],
        ["Day 0 — 5 mins later","Personalised 90-day PDF plan delivered in WhatsApp","WOW moment — real value before paying"],
        ["Day 1","Morning motivation image + quote at their local time","Habit formation: they wake up to Grit"],
        ["Day 1 — Evening","First daily check-in: 'Did you do it today?'","Accountability loop activated"],
        ["Days 2–4","Morning motivation + 2 check-ins daily. Streak building.","Psychological investment grows daily"],
        ["Day 5","Soft nudge: 'Your free trial ends in 2 days 👊'","Plant the seed — no pressure yet"],
        ["Day 6","Milestone message if streak is 6+ days: 'You've been consistent all week'","Loss aversion: they don't want to lose this"],
        ["Day 7","Payment options sent: 4 tiers, clear USD pricing, direct Stripe link","Conversion in the channel they trust"],
        ["Day 8–10 (grace)","Daily gentle reminder if no payment: 'Your coaching pauses today'","Recover hesitant users before hard cutoff"],
        ["Referred users","Same flow but 30-day trial + 20% off first month","Better conversion rate from warm referrals"],
    ], cw=[3*cm,6*cm,6.5*cm])
    story.append(trial)

    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph("Annual Pricing — The Best Retention Tool You Have", ST["h2"]))
    story.append(div())
    story.append(Paragraph(
        "Annual subscribers churn at 5–10% versus 25–35% for monthly. "
        "One annual subscriber is worth 2–3 monthly subscribers. Push this hard.", ST["body"]))

    annual = tbl([
        ["Tier","Monthly Price","Annual Price","User Saves","You Receive Upfront","Effective Monthly for User"],
        ["Core","$4.99/mo","$39.99/yr","$19.89 (33%)","$39.99 today","$3.33/mo"],
        ["Pro ★","$9.99/mo","$59.99/yr","$59.89 (50%)","$59.99 today","$5.00/mo"],
        ["Elite","$19.99/mo","$149.99/yr","$89.89 (37%)","$149.99 today","$12.50/mo"],
    ], cw=[1.8*cm,2.4*cm,2.4*cm,2.6*cm,3.2*cm,4.2*cm])
    story.append(annual)
    story.append(Paragraph("★ 'Less than $1.20 a week' is how to frame Pro Annual. Push it at end of trial and at 30-day streak.", ST["cap"]))

    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph("The 5 Best Moments to Push the Annual Plan", ST["h2"]))
    story.append(div())
    moments = tbl([
        ["Moment","Message Angle","Expected Conversion"],
        ["End of 7-day trial","'Lock in Pro for the full year at $59.99 — save $60 vs monthly'","15–25% of trial converters"],
        ["30-day streak hit","'You've been consistent for a month. Commit to the year at half price.'","20–30% of those offered"],
        ["Price increase notice","'Prices go up next month. Lock in current rate for 12 months now.'","25–35% urgency conversion"],
        ["January 1st campaign","'New year, full year. Start 2027 with 365 days of accountability.'","Seasonal spike — highest of year"],
        ["After a missed streak","'Get back on track. Commit to the full year + 3 bonus streak freezes.'","10–15% of lapsed users"],
    ], cw=[4*cm,7*cm,4.5*cm])
    story.append(moments)
    story.append(PageBreak())

    # PAGE 3 — REFERRAL PROGRAMME
    story.append(sec("PAGE 3 — REFERRAL PROGRAMME: YOUR USERS AS A SALES TEAM"))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "This feature is already built into the product. Every user gets a unique referral link. "
        "When someone signs up through it, the referrer earns 20% of every payment — automatically, every month, "
        "for as long as that person stays subscribed. Your users become a sales team that works 24/7.", ST["body"]))

    story.append(Paragraph("How the Referral System Works — End to End", ST["h2"]))
    story.append(div())
    ref_flow = tbl([
        ["Step","What Happens","Who Does What"],
        ["1","User texts SHARE to Grit","Grit sends them a pre-written WhatsApp message to forward to contacts"],
        ["2","Contact taps the link","WhatsApp opens pre-filled: 'START BRETT-X7K2'"],
        ["3","New user signs up","Gets 30-day free trial + 20% off first month automatically"],
        ["4","New user completes onboarding","Referrer gets WhatsApp notification: 'Someone just signed up using your link!'"],
        ["5","New user pays","Referrer gets instant WhatsApp: '£X commission added to your wallet'"],
        ["6","Every subsequent month","20% commission auto-calculated from Stripe → credited to referrer wallet"],
        ["7","1st of each month","Referrer gets monthly commission report + payout processed"],
        ["8","User texts WALLET","Sees balance, total paid out, active referrals"],
    ], cw=[1.5*cm,5.5*cm,8.5*cm])
    story.append(ref_flow)

    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph("What a Referrer Earns — USD Examples", ST["h2"]))
    story.append(div())
    earn = tbl([
        ["Referrals Who Convert","Monthly Commission (20% of $9.99)","Annual Earnings","What This Means"],
        ["5 paying referrals","$10/month","$120/year","Coffee money — nice bonus"],
        ["25 paying referrals","$50/month","$600/year","Side income — motivates sharing"],
        ["100 paying referrals","$200/month","$2,400/year","Significant passive income"],
        ["500 paying referrals","$999/month","$11,988/year","Full-time income from sharing one product"],
        ["2,000 paying referrals","$3,996/month","$47,952/year","This is what a top creator affiliate earns"],
    ], cw=[4*cm,3.5*cm,3*cm,5*cm])
    story.append(earn)
    story.append(Paragraph(
        "A fitness creator with 100K followers who drives 500 paying users earns $999/month recurring — "
        "every month those users stay subscribed. This is more attractive than most flat-fee brand deals.", ST["cap"]))

    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph("The Pre-Written Share Message (Fitness Version)", ST["h2"]))
    story.append(div())
    share_msg = Table([[Paragraph(
        clean_text(
            "<i>\"Hey! I've been using this AI accountability coach called Grit and it's actually keeping me on track "
            "with my fitness goals. It texts me every day on WhatsApp, gave me a personalised 90-day plan as a PDF, "
            "and tracks my streak. You get a FREE 30-day trial (instead of the usual 7) plus 20% off your first month "
            "if you use my link. No app to download — just WhatsApp.<br/><br/>"
            "https://wa.me/61XXXXXX?text=START+BRETT-X7K2<br/><br/>"
            "Seriously try it, it's changed my routine.\"</i>"
        ),
        ParagraphStyle("msg", fontSize=9.5, textColor=colors.HexColor("#333"), fontName="Helvetica", leading=15))
    ]], colWidths=[W])
    share_msg.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),LGREY),
        ("BOX",(0,0),(-1,-1),1,colors.HexColor("#ccc")),
        ("LEFTPADDING",(0,0),(-1,-1),16),("RIGHTPADDING",(0,0),(-1,-1),16),
        ("TOPPADDING",(0,0),(-1,-1),12),("BOTTOMPADDING",(0,0),(-1,-1),12),
    ]))
    story.append(share_msg)
    story.append(Paragraph("This message is auto-sent to users when they text SHARE. Finance and general versions also built in.", ST["cap"]))
    story.append(PageBreak())

    # PAGE 4 — 20 STRATEGIES
    story.append(sec("PAGE 4 — 20 MARKETING STRATEGIES (USD REVENUE MODEL)"))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "Every strategy below includes the exact USD revenue model, execution cost, "
        "timeline to first results, and realistic monthly USD potential. "
        "Ordered from zero-cost to paid. Start at the top.", ST["body"]))
    story.append(Spacer(1,0.15*cm))

    strategies = [
        (1, "Personal Network — The First 50 Paying Users",
         "Message 50 people you already know. Offer Founding Member pricing ($7.99/month locked for life). "
         "Don't ask if they want it — tell them what you built and give them a direct link. "
         "Be honest: 'I need 50 people to test this, you'll pay less than anyone ever will.' "
         "This is the fastest $400/month you will ever make.",
         "Direct Stripe payment at $7.99/month recurring. 50 people = $400 MRR, zero acquisition cost.",
         "$0", "48 hours", "$400/month immediately"),

        (2, "Reddit — The Highest Free Traffic Source",
         "Post in r/getdisciplined, r/productivity, r/Fitness, r/personalfinance, r/loseit. "
         "Title format: 'I built an AI that texts me every day on WhatsApp to keep me accountable — here's what happened.' "
         "Be genuine. Share your own experience. Add value in comments. "
         "One strong Reddit post = 300–1,500 trial sign-ups in 72 hours. No ad budget needed.",
         "Free trial sign-ups convert at 35–45% to $9.99/month. 500 sign-ups × 40% = 200 users = $2,000/month.",
         "$0", "72 hours", "$500–$2,000 per post"),

        (3, "Your Own TikTok Account — The Compounding Channel",
         "Post daily for 30 days. Content ideas: show a morning motivation message, share a user streak, "
         "reveal what a 90-day PDF plan looks like, do a 30-day challenge in public. "
         "TikTok's algorithm rewards consistency. After 30 videos you have enough data to know what works. "
         "Profile link → WhatsApp trial. Zero cost except 10 minutes a day.",
         "Bio link drives WhatsApp sign-ups → $9.99/month conversions. One viral video = $3,000–$10,000 MRR spike.",
         "$0", "2–4 weeks for traction", "$0–$5,000+/month (high variance)"),

        (4, "Instagram Reels — Screenshot Content That Spreads",
         "Post weekly: user streak screenshots (with permission), morning motivation images watermarked with your link, "
         "'what Grit sent me this morning' screen recordings. "
         "Reels showing authentic WhatsApp conversations outperform polished ads 3:1. "
         "Use trending audio. Post 3x per week minimum for the algorithm.",
         "Bio link to WhatsApp trial. Each viral Reel can drive 100–500 sign-ups. Zero production cost.",
         "$0", "1–2 weeks", "$200–$1,500/month from organic"),

        (5, "Micro-Influencer Seeding — Free Product for Organic Posts",
         "DM 30 creators with 5,000–50,000 followers in fitness, finance, study, or wellness. "
         "Offer 30 days of free Elite access ($19.99/month value). No obligation to post. "
         "Simply: 'I built this. I think your audience would love it. Try it free for a month.' "
         "30–40% will post organically if they genuinely like it. Organic posts convert 3x better than paid.",
         "20% recurring affiliate on every subscriber they refer. Their income grows as long as users stay. "
         "Your CAC is $2/month per referred user (vs $10–18 with paid ads).",
         "$0 (gifting free access costs you ~$0.10 in API costs)", "2–4 weeks", "$500–$3,000/month per active creator"),

        (6, "YouTube Creator Sponsorships — Long-Form Reviews",
         "Target YouTube creators in productivity, fitness, and self-improvement with 20K–500K subscribers. "
         "Offer a 90-second host-read sponsor slot in their video + 20% affiliate commission. "
         "Negotiate flat fee ($150–$1,500 depending on channel size) plus ongoing affiliate. "
         "YouTube audiences have the longest attention span and highest purchase intent of any platform.",
         "Flat fee (your cost) + 20% recurring affiliate on all subscribers driven. "
         "A 200K subscriber fitness channel can drive 200–800 sign-ups per video.",
         "$150–$1,500 per video", "1–2 weeks post-publish", "$1,000–$5,000/month per strong creator"),

        (7, "Podcast Sponsorships — Host-Read Ads",
         "Sponsor 3–5 podcasts in fitness, entrepreneurship, or personal development. "
         "Negotiate host-read ads (not pre-recorded spots — hosts reading your ad convert 4x better). "
         "Provide a unique promo code per podcast (GRIT30 = 30-day trial instead of 7). "
         "Track per podcast. Kill what doesn't convert, scale what does.",
         "Unique promo codes track sign-ups per show. Flat sponsorship fee is your cost. "
         "Podcast audiences convert at 2–4% of listeners (vs 0.1–0.5% for banner ads).",
         "$200–$2,000 per episode", "2–3 weeks", "$500–$3,000/month from 3–5 shows"),

        (8, "Referral Challenge — Turn Your Users Into a Sales Team",
         "When a user completes day 7, Grit automatically sends: 'You've been consistent for a week. "
         "Know one person who needs this? Send them your link — they get 30 days free, you get 20% every month.' "
         "Make the referral ask feel personal, not transactional. "
         "Social accountability is 10x more powerful than AI accountability — people want company.",
         "Referred users enter the same trial funnel → convert at 35–45% → referrer earns 20% recurring. "
         "Every active user is a potential $2/month ongoing income stream for themselves.",
         "$0 (built into product)", "Immediate", "$0.20–$2 per referred user per month, compounds infinitely"),

        (9, "Milestone Shareable Graphics — Passive Virality",
         "When users hit 7, 14, 30, or 90-day streaks, Grit auto-sends a branded shareable graphic: "
         "'I just hit 30 days straight with Grit.' Watermarked with your brand and wa.me link. "
         "Users post these to Instagram Stories and TikTok naturally — they're proud of their achievement. "
         "Every share reaches their followers. Zero cost to you. Happens automatically.",
         "Organic sign-ups from user shares → trial → $9.99/month conversions. "
         "One user with 5,000 Instagram followers sharing their 30-day graphic = 50–200 potential sign-ups.",
         "$0 (built into product)", "Immediate", "$50–$500/month per 100 active users, compounds with scale"),

        (10, "Product Hunt Launch — Tech Early Adopter Spike",
         "Launch on Product Hunt on a Tuesday or Wednesday. Prepare: compelling tagline, "
         "screenshots of the WhatsApp conversation, a sample PDF plan, and a demo video. "
         "Rally your first 50 founding members to upvote on launch day (message them directly). "
         "Top-5 finish = coverage in tech newsletters globally + 500–3,000 sign-ups in 24 hours.",
         "Free trial sign-ups from a highly engaged, vocal early-adopter audience. "
         "Tech newsletter coverage after a strong launch = additional organic reach for months.",
         "$0", "1 day (launch day)", "$2,000–$8,000 MRR spike from one launch"),

        (11, "Newsletter Sponsorships — High-Intent Audiences",
         "Sponsor issues of productivity and fitness newsletters: "
         "Morning Brew, Ali Abdaal's Sunday newsletter, The Hustle, Finimize, James Clear's 3-2-1. "
         "Negotiate a single issue first to test. Provide unique tracking URL. "
         "Newsletter readers click and act at 2–4x the rate of social media — they opted in to read content.",
         "Unique URLs track sign-ups per newsletter. Flat fee per issue is your cost. "
         "Good-fit newsletters convert at 1–3% of list size.",
         "$200–$3,000 per issue", "1 week post-send", "$500–$4,000 MRR per strong newsletter"),

        (12, "January New Year Campaign — The Best Month of the Year",
         "January is 400% above baseline for accountability and habit products. "
         "Plan from November: line up 5+ creators to post first week of January, "
         "schedule TikTok content in advance, pre-write Reddit posts, book newsletter spots. "
         "Offer the annual plan heavily ('New Year, Full Year — $59.99 locks in 12 months of accountability'). "
         "This single campaign can add 1,000–5,000 users in one week.",
         "Annual plan push drives $59.99 upfront per conversion. "
         "1,000 annual sign-ups = $59,990 cash in January. Monthly plan conversions stack on top.",
         "$1,000–$5,000 campaign budget", "Plan starts November, results January", "$15,000–$60,000 MRR added in January alone"),

        (13, "TikTok Paid Ads — Amplify Proven Organic Content",
         "Take your best-performing organic TikTok videos (100K+ views) and run them as paid ads. "
         "Proven organic content converts 2–3x better than purpose-made ad creative because it feels real. "
         "Start with $15/day, target 18–35, interests: fitness, self-improvement, journaling, habit tracking. "
         "Track CAC per ad set. Scale sets below $15 CAC. Kill everything above $20 CAC.",
         "Direct trial sign-ups tracked via UTM links. $9.99/month conversions. "
         "Profitable at any CAC below $67 (LTV at 8-month lifetime × $8.35/month profit).",
         "$15–$100/day", "1–2 weeks to see data", "$2,000–$10,000 MRR/month at $50/day spend"),

        (14, "Meta Retargeting — Recover Warm Leads",
         "Set up a Meta pixel or UTM tracking on your WhatsApp link. "
         "Anyone who clicked but didn't complete sign-up is a warm lead. "
         "Retarget them with a testimonial ad or a streak screenshot: 'Still thinking about it? "
         "10,000 people are checking in daily. Your 30-day trial is waiting.' "
         "Retargeting CPCs are 60–70% cheaper than cold prospecting.",
         "Retargeted trial sign-ups → $9.99/month conversions. "
         "Retargeting ROI is typically 3–5x better than cold ads on the same budget.",
         "$5–$30/day", "48 hours to start seeing results", "$500–$3,000/month at modest spend"),

        (15, "Corporate Wellness — B2B Contracts",
         "Approach HR managers and People teams at companies with 50–500 employees. "
         "Position Grit as an employee wellness benefit: 'Give your team an AI accountability coach for less than a daily coffee.' "
         "Companies have dedicated wellness budgets and make annual purchasing decisions. "
         "One 100-person company at $7.99/employee/month = $799/month with a 12-month contract.",
         "Annual B2B contracts invoiced directly. Zero per-user acquisition cost. "
         "Revenue is contractually guaranteed for 12 months. Zero churn risk during contract period.",
         "$0 (direct sales outreach)", "2–6 weeks sales cycle", "$800–$8,000/month per corporate client"),

        (16, "Gym and PT White-Label Partnerships",
         "Approach personal trainers and independent gyms. "
         "Offer a co-branded version: 'Your clients get Grit check-ins between sessions — "
         "branded as your coaching, priced as your add-on.' "
         "PT charges clients extra for the enhanced service. You split revenue 60/40 (you keep 60%). "
         "PT does zero tech work. You get a distribution channel with no marketing spend.",
         "60% of subscription revenue per client the PT brings on. "
         "PT with 20 clients paying $9.99/month = $120/month for you, $80/month for the PT.",
         "$0 (relationship-based)", "2–4 weeks per PT signed", "$100–$800/month per PT partner"),

        (17, "SEO Content Marketing — The Long Game",
         "Create a simple blog targeting: 'best accountability app 2026', 'AI life coach WhatsApp', "
         "'how to stick to your goals', 'accountability app no download'. "
         "Write genuinely useful 1,500-word articles. "
         "SEO takes 3–6 months to gain traction but then drives free sign-ups indefinitely — "
         "every article is a permanent acquisition asset.",
         "Organic Google traffic → WhatsApp trial sign-ups → $9.99/month conversions. "
         "Zero ongoing cost once published. A top-3 ranking for 'accountability app' = 500–2,000 monthly visitors.",
         "$0–$200/article (if outsourced)", "3–6 months", "$500–$3,000/month after 6 months"),

        (18, "Press and Earned Media — Zero-Cost PR",
         "Pitch your story to Forbes, Guardian, Business Insider, Wired, TechCrunch. "
         "The angle: 'The AI coach that texts you on WhatsApp — no app, no download, 10,000 users and growing.' "
         "Include retention data, real user testimonials, and the no-download angle as the contrarian hook. "
         "A single Forbes article can drive 2,000–15,000 sign-ups in 48 hours with zero spend.",
         "Earned media drives awareness and trial sign-ups at zero cost. "
         "Coverage also adds credibility that improves conversion rates from all other channels by 15–30%.",
         "$0 (time to write pitches)", "2–8 weeks (journalist response time)", "$3,000–$20,000 MRR spike per major article"),

        (19, "Accountability Partner Matching — Add-On Revenue",
         "At 5,000+ users, launch opt-in 'Accountability Partner' matching. "
         "Grit pairs two users with similar goals and timezone. "
         "They receive anonymous weekly updates about each other's progress. "
         "Charge $2/month extra as an add-on. Paired users churn at half the rate of solo users. "
         "This feature pays for itself many times over in reduced churn alone.",
         "$2/month add-on per paired user. "
         "At 10,000 users, 30% uptake = 3,000 paired users = $6,000 additional MRR at near-zero cost.",
         "$0 (built on existing infrastructure)", "Phase 2 — after 5,000 users", "$0 now, $3,000–$8,000/month at scale"),

        (20, "Annual Creator Partnership Deals — Scale What Works",
         "Once you have 3–5 micro-influencers driving consistent sign-ups, identify your top performer. "
         "Offer them an annual partnership: guaranteed monthly retainer ($500–$2,000) plus 20% affiliate. "
         "This locks in their promotion for 12 months, gives them income security, and gives you "
         "predictable acquisition. One locked-in creator driving 100 users/month = $1,000 MRR from that creator alone.",
         "Annual retainer (your fixed cost) + 20% affiliate (variable, performance-based). "
         "ROI positive if creator drives more than 25 paying users per month at $9.99.",
         "$500–$2,000/month retainer", "Negotiate after month 3–4", "$1,000–$5,000 MRR per anchor creator"),
    ]

    for num, title, body_text, how_paid, cost, timeline, potential in strategies:
        story.append(strat(num, title, body_text, how_paid, cost, timeline, potential))

    story.append(PageBreak())

    # PAGE 5 — ZERO TO $5K SPRINT
    story.append(sec("PAGE 5 — ZERO TO $5,000/MONTH: THE EXACT SPRINT"))
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(
        "At $9.99/month with 84% gross margin, you need 598 paying users. "
        "Here is the exact day-by-day, week-by-week plan to get there as fast as possible. "
        "No fluff. No theory. Just actions.", ST["body"]))

    story.append(Paragraph("Week-by-Week Action Plan", ST["h2"]))
    story.append(div())
    weekly = tbl([
        ["Week","Your Actions (Product)","Your Actions (Marketing)","Target Users","Target MRR"],
        ["Week 1\nDays 1–7",
         "Finalise API keys. Deploy to Railway. Test full onboarding flow yourself.",
         "Message 50 personal contacts. Offer $7.99 Founding Member rate. "
         "Write and post first Reddit thread in r/getdisciplined.",
         "30 paying","$240"],
        ["Week 2\nDays 8–14",
         "Fix anything broken from your own testing. Set up Stripe annual pricing.",
         "Post second Reddit thread in r/Fitness. "
         "DM 10 fitness micro-influencers (5K–50K followers) with free Elite access. "
         "Post first TikTok video.",
         "80 paying","$640"],
        ["Week 3\nDays 15–21",
         "Confirm scheduler sending morning messages correctly in all timezones. "
         "Check PDF delivery working.",
         "First influencer content may go live. "
         "Post on r/personalfinance and r/productivity. "
         "TikTok day 15 — 2 videos posted.",
         "150 paying","$1,200"],
        ["Week 4\nDays 22–28",
         "Monitor churn — if >20%, fix onboarding or check-in quality. "
         "Set up referral programme fully.",
         "Push annual plan to all trial users ending this week. "
         "DM 10 more influencers. "
         "Submit to Product Hunt (pick Tuesday).",
         "220 paying","$1,760"],
        ["Month 2\nWeeks 5–8",
         "Add streak freeze push notification at day 5 of streak. "
         "Set up B2B deck.",
         "Product Hunt goes live. "
         "2nd wave creator outreach. "
         "First TikTok paid ad at $15/day on best organic video. "
         "Reddit post in 2 new subreddits.",
         "400 paying","$3,200"],
        ["Month 3\nWeeks 9–12",
         "Review all unit economics. "
         "Set up newsletter sponsorship tracking URLs.",
         "First newsletter sponsorship live. "
         "3rd creator wave. "
         "Annual plan January prep begins. "
         "Pitch one corporate wellness client.",
         "598 paying","$5,000 ✅"],
    ], cw=[2.2*cm,5*cm,5*cm,2.3*cm,2*cm])
    story.append(weekly)

    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph("The 3 Things That Determine How Fast You Get There", ST["h2"]))
    story.append(div())
    three = tbl([
        ["Factor","What It Is","If Good","If Bad"],
        ["Trial conversion rate",
         "% of 7-day trial users who pay",
         "35%+: your acquisition cost is half what you think",
         "<20%: fix the day-7 payment message and trial experience first"],
        ["Month-2 retention",
         "% of month-1 subscribers still active in month 2",
         "80%+: users stick and your LTV is $80+",
         "<60%: the product isn't delivering — fix check-in quality before scaling"],
        ["Creator quality",
         "Whether your influencers actually use the product",
         "Authentic creators drive 3x the sign-ups of paid promoters",
         "Paid-only creators who don't use Grit will show in conversion — their audiences can tell"],
    ], cw=[3*cm,4.5*cm,4*cm,4*cm])
    story.append(three)

    story.append(Spacer(1,0.4*cm))
    story.append(box(
        "The infrastructure is built. The costs are $6/month until you have hundreds of users.\n"
        "At $9.99/month: 598 paying users = $5,000/month profit. Achievable in 60–90 days.\n\n"
        "Start tonight: message your 50 contacts. Post on Reddit. The rest follows.",
        bg=DARK, fg=WHITE, size=11))

    story.append(Paragraph(
        "All figures in USD. Costs based on current API and platform pricing as of June 2026. "
        "Financial projections are estimates. Built on brettyryangit/Claude GitHub repository.", ST["fn"]))

    doc.build(story, onFirstPage=hdr_ftr, onLaterPages=hdr_ftr)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build()
