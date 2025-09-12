from __future__ import annotations
import argparse
from .fifaindex import run_full_scrape

def main() -> None:
    p = argparse.ArgumentParser(
        prog="sportscraper",
        description="Scrape FIFAIndex: teams, players, and player stats into CSVs."
    )
    p.add_argument("--start", type=int, default=16, help="Start FIFA infix year (e.g., 16 for fifa16).")
    p.add_argument("--end", type=int, default=24, help="End FIFA infix year (inclusive).")
    p.add_argument("--league", type=int, default=13, help="League id on FIFAIndex (e.g., 13=Premier League).")
    p.add_argument("--out", type=str, default=".", help="Output directory for CSV files.")
    p.add_argument("--no-headless", action="store_true", help="Disable headless browser.")
    args = p.parse_args()

    run_full_scrape(
        start_year_infix=args.start,
        end_year_infix=args.end,
        league_id=args.league,
        outdir=args.out,
        headless=not args.no_headless
    )
