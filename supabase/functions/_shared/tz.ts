// Timezone helpers. We keep all timestamps in UTC in the DB and only convert to
// the user's local wall-clock when deciding *when* to send. Built on Intl so we
// don't pull in a date library.

interface LocalParts {
  year: number;
  month: number; // 1-12
  day: number;
  hour: number;
  minute: number;
  weekday: number; // 0=Sun .. 6=Sat
}

const WEEKDAY_INDEX: Record<string, number> = {
  Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6,
};

export function localParts(date: Date, tz: string): LocalParts {
  const fmt = new Intl.DateTimeFormat("en-US", {
    timeZone: tz,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    weekday: "short",
  });
  const parts = Object.fromEntries(
    fmt.formatToParts(date).map((p) => [p.type, p.value]),
  );
  return {
    year: Number(parts.year),
    month: Number(parts.month),
    day: Number(parts.day),
    // Intl can emit "24" at midnight; normalize to 0.
    hour: Number(parts.hour) % 24,
    minute: Number(parts.minute),
    weekday: WEEKDAY_INDEX[parts.weekday as string] ?? 0,
  };
}

/** "YYYY-MM-DD" in the user's local timezone. */
export function localDateKey(date: Date, tz: string): string {
  const p = localParts(date, tz);
  return `${p.year}-${pad(p.month)}-${pad(p.day)}`;
}

/** Minutes since local midnight. */
export function localMinutes(date: Date, tz: string): number {
  const p = localParts(date, tz);
  return p.hour * 60 + p.minute;
}

/**
 * A stable key for the user's local week (Monday-anchored). Used to decide
 * whether a weekly goal has already had its check-in this week. Good enough for
 * v1; not strict ISO-8601 week numbering.
 */
export function localWeekKey(date: Date, tz: string): string {
  const p = localParts(date, tz);
  // Days since Monday (treat Sunday as day 6).
  const fromMonday = (p.weekday + 6) % 7;
  const local = new Date(Date.UTC(p.year, p.month - 1, p.day));
  local.setUTCDate(local.getUTCDate() - fromMonday);
  return `${local.getUTCFullYear()}-${pad(local.getUTCMonth() + 1)}-${pad(local.getUTCDate())}`;
}

/** "HH:MM[:SS]" -> minutes since midnight. */
export function timeToMinutes(t: string): number {
  const [h, m] = t.split(":").map(Number);
  return (h || 0) * 60 + (m || 0);
}

function pad(n: number): string {
  return String(n).padStart(2, "0");
}
