export type EmailStatus = "needs_attention" | "awaiting_approval" | "completed" | "failed";
export type ExecutionStatus = "queued" | "running" | "waiting_for_approval" | "completed" | "rejected" | "failed";

export interface Execution {
  id: string;
  status: ExecutionStatus;
  current_node: string;
  intent?: string;
  confidence?: number;
  draft_reply?: string;
  tool_result?: Record<string, unknown>;
  risk_reasons?: string[];
  error_message?: string;
  sent_at?: string;
}

export interface EmailSummary {
  id: string;
  sender: string;
  subject: string;
  status: EmailStatus;
  received_at: string;
  execution_status?: ExecutionStatus;
}

export interface EmailDetail extends EmailSummary {
  gmail_thread_id: string;
  body: string;
  execution?: Execution;
}

export interface Approval {
  id: string;
  status: "pending" | "approved" | "rejected";
  draft_reply: string;
  action_summary: string;
  risk_reasons: string[];
  email_id: string;
  email_subject: string;
  email_sender: string;
}

export interface IntegrationStatus {
  configured: boolean;
  connected: boolean;
  account_email?: string | null;
  last_sync_cursor?: string | null;
}

export interface Dashboard {
  counts: Partial<Record<EmailStatus, number>>;
  activity: Array<{ type: string; detail?: Record<string, unknown>; created_at: string }>;
}
