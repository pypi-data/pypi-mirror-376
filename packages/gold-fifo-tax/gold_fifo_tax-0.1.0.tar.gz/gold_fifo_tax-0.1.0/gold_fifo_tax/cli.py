import argparse
import pandas as pd
from .core import prepare_data, fifo_buy_sell_matching

def main():
    parser = argparse.ArgumentParser(description="FIFO Buy-Sell Matching with CII Adjustment")
    parser.add_argument("input_csv", help="CSV file containing buy/sell transactions")
    parser.add_argument("cii_csv", help="CSV file containing CII table")
    parser.add_argument("-o", "--output", default="matched_output.csv", help="Output CSV file")

    args = parser.parse_args()

    buys, sells = prepare_data(args.cii_csv, args.input_csv)
    results = fifo_buy_sell_matching(buys, sells)

    results.to_csv(args.output, index=False)
    print(f"✅ Matching complete! Results saved to {args.output}")
