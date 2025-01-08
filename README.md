# crypto-portfolio-cli

A terminal-native crypto portfolio tracker. No web UI, no Electron, no bloat — just a Python script that pulls live prices from CoinGecko and shows you where your money is.

Portfolio data is stored as JSON in `~/.crypto_portfolio.json`. No database, no server, no accounts.

## Quick Start

```bash
pip install -r requirements.txt
python main.py show
```

## Commands

### Add a position

```bash
python main.py add bitcoin 0.5 42000
python main.py add ethereum 4.2 2800
python main.py add solana 150 98.50
```

Adding the same coin again averages your cost basis automatically.

### View portfolio

```bash
python main.py show
```

Displays a table with live prices, 24h change, current value, and P&L per position plus a portfolio summary. Prices come from the CoinGecko API (free, no API key needed).

### Remove a position

```bash
python main.py remove solana
```

### Browse the market

```bash
python main.py list
```

Shows the top 20 coins by market cap with current prices — useful for checking coin IDs before adding them.

## Coin IDs

CoinGecko uses lowercase string IDs, not ticker symbols. Common ones:

| Coin | ID |
|------|-----|
| Bitcoin | `bitcoin` |
| Ethereum | `ethereum` |
| Solana | `solana` |
| Cardano | `cardano` |
| Dogecoin | `dogecoin` |
| Polkadot | `polkadot` |

Run `python main.py list` to see IDs for the top 20 coins.

## Data Storage

All portfolio data lives in `~/.crypto_portfolio.json`. It's just a JSON file — you can inspect it, back it up, or edit it directly if needed.

```json
{
  "bitcoin": {
    "amount": 0.5,
    "buy_price": 42000.0,
    "added_at": "2025-01-15T10:30:00.000000",
    "last_updated": "2025-01-20T14:22:00.000000"
  }
}
```

## Rate Limits

CoinGecko's free API has rate limits (~10-30 calls/min). Don't run `show` in a tight loop. For normal use it's fine.

## Dependencies

- **requests** — HTTP calls to CoinGecko
- **rich** — terminal tables and colored output

That's it. Two packages.
