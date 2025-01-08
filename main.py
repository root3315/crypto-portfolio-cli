#!/usr/bin/env python3
"""crypto-portfolio-cli — track and manage your crypto portfolio from the terminal."""

import argparse, json, sys
from datetime import datetime
from pathlib import Path

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

COINGECKO_API = "https://api.coingecko.com/api/v3"
PORTFOLIO_FILE = Path.home() / ".crypto_portfolio.json"
console = Console()


def load_portfolio():
    if not PORTFOLIO_FILE.exists():
        return {}
    with open(PORTFOLIO_FILE) as f:
        return json.load(f)


def save_portfolio(data):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fetch_prices(coin_ids):
    if not coin_ids:
        return {}
    resp = requests.get(
        f"{COINGECKO_API}/simple/price",
        params={"ids": ",".join(set(coin_ids)), "vs_currencies": "usd", "include_24hr_change": "true"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def cmd_add(args):
    portfolio = load_portfolio()
    coin, amount, buy_price = args.coin.lower(), float(args.amount), float(args.buy_price)
    if coin in portfolio:
        entry = portfolio[coin]
        total = entry["amount"] + amount
        entry["amount"] = total
        entry["buy_price"] = round((entry["buy_price"] * entry["amount"] + buy_price * amount) / total, 6)
        entry["last_updated"] = datetime.now().isoformat()
    else:
        portfolio[coin] = {"amount": amount, "buy_price": buy_price, "added_at": datetime.now().isoformat(), "last_updated": datetime.now().isoformat()}
    save_portfolio(portfolio)
    console.print(f"[green]Added {amount} {coin.upper()} @ ${buy_price:,.2f}[/green]")


def cmd_remove(args):
    portfolio = load_portfolio()
    coin = args.coin.lower()
    if coin not in portfolio:
        console.print(f"[red]{coin.upper()} not found in portfolio[/red]")
        sys.exit(1)
    del portfolio[coin]
    save_portfolio(portfolio)
    console.print(f"[yellow]Removed {coin.upper()} from portfolio[/yellow]")


def cmd_show(args):
    portfolio = load_portfolio()
    if not portfolio:
        console.print("[dim]Portfolio is empty. Use 'add' to get started.[/dim]")
        return
    prices = fetch_prices(list(portfolio.keys()))
    table = Table(title="Crypto Portfolio")
    table.add_column("Asset", style="cyan", no_wrap=True)
    table.add_column("Holdings", justify="right")
    table.add_column("Avg Buy", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("24h", justify="right")
    table.add_column("Value (USD)", justify="right")
    table.add_column("P&L", justify="right")
    table.add_column("P&L %", justify="right")
    total_value, total_cost = 0.0, 0.0
    for coin, entry in portfolio.items():
        pd = prices.get(coin, {})
        current_price = pd.get("usd", 0)
        change_24h = pd.get("usd_24h_change")
        value = entry["amount"] * current_price
        cost = entry["amount"] * entry["buy_price"]
        pnl, pnl_pct = value - cost, (value / cost - 1) * 100 if cost else 0
        total_value += value
        total_cost += cost
        chg_str = f"{change_24h:+.2f}%" if change_24h is not None else "N/A"
        chg_c = "green" if (change_24h is not None and change_24h >= 0) else "red"
        pnl_c = "green" if pnl >= 0 else "red"
        table.add_row(coin.upper(), f"{entry['amount']:,.6f}".rstrip("0").rstrip("."),
            f"${entry['buy_price']:,.2f}", f"${current_price:,.2f}",
            f"[{chg_c}]{chg_str}[/{chg_c}]", f"${value:,.2f}",
            f"[{pnl_c}]${pnl:+,.2f}[/{pnl_c}]", f"[{pnl_c}]{pnl_pct:+.2f}%[/{pnl_c}]")
    total_pnl, total_pnl_pct = total_value - total_cost, (total_value / total_cost - 1) * 100 if total_cost else 0
    pnl_c = "green" if total_pnl >= 0 else "red"
    console.print(table)
    console.print(Panel(f"Total Value: [bold]${total_value:,.2f}[/bold]  |  Total Cost: ${total_cost:,.2f}  |  P&L: [{pnl_c}]${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)[/{pnl_c}]", title="Portfolio Summary"))


def cmd_list_coins(args):
    resp = requests.get(f"{COINGECKO_API}/coins/markets",
        params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 20, "page": 1}, timeout=15)
    resp.raise_for_status()
    table = Table(title="Top 20 Coins by Market Cap")
    table.add_column("#", justify="right")
    table.add_column("Symbol", style="cyan")
    table.add_column("Name")
    table.add_column("Price (USD)", justify="right")
    table.add_column("24h", justify="right")
    table.add_column("Market Cap", justify="right")
    for c in resp.json():
        chg = c.get("price_change_percentage_24h")
        chg_str = f"{chg:+.2f}%" if chg is not None else "N/A"
        cc = "green" if (chg is not None and chg >= 0) else "red"
        table.add_row(str(c["market_cap_rank"]), c["symbol"].upper(), c["name"],
            f"${c['current_price']:,.2f}", f"[{cc}]{chg_str}[/{cc}]", f"${c['market_cap']:,.0f}")
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Track and manage your cryptocurrency portfolio from the terminal.", prog="crypto-portfolio")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("add", help="Add a coin to your portfolio")
    p.add_argument("coin", help="Coin ID (e.g. bitcoin, ethereum)")
    p.add_argument("amount", type=float, help="Amount held")
    p.add_argument("buy_price", type=float, help="Average buy price in USD")
    p = sub.add_parser("remove", help="Remove a coin")
    p.add_argument("coin", help="Coin ID to remove")
    sub.add_parser("show", help="Display portfolio with live prices and P&L")
    sub.add_parser("list", help="List top 20 coins by market cap")
    args = parser.parse_args()
    {"add": cmd_add, "remove": cmd_remove, "show": cmd_show, "list": cmd_list_coins}[args.command](args)


if __name__ == "__main__":
    main()
