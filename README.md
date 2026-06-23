# Grit — AI Accountability Coach

WhatsApp-native accountability coaching powered by Claude AI. Users set goals, receive personalised 90-day plans as PDFs, and get daily check-ins + morning motivation directly in WhatsApp.

## Stack
- **Backend**: Python 3.11 + FastAPI
- **AI**: Anthropic Claude (Haiku for check-ins, Sonnet for onboarding/plans)
- **WhatsApp**: Meta WhatsApp Cloud API
- **Payments**: Stripe
- **Database**: PostgreSQL (via Railway)
- **Storage**: Cloudflare R2 (PDFs + motivation images)
- **Hosting**: Railway

## Setup

### 1. Environment Variables
Copy `.env.example` to `.env` and fill in all values:
```bash
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Locally
```bash
uvicorn main:app --reload --port 8000
```

### 4. Expose Locally for WhatsApp Webhook Testing
```bash
# Install ngrok, then:
ngrok http 8000
# Copy the https URL → paste into Meta WhatsApp webhook config
```

### 5. Deploy to Railway
- Connect this GitHub repo to Railway
- Add all environment variables in Railway dashboard
- Railway auto-deploys on every push

## WhatsApp Webhook Setup
1. Go to Meta Business Suite → WhatsApp Manager → Configuration
2. Set webhook URL: `https://your-railway-url.railway.app/webhook`
3. Set verify token: matches `WHATSAPP_VERIFY_TOKEN` in your `.env`
4. Subscribe to: `messages`

## Stripe Setup
1. Create 4 products in Stripe: Core (£4.99/mo), Pro (£9.99/mo), Elite (£19.99/mo), Annual (£59.99/yr)
2. Copy each Price ID into `.env`
3. Set webhook endpoint: `https://your-railway-url.railway.app/stripe/webhook`
4. Subscribe to: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`

## User Flow
1. User texts the WhatsApp number
2. 10-question onboarding via Claude
3. 90-day personalised plan generated + sent as PDF
4. 7-day free trial begins
5. Daily check-ins + morning motivation (quote + image) on schedule
6. Stripe payment link sent at end of trial
7. Streak tracking, milestone celebrations, weekly summaries

## Pricing
| Tier | Price | Features |
|------|-------|----------|
| Core | £4.99/mo | 3 goals, 2 check-ins/day |
| Pro | £9.99/mo | Unlimited goals, 3 check-ins, analytics |
| Elite | £19.99/mo | Everything + weekly coaching recap |
| Annual | £59.99/yr | Pro features, best value |
