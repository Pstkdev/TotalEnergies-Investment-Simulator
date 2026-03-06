from src.tte_simulation import TTESimulation


def main() -> None:

    sim = TTESimulation(
        initial_share_price=55.0,
        initial_shares=10,
        monthly_investment=0,
        reinvest_dividends=False,
        initial_dividend=3.0,
        dividend_growth_rate=0.02,
        years=20,
        start_year=2026,
        regime_scenario="Random",
        mean_price_high=70.0,
        mean_price_low=40.0,
        reversion_speed=0.25,
        vol_high=0.25,
        vol_low=0.20,
        p_high=0.5,
        seed=42,
    )

    df = sim.run_simulation()

    last = df.iloc[-1]
    final_value = float(last["Portfolio value"])
    final_shares = int(last["Total shares"])
    total_invested = float(last["Total invested"])
    total_div = float(last["Total dividends received"])
    final_cash = float(last["Cash"])

    total_return_pct = 0.0
    if total_invested > 0:
        total_return_pct = (final_value - total_invested) / total_invested * 100.0

    print("\n--- Summary ---")
    print(f"Final portfolio value: €{final_value:,.2f}")
    print(f"Final shares: {final_shares}")
    print(f"Final cash: €{final_cash:,.2f}")
    print(f"Total invested: €{total_invested:,.2f}")
    print(f"Total dividends received: €{total_div:,.2f}")
    print(f"Total return: {total_return_pct:.2f}%")

    print("\n--- Last 10 rows ---")
    print(df.tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
