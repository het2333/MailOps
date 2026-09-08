from langchain_openai import ChatOpenAI

from app.core.config import Settings
from app.workflow.state import TriageResult


class DeepSeekTriageClient:
    """DeepSeek adapter using its OpenAI-compatible API."""

    def __init__(self, settings: Settings):
        if not settings.llm_configured:
            raise RuntimeError("DeepSeek is not configured; set OPENAI_API_KEY")
        self.model = ChatOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.openai_api_key.get_secret_value() if settings.openai_api_key else None,
            model=settings.llm_model,
            temperature=0,
        ).with_structured_output(TriageResult)

    def classify(self, subject: str, body: str) -> TriageResult:
        prompt = (
            "Classify this enterprise customer email as one of: order_status, quotation, meeting, faq, spam, other. "
            "Return only verified arguments explicitly present in the email. "
            f"Subject: {subject}\n\nBody: {body}"
        )
        result = self.model.invoke(prompt)
        return TriageResult.model_validate(result)
