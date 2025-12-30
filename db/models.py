"""Database models (SQLAlchemy)."""

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    event_uid = Column(String, primary_key=True)

    sport = Column(String, nullable=False)
    league = Column(String, nullable=False)
    season = Column(String, nullable=True)

    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)

    kickoff_time = Column(DateTime(timezone=True), nullable=False)

    status = Column(
        Enum(
            "SCHEDULED",
            "LIVE",
            "FINISHED",
            "POSTPONED",
            "CANCELLED",
            name="event_status",
        ),
        nullable=False,
    )

    polymarket_id = Column(String, nullable=True)
    betfair_id = Column(String, nullable=True)
    betdex_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BinaryMarket(Base):
    __tablename__ = "binary_markets"

    id = Column(Integer, primary_key=True)

    platform = Column(
        Enum("polymarket", "betfair", name="platform"),
        nullable=False,
    )
    market_id = Column(String, nullable=False)

    event_uid = Column(String, ForeignKey("events.event_uid"), nullable=False)

    team = Column(String, nullable=False)
    question = Column(String, nullable=False)

    yes_means = Column(String, nullable=False)
    no_means = Column(String, nullable=False)

    price = Column(Float, nullable=False)
    liquidity = Column(Float, nullable=True)

    last_updated = Column(DateTime(timezone=True), nullable=False)

    event = relationship("Event")

    __table_args__ = (
        UniqueConstraint(
            "platform",
            "market_id",
            name="uq_platform_market",
        ),
    )


class Equivalence(Base):
    __tablename__ = "equivalences"

    id = Column(Integer, primary_key=True)

    event_uid = Column(String, ForeignKey("events.event_uid"), nullable=False)

    team = Column(String, nullable=False)

    polymarket_market_id = Column(String, nullable=False)
    betfair_market_id = Column(String, nullable=False)
    betfair_runner_id = Column(String, nullable=False)

    confidence = Column(Float, nullable=False)

    validated_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event")

    __table_args__ = (
        UniqueConstraint(
            "event_uid",
            "team",
            name="uq_event_team_equivalence",
        ),
    )


class ArbitrageEvaluation(Base):
    __tablename__ = "arbitrage_evaluations"

    id = Column(Integer, primary_key=True)

    event_uid = Column(String, nullable=False)
    team = Column(String, nullable=False)

    direction = Column(String, nullable=False)

    poly_market_id = Column(String, nullable=False)
    betdex_market_id = Column(String, nullable=False)
    betdex_selection_id = Column(String, nullable=False)

    pm_price = Column(Float, nullable=False)
    bdx_odds = Column(Float, nullable=False)

    stake_pm = Column(Float, nullable=False)
    hedge_size = Column(Float, nullable=False)

    worst_case_profit = Column(Float, nullable=False)
    profit_if_team_wins = Column(Float, nullable=False)
    profit_if_team_not_win = Column(Float, nullable=False)

    evaluated_at = Column(DateTime(timezone=True), server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)

    platform = Column(
        Enum("polymarket", "betfair", name="order_platform"),
        nullable=False,
    )

    market_id = Column(String, nullable=False)
    runner_id = Column(String, nullable=True)

    event_uid = Column(String, nullable=False)
    team = Column(String, nullable=False)

    side = Column(
        Enum("YES", "NO", "BACK", "LAY", name="order_side"),
        nullable=False,
    )

    price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)

    status = Column(
        Enum(
            "PENDING",
            "PLACED",
            "MATCHED",
            "CANCELLED",
            "FAILED",
            name="order_status",
        ),
        nullable=False,
    )

    placed_at = Column(DateTime(timezone=True), server_default=func.now())


class ExchangeMarket(Base):
    __tablename__ = "exchange_markets"

    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    event_uid = Column(String, nullable=False, index=True)

    market_id = Column(String, nullable=False)
    market_name = Column(String, nullable=True)

    selection_id = Column(String, nullable=False)
    selection_name = Column(String, nullable=False)

    best_back_odds = Column(Float, nullable=True)
    best_lay_odds = Column(Float, nullable=True)

    last_updated = Column(DateTime(timezone=True), nullable=False)
