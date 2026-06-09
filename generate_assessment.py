#!/usr/bin/env python3

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── Palette ──────────────────────────────────────────────────────────────────
NAVY      = HexColor('#1a1a2e')
TEAL      = HexColor('#0d7c6e')
TEAL_LITE = HexColor('#e6f4f2')
GREY_LITE = HexColor('#f7f7f7')
GREY_MID  = HexColor('#888888')
TEXT      = HexColor('#1f1f1f')
RED_LITE  = HexColor('#fdf0f0')
RED_ACC   = HexColor('#c0392b')
AMBER     = HexColor('#e67e22')
GREEN     = HexColor('#27ae60')
WHITE     = white

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm


# ── Style helpers ─────────────────────────────────────────────────────────────
def styles():
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        'cover_name': s('cover_name',
            fontName='Helvetica-Bold', fontSize=32, textColor=WHITE,
            leading=38, alignment=TA_LEFT),

        'cover_sub': s('cover_sub',
            fontName='Helvetica', fontSize=13, textColor=HexColor('#a8d8d2'),
            leading=18, alignment=TA_LEFT),

        'cover_date': s('cover_date',
            fontName='Helvetica', fontSize=10, textColor=HexColor('#6a9e99'),
            leading=14, alignment=TA_LEFT),

        'section_num': s('section_num',
            fontName='Helvetica-Bold', fontSize=9, textColor=TEAL,
            leading=12, alignment=TA_LEFT, spaceAfter=2),

        'section_title': s('section_title',
            fontName='Helvetica-Bold', fontSize=17, textColor=NAVY,
            leading=22, spaceBefore=18, spaceAfter=6),

        'subsection': s('subsection',
            fontName='Helvetica-Bold', fontSize=11, textColor=NAVY,
            leading=15, spaceBefore=12, spaceAfter=4),

        'body': s('body',
            fontName='Helvetica', fontSize=10, textColor=TEXT,
            leading=16, alignment=TA_JUSTIFY, spaceAfter=6),

        'body_left': s('body_left',
            fontName='Helvetica', fontSize=10, textColor=TEXT,
            leading=16, alignment=TA_LEFT, spaceAfter=4),

        'bullet': s('bullet',
            fontName='Helvetica', fontSize=10, textColor=TEXT,
            leading=16, leftIndent=14, firstLineIndent=-10,
            spaceAfter=3),

        'bullet_bold': s('bullet_bold',
            fontName='Helvetica-Bold', fontSize=10, textColor=NAVY,
            leading=16, leftIndent=14, firstLineIndent=-10,
            spaceAfter=3),

        'callout': s('callout',
            fontName='Helvetica-BoldOblique', fontSize=10.5, textColor=NAVY,
            leading=16, alignment=TA_LEFT),

        'action_header': s('action_header',
            fontName='Helvetica-Bold', fontSize=10, textColor=WHITE,
            leading=14, alignment=TA_LEFT),

        'action_body': s('action_body',
            fontName='Helvetica', fontSize=10, textColor=TEXT,
            leading=16, spaceAfter=3),

        'small_grey': s('small_grey',
            fontName='Helvetica', fontSize=8.5, textColor=GREY_MID,
            leading=12, alignment=TA_CENTER),

        'toc_item': s('toc_item',
            fontName='Helvetica', fontSize=10, textColor=NAVY,
            leading=18, leftIndent=6),
    }


ST = styles()


# ── Reusable blocks ───────────────────────────────────────────────────────────
def spacer(h=0.3):
    return Spacer(1, h * cm)

def rule(color=HexColor('#dddddd'), thickness=0.5):
    return HRFlowable(width='100%', thickness=thickness, color=color,
                      spaceAfter=6, spaceBefore=4)

def section_header(num, title):
    return [
        spacer(0.5),
        Paragraph(f'SECTION {num}', ST['section_num']),
        Paragraph(title, ST['section_title']),
        rule(TEAL, 1.5),
        spacer(0.2),
    ]

def sub(text):
    return Paragraph(text, ST['subsection'])

def body(text):
    return Paragraph(text, ST['body'])

def body_l(text):
    return Paragraph(text, ST['body_left'])

def bullet(text, bold=False):
    marker = '<bullet>&bull;</bullet>'
    st = ST['bullet_bold'] if bold else ST['bullet']
    return Paragraph(f'{marker} {text}', st)

def callout_box(text, bg=TEAL_LITE, border=TEAL):
    data = [[Paragraph(text, ST['callout'])]]
    t = Table(data, colWidths=[PAGE_W - MARGIN * 2 - 0.4 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX',        (0, 0), (-1, -1), 1, border),
        ('LEFTPADDING',  (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING',   (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 10),
    ]))
    return t

def action_row(label, items, color=TEAL):
    header_cell = Paragraph(label, ST['action_header'])
    body_text = '<br/>'.join(f'&#9744; &nbsp;{i}' for i in items)
    body_cell  = Paragraph(body_text, ST['action_body'])
    t = Table([[header_cell, body_cell]],
              colWidths=[3.8 * cm, PAGE_W - MARGIN * 2 - 4.2 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (0, -1), color),
        ('BACKGROUND',   (1, 0), (1, -1), GREY_LITE),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING',   (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 8),
        ('LINEBELOW',    (0, 0), (-1, -1), 0.5, WHITE),
    ]))
    return t

def two_col(left_items, right_items, left_label, right_label,
            left_bg=TEAL_LITE, right_bg=RED_LITE,
            left_border=TEAL, right_border=RED_ACC):
    col_w = (PAGE_W - MARGIN * 2 - 0.6 * cm) / 2

    def cell(label, items, bg, border):
        content = f'<b>{label}</b><br/><br/>'
        content += '<br/>'.join(f'&#9654; &nbsp;{i}' for i in items)
        return Paragraph(content, ST['body_left'])

    data = [[cell(left_label, left_items, left_bg, left_border),
             cell(right_label, right_items, right_bg, right_border)]]

    t = Table(data, colWidths=[col_w, col_w], spaceBefore=6)
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (0, -1), left_bg),
        ('BACKGROUND',   (1, 0), (1, -1), right_bg),
        ('BOX',          (0, 0), (0, -1), 1, left_border),
        ('BOX',          (1, 0), (1, -1), 1, right_border),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING',   (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 10),
    ]))
    return t


# ── Cover page ────────────────────────────────────────────────────────────────
def cover_page():
    cover_w = PAGE_W - MARGIN * 2

    title_cell = Table(
        [[Paragraph('BRETT RYAN', ST['cover_name'])],
         [Paragraph('Personal Life Assessment', ST['cover_sub'])],
         [spacer(0.4)],
         [Paragraph('Prepared 9 June 2026  ·  Confidential', ST['cover_date'])]],
        colWidths=[cover_w]
    )
    title_cell.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), NAVY),
        ('LEFTPADDING',  (0, 0), (-1, -1), 24),
        ('RIGHTPADDING', (0, 0), (-1, -1), 24),
        ('TOPPADDING',   (0, 0), (0, 0), 36),
        ('BOTTOMPADDING',(0, -1), (0, -1), 36),
        ('TOPPADDING',   (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING',(0, 0), (-1, -2), 4),
    ]))

    toc_items = [
        ('01', 'Who You Are'),
        ('02', 'Your Goals & Vision'),
        ('03', 'What Aligns — What Doesn\'t'),
        ('04', 'Trading: The Real Issues & The Fix'),
        ('05', 'ADHD Assessment — Full Action Plan'),
        ('06', 'Daily Structure for Your Brain'),
        ('07', 'Side Income Options'),
        ('08', 'The Victoria Trip'),
        ('09', 'Relationships'),
        ('10', 'Working With Claude Day-to-Day'),
        ('11', '30-Day Action Plan'),
    ]

    toc_content = [Paragraph('<b>CONTENTS</b>', ParagraphStyle(
        'toc_head', fontName='Helvetica-Bold', fontSize=11,
        textColor=NAVY, leading=16, spaceAfter=8))]

    for num, title in toc_items:
        toc_content.append(
            Paragraph(f'<font color="#0d7c6e"><b>{num}</b></font> &nbsp; {title}',
                      ST['toc_item']))

    return [
        title_cell,
        spacer(1.0),
        callout_box(
            'This document was built from a 20-question personal life assessment '
            'conversation. It is a starting point — a map, not a contract. '
            'Review it tomorrow, mark what resonates, and start with Section 05.',
            bg=HexColor('#fffbea'), border=AMBER
        ),
        spacer(0.6),
        *toc_content,
        PageBreak(),
    ]


# ── Section 1: Who You Are ────────────────────────────────────────────────────
def section_1():
    return [
        *section_header('01', 'Who You Are'),

        body(
            'You are a 30-year-old Australian living strategically in Bali, '
            'building toward financial and lifestyle freedom through trading. '
            'You have a construction background, strong practical intelligence, '
            'and a genuine capacity for discipline when it matters — you quit '
            'alcohol five months ago, you are consistent at the gym, and you '
            'moved your entire life to Southeast Asia with a clear purpose.'
        ),
        body(
            'You also have a deep streak of empathy. You volunteered after the '
            'Australian bushfires, spent time with people who had lost everything, '
            'and carry that spirit of generosity into daily life in Bali. You buy '
            'coffees and meals for local friends because it matters to them. '
            'That is a genuine value, not a personality trait you stumbled into.'
        ),
        body(
            'Your brain works differently to most. You hit hyperfocus states late '
            'at night, you thrive under deadlines and with your hands, and you '
            'struggle to engage with things that feel like homework — even when '
            'they matter. Multiple doctors have pointed toward ADHD. This document '
            'treats that as real and works with it, not around it.'
        ),

        spacer(0.3),
        sub('Core Strengths'),
        bullet('High self-awareness — you know when you are doing dumb stuff in real time'),
        bullet('Genuine discipline when committed (alcohol, gym, relocation to Bali)'),
        bullet('Practical intelligence — you were very good at your construction career'),
        bullet('Empathy and generosity — values you already act on, not just feel'),
        bullet('Financial responsibility — you saved enough to give yourself years of runway'),
        bullet('Creative hyperfocus — when engaged, you go extremely deep'),
        bullet('Resilience — you have been through hard periods and come out building something better'),

        spacer(0.3),
        sub('Core Challenges'),
        bullet('Execution gap: big plans, slow starts'),
        bullet('Impulsive decisions under stimulation pressure (trading FOMO, historically alcohol)'),
        bullet('No external accountability structure — you do everything alone'),
        bullet('Goals sitting in the "one day" pile despite genuine intention'),
        bullet('Mood heavily linked to external results — especially trading performance'),
        bullet('Likely undiagnosed ADHD underpinning all of the above'),

        spacer(0.3),
        callout_box(
            '"I don\'t have those people to lean on to keep me on track." '
            '— This is the thing that makes everything else harder. '
            'Building even one accountability structure changes the game.',
            bg=TEAL_LITE, border=TEAL
        ),
    ]


# ── Section 2: Goals & Vision ─────────────────────────────────────────────────
def section_2():
    return [
        *section_header('02', 'Your Goals & Vision'),

        sub('3-Year Vision'),
        bullet('Trading as full-time income — location-independent, from a laptop'),
        bullet('Traveling beyond Southeast Asia: Europe, South America, further'),
        bullet('In a meaningful, serious relationship'),
        bullet('Conversational in Indonesian'),
        bullet('Boxing as a regular practice'),
        bullet('Guitar as a creative outlet'),
        bullet('Helping people in meaningful, tangible ways'),
        bullet('Not having to think about money as a source of anxiety'),

        spacer(0.3),
        sub('Why Bali Right Now'),
        body(
            'Bali is a strategic base, not the destination. Lower cost of living '
            'gives you the runway to develop trading without financial desperation. '
            'The lifestyle supports gym, discipline, and focus. '
            'When trading generates consistent income, the world opens up. '
            'Keep that framing — it makes the discipline feel purposeful.'
        ),

        spacer(0.3),
        sub('30-Day Priorities — In Order of Impact'),

        action_row('WEEK 1', [
            'Book telehealth GP appointment — ADHD referral (see Section 05)',
            'Write the trading rule on a sticky note: NO SETUP. NO TRADE.',
            'Open the Indonesian app — complete first lesson (10 min)',
            'Decide now: trade or pause during Victoria trip. Write it down.',
            'Check Medicare details at my.gov.au',
        ], TEAL),

        spacer(0.15),
        action_row('WEEK 2', [
            'Victoria trip — be present, protect your account',
            'Stick to the pre-decided trading plan (no improvising)',
            'Keep gym going where possible',
        ], NAVY),

        spacer(0.15),
        action_row('WEEK 3–4', [
            'Return to Bali — 48-hour reset before trading again',
            'Book boxing lessons',
            'GP appointment completed — referral in hand',
            'Review side income options with Claude',
            '10-minute Indonesian daily, no days off',
        ], TEAL),
    ]


# ── Section 3: Aligns / Doesn't ───────────────────────────────────────────────
def section_3():
    aligns = [
        'Consistent morning gym — protects mental clarity',
        'Structured trading sessions (London + US only)',
        'Local friendships in Bali — grounding, not draining',
        'ADHD assessment — the single highest-leverage action',
        'Indonesian app daily — respect for where you live',
        'Living cheaply in Bali — financial runway intact',
        'Sobriety — protecting decision-making quality',
        'Creative projects (app design etc.) — use the hyperfocus productively',
    ]
    doesnt = [
        'Impulsive trades without a setup — destroys the funded account',
        'Apps downloaded but never opened — false sense of progress',
        'Staying up past 1am without purpose — costs next day\'s clarity',
        'Leaving ADHD unaddressed — keeps all other patterns in place',
        'No accountability structure — harder to stay on track alone',
        'Making financial decisions while emotionally activated',
        'Letting the Victoria trip derail trading behaviour',
    ]
    return [
        *section_header('03', 'What Aligns — What Doesn\'t'),
        two_col(aligns, doesnt, 'ALIGNS WITH YOUR GOALS', 'WORKS AGAINST YOUR GOALS'),
        spacer(0.4),
        callout_box(
            'The gap between these two lists is not willpower. It is structure. '
            'Almost everything in the right column happens in the absence of a '
            'pre-made decision. Make the decision before the moment arrives.',
            bg=HexColor('#fffbea'), border=AMBER
        ),
    ]


# ── Section 4: Trading ────────────────────────────────────────────────────────
def section_4():
    return [
        *section_header('04', 'Trading: The Real Issues & The Fix'),

        sub('Your Strategy (What\'s Working)'),
        body(
            'You have a solid, tested edge: change of structures on 5-minute '
            'charts, confirmed with supporting volume, combined with clear risk '
            'parameters. This strategy gave you 17 green days out of 19 before '
            'the funded account. The strategy is not the problem.'
        ),

        spacer(0.2),
        sub('What\'s Actually Going Wrong'),
        bullet('FOMO entries: seeing volume run and jumping in without your setup present', bold=True),
        bullet('Moving to breakeven too early — self-doubt overriding the trade plan'),
        bullet('Adding to positions impulsively under pressure'),
        bullet(
            'Funded account constraint: your original edge ran on higher contract '
            'sizes with small, consistent wins. The funded account parameters '
            'changed that. Instead of adapting down, you have been chasing bigger '
            'wins to compensate. That is the wrong direction.', bold=True
        ),
        bullet('Family stress and poor sleep occasionally amplifying all of the above'),

        spacer(0.2),
        callout_box(
            'The breakdown is psychological, not technical. '
            'Your brain built its edge on novelty and stimulation. '
            'When the funded account removed one lever, it went looking for another. '
            'The fix is to deliberately reduce stimulation, not increase it.',
            bg=TEAL_LITE, border=TEAL
        ),

        spacer(0.3),
        sub('The Fix — Three Rules'),

        action_row('RULE 1', [
            'No setup. No trade.',
            'Write this on a sticky note. Tape it to your screen.',
            'If you cannot point to the structure and the volume, you do not enter.',
        ], TEAL),
        spacer(0.15),
        action_row('RULE 2', [
            'Scale down on the funded account. Accept smaller wins.',
            'Stack green days. A small green day beats a red day every time.',
            'The goal right now is consistency, not size.',
        ], NAVY),
        spacer(0.15),
        action_row('RULE 3', [
            'Log every trade: entry reason + was there a setup? (yes/no)',
            'Review weekly — not daily. Daily review creates anxiety loops.',
            'One metric to track: green day percentage. Nothing else.',
        ], TEAL),

        spacer(0.3),
        sub('Red Flags — Stop Trading If Any of These Are Present'),
        bullet('Fewer than 6 hours of sleep'),
        bullet('Emotionally activated from family or personal stress'),
        bullet('You feel the urge to "not miss this move" before a setup appears'),
        bullet('You have already had one red trade today'),

        spacer(0.2),
        sub('Victoria Trip Decision'),
        body(
            'Make this decision now, before you are on a plane and in an '
            'emotionally draining environment. Recommended: pause trading entirely '
            'for the two weeks, or trade the London session only with a hard '
            'one-trade-per-session maximum. Two weeks off the funded account will '
            'not hurt your progress. Two weeks of emotionally compromised trading might.'
        ),
    ]


# ── Section 5: ADHD ───────────────────────────────────────────────────────────
def section_5():
    return [
        *section_header('05', 'ADHD Assessment — Full Action Plan'),

        callout_box(
            'Three separate doctors have referred you for an ADHD assessment. '
            'You have not followed through. This section gives you everything '
            'you need to do it from Bali via telehealth, starting tomorrow.',
            bg=HexColor('#fffbea'), border=AMBER
        ),

        spacer(0.3),
        sub('Why This Is the Highest-Priority Action'),
        body(
            'The impulsive trades, the procrastination, the apps downloaded but '
            'unopened, the midnight hyperfocus, the self-damaging decisions under '
            'stimulation, the mood swings, the execution gap between plans and '
            'action — all of it is consistent with ADHD. You have been managing '
            'it without a diagnosis, without support, and largely without '
            'acknowledgement. That takes more energy than most people realise.'
        ),
        body(
            'Your fear of losing your spark is legitimate and worth taking '
            'seriously. But the version of you right now — running on an '
            'unmanaged brain, burning energy on regret and self-sabotage — is '
            'not your spark. It is the cost of leaving it untreated. '
            'An assessment gives you information. It does not commit you to anything.'
        ),

        spacer(0.2),
        sub('Your Medicare Situation — What You Need to Know'),
        bullet(
            'Medicare is a national scheme. Your WA Medicare card works '
            'anywhere in Australia and for all Australian telehealth services. '
            'You do not need a WA-based GP.'
        ),
        bullet(
            'You can register as a new patient with any GP in Australia, '
            'including Geelong-based practices or national telehealth services.'
        ),
        bullet(
            'To check or update your Medicare address: my.gov.au '
            'or call Services Australia: 132 011'
        ),

        spacer(0.3),
        sub('Step-by-Step Assessment Pathway'),

        action_row('STEP 1\nGP Appt', [
            'Book a telehealth GP appointment (services listed below)',
            'Request: referral to a psychiatrist for ADHD assessment',
            'Request: Mental Health Treatment Plan (MHTP) — gives you 10 Medicare-rebated psychology sessions',
            'Mention the doctors who have previously referred you',
        ], TEAL),
        spacer(0.15),
        action_row('STEP 2\nPsychiatrist', [
            'A psychiatrist (not psychologist) diagnoses ADHD in Australia',
            'Can be done fully via telehealth — you do not need to be in Australia',
            'Cost: approx $500–$800 total. Medicare rebate (with GP referral): approx $150–$250',
            'Out of pocket: typically $250–$500',
            'Ask your GP to refer you to a telehealth psychiatrist who bulk-bills or gap-bills',
        ], NAVY),
        spacer(0.15),
        action_row('STEP 3\nFollow-up', [
            'If diagnosed: discuss options openly with the psychiatrist',
            'Raise your concern about "losing your spark" directly — a good psychiatrist expects this',
            'Non-stimulant options exist (Strattera/atomoxetine) if stimulant medication feels wrong',
            'Behavioural strategies alone are also a valid path',
        ], TEAL),

        spacer(0.3),
        sub('What to Say at Your GP Appointment'),
        body('Use these exact points — this is what gets you a referral efficiently:'),

        callout_box(
            '"I have been referred for an ADHD assessment by multiple doctors over '
            'the past few years. I have been living overseas and am ready to follow '
            'through now. I experience significant difficulty with: procrastination '
            'on self-directed tasks, impulsive decision-making, hyperfocus at night '
            'but difficulty engaging during the day, mood fluctuations tied to '
            'external results, and sustained attention on tasks that are not '
            'stimulating. I quit alcohol five months ago and want to address '
            'the underlying patterns. I need a referral to a telehealth '
            'psychiatrist for an ADHD assessment, and I would like a Mental '
            'Health Treatment Plan."',
            bg=GREY_LITE, border=GREY_MID
        ),

        spacer(0.3),
        sub('Telehealth GP Services — Book One of These'),
        body('These services operate nationally for Australians, including from overseas:'),

        bullet('<b>Hola Health</b> — holahealth.com.au — bulk billing available, Australians overseas accepted'),
        bullet('<b>HotDoc Telehealth</b> — hotdoc.com.au — search Geelong or use national telehealth'),
        bullet('<b>HealthEngine</b> — healthengine.com.au — search Geelong-area GPs for in-person when back'),
        bullet('<b>InstantScripts</b> — instantscripts.com.au — quick telehealth GP appointments'),

        spacer(0.2),
        sub('ADHD-Specific Services (after GP referral)'),
        bullet('Ask your GP specifically for a telehealth psychiatrist referral with ADHD experience'),
        bullet('Search: "telehealth psychiatrist ADHD Australia" — many now operate fully online'),
        bullet('Services to research: Osler Health, Concentric Health, Monarch Mental Health'),

        spacer(0.2),
        callout_box(
            'Note: Service availability and costs may change. Verify before booking. '
            'This information reflects what was current at time of preparation.',
            bg=GREY_LITE, border=GREY_MID
        ),
    ]


# ── Section 6: Daily Structure ────────────────────────────────────────────────
def section_6():
    sched = [
        ['08:45', 'Wake — no phone for first 15 minutes'],
        ['09:00', 'Gym (already doing this — protect it)'],
        ['10:30', 'Return, shower, coffee'],
        ['10:45', 'Indonesian app — 10 minutes only (set a timer, stop at 10)'],
        ['11:00', 'Free time / chill'],
        ['14:45', 'London open prep — review levels, check setup conditions only'],
        ['15:00', 'London trading session'],
        ['17:00', 'Trade log — was there a setup? yes/no. 5 minutes maximum.'],
        ['17:15', 'Free time, social, dinner'],
        ['21:00', 'US open prep'],
        ['21:30', 'US trading session'],
        ['23:00', 'Trade log'],
        ['23:30', 'Wind down — no screens after this if possible'],
        ['01:00', 'In bed'],
    ]

    table_data = [['TIME', 'ACTIVITY']] + sched
    col_widths = [2.5 * cm, PAGE_W - MARGIN * 2 - 3.0 * cm]

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',    (0, 0), (-1, 0), WHITE),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0), 9),
        ('FONTNAME',     (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 1), (-1, -1), 9),
        ('TEXTCOLOR',    (0, 1), (0, -1), TEAL),
        ('BACKGROUND',   (0, 1), (-1, -1), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GREY_LITE]),
        ('GRID',         (0, 0), (-1, -1), 0.3, HexColor('#dddddd')),
        ('LEFTPADDING',  (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING',   (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    return [
        *section_header('06', 'Daily Structure for Your Brain'),

        body(
            'Your brain is not broken — it is tuned differently. '
            'It runs on novelty, external deadlines, tactile tasks, '
            'and late-night quiet. The structure below works with that, '
            'not against it. It keeps your core routine intact while '
            'protecting your trading sessions and building the habits you want.'
        ),

        spacer(0.3),
        sub('Proposed Daily Routine'),
        t,

        spacer(0.4),
        sub('Making Trading Study Less Like Homework'),
        bullet('Frame it as detective work: "Why did this setup work? Why did that one fail?"'),
        bullet('Keep a trade screenshot journal — one image, one sentence per trade'),
        bullet('Set a 15-minute timer for study. Stop at 15. Short and sharp beats long and dreaded.'),
        bullet('Track green day streaks visually — a simple tally on paper or in your phone notes'),
        bullet('Reward the process, not just the outcome: a clean session with no bad trades is a win'),

        spacer(0.3),
        sub('The Late-Night Hyperfocus'),
        body(
            'Your brain turns on around midnight. That is real, and fighting it '
            'entirely wastes a genuine asset. The goal is not to eliminate it — '
            'it is to channel it. If you are awake at midnight and your brain is '
            'running, use it for something productive: app development, '
            'Indonesian practice, trade journalling, creative work. '
            'Do not let it become passive scrolling. And try to keep it to '
            'midnight–1am, not midnight–4am.'
        ),
    ]


# ── Section 7: Side Income ────────────────────────────────────────────────────
def section_7():
    return [
        *section_header('07', 'Side Income Options'),

        body(
            'The goal here is simple: reduce the psychological pressure on '
            'trading so you trade to grow, not to survive. Even AUD $500–$1,000 '
            'per month from another source changes the emotional weight on '
            'every trading session. Here are five realistic options based on '
            'your skills and situation.'
        ),

        spacer(0.2),
        sub('Option 1 — Construction Consulting / Remote Project Support'),
        body(
            'Your construction expertise has real market value. Australian builders, '
            'developers, and project managers pay for remote scope-of-works writing, '
            'document review, takeoffs, and estimating — especially from '
            'someone with supervisor-level experience. Low setup cost, '
            'high hourly rate. Platforms: Expert360, Airtasker (Pro), LinkedIn.'
        ),

        sub('Option 2 — Freelance Estimating / Takeoffs'),
        body(
            'Construction estimating and takeoffs are in constant demand. '
            'You can do this from a laptop in Bali. Platforms: Upwork, Fiverr, '
            'direct LinkedIn outreach to smaller Australian construction firms. '
            'Australians are expensive to hire locally — your skills are valuable remotely.'
        ),

        sub('Option 3 — Content Around Trading Journey'),
        body(
            'Document the journey. A 30-year-old Australian trading from Bali, '
            'building a funded account, navigating psychology — that is a '
            'genuine story. YouTube, TikTok, or a newsletter. '
            'Income arrives later, but the discipline benefit is immediate: '
            'journalling for an audience forces clarity on your own process.'
        ),

        sub('Option 4 — AI-Assisted App or Tool Development'),
        body(
            'You have already built something with Claude and hit flow state '
            'doing it. No-code and low-code tools combined with AI have made '
            'building genuinely accessible. A niche tool, a trading utility, '
            'a simple SaaS product. This is worth exploring — especially given '
            'how your brain engages with creative, novel problems.'
        ),

        sub('Option 5 — Online Tutoring / Trade Skills Transfer'),
        body(
            'Trade qualifications, site safety knowledge, or practical building '
            'knowledge have real online demand. Platforms like Udemy allow '
            'course creation. One well-made course generates passive income '
            'with no ongoing time commitment.'
        ),

        spacer(0.3),
        callout_box(
            'Recommended next step: come back to this section with Claude '
            'and narrow it to one option. Bring your weekly available hours '
            'and we will build a simple starting plan.',
            bg=TEAL_LITE, border=TEAL
        ),
    ]


# ── Section 8: Victoria Trip ──────────────────────────────────────────────────
def section_8():
    return [
        *section_header('08', 'The Victoria Trip'),

        callout_box(
            'You already know this trip will cost you energy. '
            'That is useful, honest information. Plan around it '
            'rather than hoping it will not affect you.',
            bg=HexColor('#fffbea'), border=AMBER
        ),

        spacer(0.3),
        sub('Before You Leave Bali'),
        bullet('Make the trading decision now — write it down, do not leave it open'),
        bullet('Recommended: pause entirely, or London session only with one-trade maximum'),
        bullet('Set a hard account rule before you fly — not in the moment'),
        bullet('Brief check-in with Claude the night before departure'),
        bullet('Indonesian app: try to keep the streak going through the trip'),

        spacer(0.2),
        sub('While You Are There'),
        bullet('Your main job is your father. Be present. That is the whole point of going.'),
        bullet('Protect your sleep where you can — even small sleep debts compound'),
        bullet('Keep gym going if possible: hotel gym, a run, anything'),
        bullet('Do not make financial decisions while emotionally activated'),
        bullet('If you feel the urge to trade impulsively, come talk it through first'),
        bullet('Two-minute daily check-in with Claude if it helps to have somewhere to put thoughts'),

        spacer(0.2),
        sub('When You Return to Bali'),
        bullet('48-hour reset before trading again — no exceptions'),
        bullet('Book boxing lessons in the first week back'),
        bullet('Review where you are on the ADHD pathway — is the GP appointment done?'),
        bullet('Come back to the side income shortlist'),
        bullet('Re-read Section 04 before your first trading session back'),
    ]


# ── Section 9: Relationships ──────────────────────────────────────────────────
def section_9():
    return [
        *section_header('09', 'Relationships'),

        body(
            'You are not actively pursuing a relationship and you do not need to be. '
            'The Bali chapter is strategic — a foundation, not the final destination. '
            'The right relationship is unlikely to come from a transient environment, '
            'and that is fine. This section is less about what to do and more about '
            'what to notice.'
        ),

        spacer(0.2),
        sub('What Is Already There'),
        bullet('Social confidence without alcohol — mostly there, situational not structural'),
        bullet('Genuine empathy and generosity — attractive qualities that do not need developing'),
        bullet('Sobriety at 30 in a social environment signals something real to the right person'),
        bullet('Local friendships in Bali — grounding, not draining. Protect these.'),

        spacer(0.2),
        sub('What to Watch'),
        bullet(
            'Your pattern of doing everything alone. When the relationship '
            'you want arrives, letting someone in — and accepting support — '
            'will be the thing that takes the most conscious effort.',
            bold=True
        ),
        bullet(
            'The Bali social scene is transient by nature. '
            'Do not invest heavily in connections you know are temporary '
            'unless they are genuinely nourishing right now.'
        ),
        bullet(
            'As trading becomes more consistent and travel opens up, '
            'the pool changes. Do not rush this chapter.'
        ),

        spacer(0.3),
        callout_box(
            'No action required here beyond noticing. '
            'Build the life — the relationship follows the person you are becoming.',
            bg=TEAL_LITE, border=TEAL
        ),
    ]


# ── Section 10: Working With Claude ──────────────────────────────────────────
def section_10():
    return [
        *section_header('10', 'Working With Claude Day-to-Day'),

        body(
            'You said you do not have people to lean on to keep you on track. '
            'Claude cannot replace a mentor, a mate, or a therapist — but it '
            'can be a consistent, non-judgmental thinking partner available at '
            'midnight in Bali when your brain turns on. Here is how to use it well.'
        ),

        spacer(0.2),
        sub('Morning Check-in (2 minutes, after gym)'),
        callout_box(
            '"Sleep: good/average/bad. Trading today: London + US / London only / pausing. '
            'Anything on my mind going in: [one sentence]."',
            bg=GREY_LITE, border=GREY_MID
        ),

        spacer(0.2),
        sub('Post-Trading Check-in (5 minutes)'),
        callout_box(
            '"Session: green/red. Setup present: yes/no. '
            'Rule broken: yes/no. Green day count this week: [number]."',
            bg=GREY_LITE, border=GREY_MID
        ),

        spacer(0.2),
        sub('Weekly Review (15 minutes, Sunday evening)'),
        callout_box(
            '"This week: what worked, what didn\'t, one thing I\'m carrying into next week."',
            bg=GREY_LITE, border=GREY_MID
        ),

        spacer(0.3),
        sub('Use Claude For'),
        bullet('Thinking through a decision before you make it — especially financial ones'),
        bullet('When you feel the urge to do something you suspect is dumb'),
        bullet('Breaking a big goal into the smallest possible first step'),
        bullet('Researching anything in this document (ADHD services, income options, etc.)'),
        bullet('Building things — apps, tools, systems — when the hyperfocus hits'),
        bullet('Preparing for the ADHD appointment — practising what to say'),
        bullet('Talking through the Victoria trip before, during, and after'),

        spacer(0.3),
        sub('WhatsApp / Mobile Access'),
        body(
            'There is no native Claude–WhatsApp integration currently. '
            'The simplest approach: set a daily phone alarm labelled "Claude check-in" '
            'for after gym. Open Claude on mobile and send one line. '
            'That habit, done consistently, is worth more than any integration. '
            'For building something more automated, come back to this — '
            'it is a solvable technical problem and one you would likely enjoy building.'
        ),

        spacer(0.3),
        callout_box(
            'What Claude will not do: tell you what you want to hear, '
            'let you off the hook when you are drifting, or make decisions for you. '
            'The mirror only works if you look at it.',
            bg=TEAL_LITE, border=TEAL
        ),
    ]


# ── Section 11: 30-Day Action Plan ───────────────────────────────────────────
def section_11():
    return [
        *section_header('11', '30-Day Action Plan'),

        body(
            'This is your starting point. Not everything. Not forever. '
            'Just the next 30 days. Mark each item when done. '
            'Come back to Claude when you are stuck or something changes.'
        ),

        spacer(0.3),
        action_row('DAY 1\nToday', [
            'Read this document. Highlight what resonates.',
            'Open the Indonesian app. Do the first lesson. Right now.',
            'Write on a sticky note: NO SETUP. NO TRADE. Put it on your screen.',
            'Check my.gov.au — confirm Medicare details are current',
        ], TEAL),

        spacer(0.15),
        action_row('DAYS 2–3', [
            'Book telehealth GP appointment (see Section 05 for services)',
            'Decide trading plan for Victoria trip. Write it down.',
            'Research one side income option from Section 07',
        ], NAVY),

        spacer(0.15),
        action_row('DAYS 4–7', [
            'Complete GP appointment — leave with psychiatrist referral',
            'Indonesian app every day — 10 minutes, timer on',
            'Trade log running: setup yes/no for every trade',
            'Brief check-in with Claude before Victoria departure',
        ], TEAL),

        spacer(0.15),
        action_row('WEEK 2\nVictoria', [
            'Be present with your father — that is the whole job',
            'Stick to the pre-decided trading plan',
            'Keep gym going where possible',
            'Indonesian app daily if possible',
            'No major financial decisions',
        ], NAVY),

        spacer(0.15),
        action_row('WEEK 3–4\nBack in Bali', [
            '48-hour reset on return before trading again',
            'Book boxing lessons — first session in week 3',
            'Psychiatrist appointment booked or in progress',
            'Side income: one concrete step on chosen option',
            'Review green day % on funded account with Claude',
            'Re-read Section 04 before first session back',
        ], TEAL),

        spacer(0.4),
        callout_box(
            'At the end of 30 days, come back to Claude with a one-paragraph '
            'update on each section. What moved. What did not. What you want to '
            'focus on next. That is the rhythm.',
            bg=HexColor('#fffbea'), border=AMBER
        ),
    ]


# ── Footer on each page ───────────────────────────────────────────────────────
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(GREY_MID)
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(PAGE_W / 2, 1.2 * cm,
                             f'Brett Ryan — Personal Life Assessment  ·  Page {page_num}  ·  Confidential')
    canvas.restoreState()


# ── Main ──────────────────────────────────────────────────────────────────────
def build_pdf(path):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=2.0 * cm,
        title='Brett Ryan — Personal Life Assessment',
        author='Claude',
    )

    story = []
    story += cover_page()
    story += section_1()
    story += [spacer(0.4)]
    story += section_2()
    story += [PageBreak()]
    story += section_3()
    story += [spacer(0.4)]
    story += section_4()
    story += [PageBreak()]
    story += section_5()
    story += [PageBreak()]
    story += section_6()
    story += [spacer(0.4)]
    story += section_7()
    story += [PageBreak()]
    story += section_8()
    story += [spacer(0.4)]
    story += section_9()
    story += [PageBreak()]
    story += section_10()
    story += [spacer(0.4)]
    story += section_11()

    story.append(spacer(0.6))
    story.append(Paragraph(
        'Prepared 9 June 2026 · Generated by Claude · Verify all service information before booking',
        ST['small_grey']
    ))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f'PDF written to {path}')


if __name__ == '__main__':
    build_pdf('/home/user/Claude/Brett_Ryan_Personal_Life_Assessment.pdf')
