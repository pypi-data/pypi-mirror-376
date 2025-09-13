import pandas as pd

def make_get_cii(consumer_infation_index_csv):
    """Return a function that looks up CII from only a date."""
    cii_df = pd.read_csv(consumer_infation_index_csv)
    CII_TABLE = dict(zip(cii_df["Year"], cii_df["CII"]))

    def get_cii(date):
        year = date.year
        if date.month < 4:  # before April, financial year counts as previous
            year -= 1
        return CII_TABLE.get(year, max(CII_TABLE.values()))

    return get_cii


def prepare_data(consumer_infation_index_csv, input_csv):
    """
    Prepares buys and sells DataFrames with rates and CII values.
    """
    df = pd.read_csv(input_csv, parse_dates=["Date"])

    buys = df[df["Type"].str.upper() == "B"].copy()
    sells = df[df["Type"].str.upper() == "S"].copy()

    # Compute rates
    buys["Rate"] = buys["TotalCost"] / buys["Quantity"]
    sells["Rate"] = sells["TotalCost"] / sells["Quantity"]

    # Add CII
    get_cii = make_get_cii(consumer_infation_index_csv)
    buys["CII_Buy"] = buys["Date"].apply(get_cii)
    sells["CII_Sell"] = sells["Date"].apply(get_cii)

    # Sort FIFO
    buys = buys.sort_values("Date").reset_index(drop=True)
    sells = sells.sort_values("Date").reset_index(drop=True)

    return buys, sells


def fifo_buy_sell_matching(buys, sells):
    results = []

    for _, sell in sells.iterrows():
        qty_to_sell = sell["Quantity"]
        sell_date = sell["Date"]
        sell_rate = sell["Rate"]
        cii_sell = sell["CII_Sell"]

        for i, buy in buys.iterrows():
            if qty_to_sell <= 0:
                break

            available_qty = buy["Quantity"]
            if available_qty == 0:
                continue

            matched_qty = min(qty_to_sell, available_qty)

            holding_months = (sell_date.year - buy["Date"].year) * 12 + (
                sell_date.month - buy["Date"].month
            )
            sale_value = matched_qty * sell_rate

            if holding_months >= 36:
                indexed_cost = matched_qty * buy["Rate"] * (cii_sell / buy["CII_Buy"])
                gain_type = "LTCG"
            else:
                indexed_cost = matched_qty * buy["Rate"]
                gain_type = "STCG"

            capital_gain = sale_value - indexed_cost

            results.append(
                {
                    "BuyDate": buy["Date"].date(),
                    "SellDate": sell_date.date(),
                    "QtyMatched": matched_qty,
                    "BuyRate": round(buy["Rate"], 2),
                    "SellRate": round(sell_rate, 2),
                    "HoldingMonths": holding_months,
                    "GainType": gain_type,
                    "SaleValue": round(sale_value, 2),
                    "IndexedCost": round(indexed_cost, 2),
                    "CapitalGain": round(capital_gain, 2),
                }
            )

            buys.at[i, "Quantity"] -= matched_qty
            qty_to_sell -= matched_qty

    return pd.DataFrame(results)
