from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import KnowledgeArticle, Order, Product


def seed_business_data(session: Session) -> None:
    """Populate the self-contained demo business records once."""

    if session.scalar(select(Order.id).limit(1)) is None:
        session.add_all(
            [
                Order(
                    po_number="PO-20260901",
                    customer_name="Tesla",
                    status="Shipped",
                    delivery_date="2026-09-12",
                    tracking_number="DHL123456",
                ),
                Order(
                    po_number="PO-002",
                    customer_name="Northstar Labs",
                    status="Processing",
                    delivery_date="2026-09-16",
                    tracking_number="Pending",
                ),
            ]
        )
    if session.scalar(select(Product.id).limit(1)) is None:
        session.add_all(
            [
                Product(model_code="MODEL-X", name="Model X Industrial Sensor", unit_price=Decimal("89.00"), currency="USD"),
                Product(model_code="MODEL-A", name="Model A Monitor", unit_price=Decimal("129.00"), currency="USD"),
            ]
        )
    if session.scalar(select(KnowledgeArticle.id).limit(1)) is None:
        session.add(
            KnowledgeArticle(
                title="Standard warranty policy",
                keywords="warranty,guarantee,repair,coverage",
                body="All Model X products include a two-year limited warranty covering manufacturing defects.",
            )
        )
    session.commit()
