from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

# Config: tune these once you see outputs.
BETDEX_COMMISSION = 0.03
POLY_FEE = 0.0
POLY_SLIPPAGE = 0.002
MIN_EUR_PROFIT = 0.10
BASE_STAKE_EUR = 5.0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ArbResult:
    event_uid: str
    team: str
    poly_market_id: str
    betdex_market_id: str
    betdex_selection_id: str
    direction: str
    pm_price: float
    bdx_odds: float
    stake_pm: float
    lay_stake_or_back_stake: float
    worst_case_profit: float
    profit_if_team_wins: float
    profit_if_team_not_win: float


def _pm_yes_profit(stake: float, p_yes: float, fee: float, slip: float) -> float:
    eff = p_yes + fee + slip
    return stake * (1.0 - eff)


def _pm_yes_loss(stake: float, p_yes: float, fee: float, slip: float) -> float:
    eff = p_yes + fee + slip
    return -stake * eff


def _pm_no_profit(stake: float, p_no: float, fee: float, slip: float) -> float:
    eff = p_no + fee + slip
    return stake * (1.0 - eff)


def _pm_no_loss(stake: float, p_no: float, fee: float, slip: float) -> float:
    eff = p_no + fee + slip
    return -stake * eff


def _bdx_back_profit(stake: float, odds: float, commission: float) -> float:
    gross_profit = stake * (odds - 1.0)
    return gross_profit * (1.0 - commission)


def _bdx_back_loss(stake: float) -> float:
    return -stake


def _bdx_lay_profit(lay_stake: float, commission: float) -> float:
    return lay_stake * (1.0 - commission)


def _bdx_lay_loss(lay_stake: float, odds: float) -> float:
    liability = lay_stake * (odds - 1.0)
    return -liability


def _solve_lay_stake_for_balance(
    stake_pm: float,
    p_yes: float,
    odds_lay: float,
    commission: float,
    fee: float,
    slip: float,
) -> float:
    A = _pm_yes_profit(stake_pm, p_yes, fee, slip)
    B = _pm_yes_loss(stake_pm, p_yes, fee, slip)
    denom = odds_lay - commission
    if denom <= 0:
        return 0.0
    return (A - B) / denom


def _solve_back_stake_for_balance(
    stake_pm: float,
    p_no: float,
    odds_back: float,
    commission: float,
    fee: float,
    slip: float,
) -> float:
    pm_loss_win = _pm_no_loss(stake_pm, p_no, fee, slip)
    bdx_profit_win = _bdx_back_profit(1.0, odds_back, commission)

    pm_profit_lose = _pm_no_profit(stake_pm, p_no, fee, slip)
    bdx_loss_lose = _bdx_back_loss(1.0)

    denom = bdx_profit_win + 1.0
    if denom <= 0:
        return 0.0
    return (pm_profit_lose - pm_loss_win) / denom


def evaluate_arbs(session) -> list[ArbResult]:
    from db.models import ArbitrageEvaluation, BinaryMarket, ExchangeMarket

    pm_rows = (
        session.query(BinaryMarket)
        .filter(BinaryMarket.platform == "polymarket")
        .all()
    )
    ex_rows = session.query(ExchangeMarket).all()

    pm_index: dict[tuple[str, str], tuple[float, Optional[float], str]] = {}
    for pm in pm_rows:
        if not pm.event_uid or not pm.team or pm.price is None:
            continue
        p_yes = float(pm.price)
        p_no = getattr(pm, "price_no", None)
        if p_no is None:
            p_no = 1.0 - p_yes
        pm_index[(pm.event_uid, pm.team)] = (p_yes, float(p_no), pm.market_id)

    ex_index: dict[tuple[str, str], tuple[str, str, Optional[float], Optional[float]]] = {}
    for ex in ex_rows:
        if not ex.event_uid or not ex.selection_name:
            continue
        key = (ex.event_uid, ex.selection_name)
        ex_index[key] = (
            ex.market_id,
            ex.selection_id,
            ex.best_back_odds,
            ex.best_lay_odds,
        )

    pm_uids = {uid for (uid, _team) in pm_index.keys()}
    ex_uids = {uid for (uid, _team) in ex_index.keys()}
    overlap = pm_uids & ex_uids
    print(
        f"[arb] pm markets: {len(pm_index)} | ex markets: {len(ex_index)} | "
        f"overlapping event_uids: {len(overlap)}"
    )

    results: list[ArbResult] = []

    for key, (p_yes, p_no, pm_id) in pm_index.items():
        if key not in ex_index:
            continue

        event_uid, team = key
        market_id, selection_id, best_back, best_lay = ex_index[key]
        stake_pm = BASE_STAKE_EUR

        if best_lay and best_lay > 1.01:
            lay_stake = _solve_lay_stake_for_balance(
                stake_pm=stake_pm,
                p_yes=p_yes,
                odds_lay=float(best_lay),
                commission=BETDEX_COMMISSION,
                fee=POLY_FEE,
                slip=POLY_SLIPPAGE,
            )
            profit_win = _pm_yes_profit(
                stake_pm, p_yes, POLY_FEE, POLY_SLIPPAGE
            ) + _bdx_lay_loss(lay_stake, float(best_lay))
            profit_not = _pm_yes_loss(
                stake_pm, p_yes, POLY_FEE, POLY_SLIPPAGE
            ) + _bdx_lay_profit(lay_stake, BETDEX_COMMISSION)
            worst = min(profit_win, profit_not)

            if worst >= MIN_EUR_PROFIT:
                results.append(
                    ArbResult(
                        event_uid=event_uid,
                        team=team,
                        poly_market_id=pm_id,
                        betdex_market_id=market_id,
                        betdex_selection_id=selection_id,
                        direction="PM_YES_vs_BDX_LAY",
                        pm_price=p_yes,
                        bdx_odds=float(best_lay),
                        stake_pm=stake_pm,
                        lay_stake_or_back_stake=lay_stake,
                        worst_case_profit=worst,
                        profit_if_team_wins=profit_win,
                        profit_if_team_not_win=profit_not,
                    )
                )

        if best_back and best_back > 1.01:
            back_stake = _solve_back_stake_for_balance(
                stake_pm=stake_pm,
                p_no=p_no,
                odds_back=float(best_back),
                commission=BETDEX_COMMISSION,
                fee=POLY_FEE,
                slip=POLY_SLIPPAGE,
            )
            profit_win = _pm_no_loss(
                stake_pm, p_no, POLY_FEE, POLY_SLIPPAGE
            ) + _bdx_back_profit(back_stake, float(best_back), BETDEX_COMMISSION)
            profit_not = _pm_no_profit(
                stake_pm, p_no, POLY_FEE, POLY_SLIPPAGE
            ) + _bdx_back_loss(back_stake)
            worst = min(profit_win, profit_not)

            if worst >= MIN_EUR_PROFIT:
                results.append(
                    ArbResult(
                        event_uid=event_uid,
                        team=team,
                        poly_market_id=pm_id,
                        betdex_market_id=market_id,
                        betdex_selection_id=selection_id,
                        direction="PM_NO_vs_BDX_BACK",
                        pm_price=p_no,
                        bdx_odds=float(best_back),
                        stake_pm=stake_pm,
                        lay_stake_or_back_stake=back_stake,
                        worst_case_profit=worst,
                        profit_if_team_wins=profit_win,
                        profit_if_team_not_win=profit_not,
                    )
                )

    print(
        f"[arb] opportunities found: {len(results)} "
        f"(threshold: EUR {MIN_EUR_PROFIT:.2f})"
    )
    for result in results:
        row = ArbitrageEvaluation(
            event_uid=result.event_uid,
            team=result.team,
            direction=result.direction,
            poly_market_id=result.poly_market_id,
            betdex_market_id=result.betdex_market_id,
            betdex_selection_id=result.betdex_selection_id,
            pm_price=result.pm_price,
            bdx_odds=result.bdx_odds,
            stake_pm=result.stake_pm,
            hedge_size=result.lay_stake_or_back_stake,
            worst_case_profit=result.worst_case_profit,
            profit_if_team_wins=result.profit_if_team_wins,
            profit_if_team_not_win=result.profit_if_team_not_win,
            evaluated_at=_utcnow(),
        )
        session.add(row)
    session.commit()
    return sorted(results, key=lambda r: r.worst_case_profit, reverse=True)
