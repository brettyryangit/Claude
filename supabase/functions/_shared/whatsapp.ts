// WhatsApp messaging layer.
//
// The rest of the codebase talks to `WhatsAppClient` — an interface — so the
// BSP (Business Solution Provider) is a swappable detail. v1 ships a Twilio
// implementation because Twilio has the cleanest developer sandbox and full
// programmatic control. To move to Wati / 360dialog / ManyChat later, write a
// new class implementing WhatsAppClient and change getWhatsAppClient(); nothing
// else changes.
//
// Twilio sandbox setup: https://www.twilio.com/docs/whatsapp/sandbox
//   TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM (e.g.
//   "whatsapp:+14155238886" for the sandbox number).

export interface InboundMessage {
  from: string; // E.164, e.g. "+61412345678" (the "whatsapp:" prefix stripped)
  body: string;
  providerId: string | null; // BSP message id, for logging
}

export interface WhatsAppClient {
  /** Send a text message. Returns the BSP message id if available. */
  send(to: string, body: string): Promise<string | null>;
  /** Parse an inbound webhook request body into a normalized message. */
  parseInbound(req: Request): Promise<InboundMessage>;
}

// --- Twilio implementation -------------------------------------------------

const TWILIO_PREFIX = "whatsapp:";

class TwilioWhatsAppClient implements WhatsAppClient {
  private accountSid: string;
  private authToken: string;
  private from: string;

  constructor() {
    this.accountSid = required("TWILIO_ACCOUNT_SID");
    this.authToken = required("TWILIO_AUTH_TOKEN");
    this.from = required("TWILIO_WHATSAPP_FROM"); // e.g. whatsapp:+14155238886
  }

  async send(to: string, body: string): Promise<string | null> {
    const url =
      `https://api.twilio.com/2010-04-01/Accounts/${this.accountSid}/Messages.json`;
    const form = new URLSearchParams({
      From: this.from,
      To: to.startsWith(TWILIO_PREFIX) ? to : `${TWILIO_PREFIX}${to}`,
      Body: body,
    });
    const res = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: "Basic " +
          btoa(`${this.accountSid}:${this.authToken}`),
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: form,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Twilio send failed (${res.status}): ${text}`);
    }
    const json = await res.json();
    return json.sid ?? null;
  }

  async parseInbound(req: Request): Promise<InboundMessage> {
    // Twilio posts inbound messages as application/x-www-form-urlencoded.
    const form = await req.formData();
    const from = String(form.get("From") ?? "").replace(TWILIO_PREFIX, "");
    const body = String(form.get("Body") ?? "");
    const providerId = form.get("MessageSid")
      ? String(form.get("MessageSid"))
      : null;
    return { from, body, providerId };
  }
}

function required(name: string): string {
  const v = Deno.env.get(name);
  if (!v) throw new Error(`${name} must be set.`);
  return v;
}

export function getWhatsAppClient(): WhatsAppClient {
  // Single switch point for swapping BSP. Could branch on a WHATSAPP_PROVIDER
  // env var once a second provider exists.
  return new TwilioWhatsAppClient();
}
