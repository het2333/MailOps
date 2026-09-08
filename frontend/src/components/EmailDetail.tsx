import type { EmailDetail as EmailDetailType } from "../types/api";

export function EmailDetail({ email }: { email?: EmailDetailType }) {
  if (!email) return <section className="empty-detail"><span>✦</span><h2>Select an email</h2><p>Open a customer message to inspect the Agent’s verified work.</p></section>;
  const execution = email.execution;
  return <section className="email-detail"><div className="message-heading"><div><p className="eyebrow">CUSTOMER EMAIL</p><h1>{email.subject || "(No subject)"}</h1><p>From <b>{email.sender}</b> · Thread {email.gmail_thread_id}</p></div>{execution?.intent && <span className="intent-pill">{execution.intent.replace("_", " ")}</span>}</div>
    <article className="original-message"><p>{email.body}</p></article>
    {execution?.tool_result && <section className="verified-context"><p className="eyebrow">VERIFIED BUSINESS CONTEXT</p><div className="fact-grid">{Object.entries(execution.tool_result).map(([key, value]) => <div key={key}><span>{key.replaceAll("_", " ")}</span><b>{Array.isArray(value) ? value.join(", ") : String(value)}</b></div>)}</div></section>}
    {execution?.draft_reply && <section className="draft"><p className="eyebrow">PROPOSED REPLY</p><p>{execution.draft_reply}</p></section>}
  </section>;
}
