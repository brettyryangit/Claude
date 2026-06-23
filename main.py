import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import create_tables
from app.routers import whatsapp, stripe_webhooks
from app.services.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Grit...")
    create_tables()
    start_scheduler()
    logger.info("Grit is live ✅")
    yield
    logger.info("Shutting down Grit...")


app = FastAPI(
    title="Grit — AI Accountability Coach",
    description="WhatsApp-native accountability coaching powered by Claude AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(whatsapp.router)
app.include_router(stripe_webhooks.router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": "Grit"}
