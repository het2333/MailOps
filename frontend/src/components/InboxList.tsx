import type { EmailSummary } from "../types/api";

interface InboxListProps {
  emails: EmailSummary[];
  selectedId?: string;
  onSelect: (emailId: string) => void;
}

const statusText: Record<string, string> = {
  needs_attention: "Needs attention",
  awaiting_approval: "Awaiting approval",
  completed: "Completed",
  failed: "Needs attention",
};

export function InboxList({ emails, selectedId, onSelect }: InboxListProps) {
  if (emails.length === 0) return <div className="empty-list">No synced customer email yet.</div>;
  return <div className="inbox-list">{emails.map((email) => <button className={`inbox-item ${selectedId === email.id ? "selected" : ""}`} key={email.id} onClick={() => onSelect(email.id)}>
    <span className="inbox-sender">{email.sender}</span>
    <strong>{email.subject || "(No subject)"}</strong>
    <span className={`status-dot ${email.status}`}>{statusText[email.status]}</span>
  </button>)}</div>;
}
