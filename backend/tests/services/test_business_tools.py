from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.seed import seed_business_data
from app.services.business_tools import BusinessTools


class FakeCalendar:
    def list_free_slots(self, _request: str) -> list[str]:
        return ["2026-09-09T14:00:00+00:00"]

    def create_event(self, _request: str) -> str:
        return "event-001"


def test_quote_is_calculated_from_persisted_product_price():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_business_data(session)

    quote = BusinessTools(session, calendar=FakeCalendar()).get_quote("MODEL-X", 100)

    assert quote.ok is True
    assert quote.data["total"] == "8900.00"
    assert quote.data["currency"] == "USD"


def test_unknown_product_never_creates_an_estimated_quote():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_business_data(session)

    quote = BusinessTools(session, calendar=FakeCalendar()).get_quote("MODEL-UNKNOWN", 100)

    assert quote.ok is False
    assert quote.data == {}
