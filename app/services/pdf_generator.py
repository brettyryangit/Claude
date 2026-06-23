import boto3
import logging
import uuid
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_plan_pdf(user_name: str, goal_title: str, plan_content: str) -> BytesIO:
    """Generate a PDF from the plan content and return as BytesIO."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    brand_color = colors.HexColor("#1a1a2e")
    accent_color = colors.HexColor("#e94560")

    title_style = ParagraphStyle(
        "GritTitle",
        parent=styles["Title"],
        fontSize=28,
        textColor=brand_color,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "GritSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=accent_color,
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "GritHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=brand_color,
        spaceBefore=16,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "GritBody",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#333333"),
        spaceAfter=8,
        leading=16,
        alignment=TA_LEFT,
    )

    story = []

    story.append(Paragraph("GRIT", title_style))
    story.append(Paragraph("Your Personal Accountability Coach", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=accent_color))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"90-Day Plan for {user_name}", heading_style))
    story.append(Paragraph(f"Goal: {goal_title}", body_style))
    story.append(Paragraph(f"Created: {datetime.now().strftime('%d %B %Y')}", body_style))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#eeeeee")))
    story.append(Spacer(1, 0.5 * cm))

    # Parse plan content into sections
    for line in plan_content.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.2 * cm))
            continue
        if line.startswith("#"):
            clean = line.lstrip("#").strip()
            story.append(Paragraph(clean, heading_style))
        else:
            story.append(Paragraph(line, body_style))

    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=accent_color))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Built with Grit — Your AI Accountability Coach", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


async def upload_pdf_to_r2(pdf_buffer: BytesIO, filename: str) -> str:
    """Upload PDF to Cloudflare R2 and return public URL."""
    s3_client = boto3.client(
        "s3",
        endpoint_url=f"https://{settings.CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
        aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
        region_name="auto",
    )

    key = f"plans/{filename}"
    s3_client.upload_fileobj(
        pdf_buffer,
        settings.CLOUDFLARE_R2_BUCKET,
        key,
        ExtraArgs={"ContentType": "application/pdf"},
    )

    return f"{settings.CLOUDFLARE_R2_PUBLIC_URL}/{key}"


async def create_and_upload_plan(user_name: str, goal_title: str, plan_content: str) -> str:
    """Full pipeline: generate PDF and upload to R2, return URL."""
    pdf_buffer = generate_plan_pdf(user_name, goal_title, plan_content)
    filename = f"{uuid.uuid4()}-{user_name.lower().replace(' ', '-')}-plan.pdf"
    url = await upload_pdf_to_r2(pdf_buffer, filename)
    logger.info(f"Plan PDF uploaded for {user_name}: {url}")
    return url
