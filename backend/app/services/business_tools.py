from decimal import Decimal
from typing import Any, Protocol

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import KnowledgeArticle, Order, Product


class CalendarPort(Protocol):
    def list_free_slots(self, request: str) -> list[str]: ...

    def create_event(self, request: str) -> str: ...


class ToolResult(BaseModel):
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class BusinessTools:
    """Strict data access tools used by the agent graph."""

    def __init__(self, session: Session, calendar: CalendarPort):
        self.session = session
        self.calendar = calendar

    def get_order(self, po_number: str) -> ToolResult:
        order = self.session.scalar(select(Order).where(Order.po_number == po_number.upper()))
        if order is None:
            return ToolResult(ok=False, error=f"No order found for {po_number}")
        return ToolResult(
            ok=True,
            data={
                "po_number": order.po_number,
                "customer_name": order.customer_name,
                "status": order.status,
                "delivery_date": order.delivery_date,
                "tracking_number": order.tracking_number,
            },
        )

    def get_quote(self, model_code: str, quantity: int) -> ToolResult:
        if quantity <= 0:
            return ToolResult(ok=False, error="Quantity must be greater than zero")
        product = self.session.scalar(select(Product).where(Product.model_code == model_code.upper()))
        if product is None:
            return ToolResult(ok=False, error=f"No product found for {model_code}")
        total = Decimal(product.unit_price) * quantity
        return ToolResult(
            ok=True,
            data={
                "model_code": product.model_code,
                "product_name": product.name,
                "quantity": quantity,
                "unit_price": f"{Decimal(product.unit_price):.2f}",
                "total": f"{total:.2f}",
                "currency": product.currency,
            },
        )

    def search_knowledge(self, query: str) -> ToolResult:
        query_terms = {term for term in query.lower().replace("?", " ").split() if len(term) > 2}
        articles = self.session.scalars(select(KnowledgeArticle)).all()
        ranked = sorted(
            articles,
            key=lambda article: len(query_terms & set(f"{article.title} {article.keywords}".lower().replace(",", " ").split())),
            reverse=True,
        )
        if not ranked or not query_terms:
            return ToolResult(ok=False, error="No knowledge article matched the request")
        article = ranked[0]
        score = len(query_terms & set(f"{article.title} {article.keywords}".lower().replace(",", " ").split()))
        if score == 0:
            return ToolResult(ok=False, error="No knowledge article matched the request")
        return ToolResult(ok=True, data={"title": article.title, "body": article.body})

    def find_calendar_slots(self, request: str) -> ToolResult:
        slots = self.calendar.list_free_slots(request)
        if not slots:
            return ToolResult(ok=False, error="No calendar slots are available")
        return ToolResult(ok=True, data={"slots": slots})

    def create_calendar_event(self, request: str) -> ToolResult:
        event_id = self.calendar.create_event(request)
        return ToolResult(ok=True, data={"event_id": event_id})
