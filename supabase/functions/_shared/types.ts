// Shared row types mirroring supabase/migrations/0001_initial_schema.sql.

export type SubscriptionStatus =
  | "trial"
  | "active"
  | "expired"
  | "cancelled"
  | "comped";

export type OnboardingState = "onboarding" | "active";
export type PreferredTone = "soft" | "direct";
export type Cadence = "daily" | "weekly";
export type GoalStatus = "active" | "paused" | "archived";
export type CheckinResponse = "yes" | "no" | "missed";
export type MessageDirection = "inbound" | "outbound";

export interface User {
  id: string;
  whatsapp_number: string;
  display_name: string | null;
  timezone: string;
  onboarding_state: OnboardingState;
  trial_started_at: string | null;
  subscription_status: SubscriptionStatus;
  created_at: string;
}

export interface Goal {
  id: string;
  user_id: string;
  title: string;
  why: string | null;
  obstacle: string | null;
  preferred_time: string | null; // "HH:MM:SS"
  preferred_tone: PreferredTone;
  cadence: Cadence;
  status: GoalStatus;
  created_at: string;
}

export interface Checkin {
  id: string;
  goal_id: string;
  scheduled_for: string;
  sent_at: string | null;
  responded_at: string | null;
  response: CheckinResponse | null;
  nudge_count: number;
  created_at: string;
}

export interface Pattern {
  id: string;
  goal_id: string;
  insight: string;
  surfaced_at: string | null;
  computed_at: string;
}

export interface MessageLog {
  id: string;
  user_id: string | null;
  direction: MessageDirection;
  body: string;
  checkin_id: string | null;
  provider_id: string | null;
  created_at: string;
}
