import { useI18n } from "../i18n";
import type { EmailSummary } from "../types/api";

interface InboxListProps {
  emails: EmailSummary[];
  selectedId?: string;
  onSelect: (emailId: string) => void;
}

export function InboxList({ emails, selectedId, onSelect }: InboxListProps) {
  const { t } = useI18n();
  if (emails.length === 0) return <div className="empty-list">{t("inbox.empty")}</div>;
  return <div className="inbox-list">{emails.map((email) => <button className={`inbox-item ${selectedId === email.id ? "selected" : ""}`} key={email.id} onClick={() => onSelect(email.id)}>
    <span className="inbox-sender">{email.sender}</span>
    <strong>{email.subject || t("email.noSubject")}</strong>
    <span className={`status-dot ${email.status}`}>{t(`status.${email.status}`)}</span>
  </button>)}</div>;
}
