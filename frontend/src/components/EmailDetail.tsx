import { useI18n } from "../i18n";
import type { EmailDetail as EmailDetailType } from "../types/api";

export function EmailDetail({ email }: { email?: EmailDetailType }) {
  const { t } = useI18n();
  if (!email) return <section className="empty-detail"><span>✦</span><h2>{t("email.select")}</h2><p>{t("email.selectHint")}</p></section>;
  const execution = email.execution;
  return <section className="email-detail"><div className="message-heading"><div><p className="eyebrow">{t("email.customer")}</p><h1>{email.subject || t("email.noSubject")}</h1><p>{t("email.from")} <b>{email.sender}</b> · {t("email.thread")} {email.gmail_thread_id}</p></div>{execution?.intent && <span className="intent-pill">{t(`intent.${execution.intent}`)}</span>}</div>
    <article className="original-message"><p>{email.body}</p></article>
    {execution?.tool_result && <section className="verified-context"><p className="eyebrow">{t("email.context")}</p><div className="fact-grid">{Object.entries(execution.tool_result).map(([key, value]) => <div key={key}><span>{t(`fact.${key}`)}</span><b>{Array.isArray(value) ? value.join(", ") : String(value)}</b></div>)}</div></section>}
    {execution?.draft_reply && <section className="draft"><p className="eyebrow">{t("email.reply")}</p><p>{execution.draft_reply}</p></section>}
  </section>;
}
