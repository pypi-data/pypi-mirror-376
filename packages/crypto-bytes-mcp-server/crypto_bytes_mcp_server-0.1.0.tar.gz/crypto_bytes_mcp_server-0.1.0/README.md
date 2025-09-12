# Crypto Bytes MCP Server

Crypto Bytes is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides real-time cryptocurrency news.  
It fetches articles from leading crypto news aggregators and makes them available to any MCP-compatible client.

---

## Features

- Fetch the latest breaking news in the crypto ecosystem  
- Filter by time period:
  - `breaking` – most recent articles  
  - `24hrs` – last 24 hours  
  - `1week` – last 7 days  
  - `all_time` – latest articles with no time filter  
- Target by cryptocurrency symbol (e.g., `BTC`, `ETH`) or get general blockchain updates  
- Quick summary tool `whats_happening` for fast daily updates  

---

## Installation

Install from [PyPI](https://pypi.org/project/crypto-bytes-server/):

```bash
pip install crypto-bytes-server

Tools:
fetch_crypto_news

Fetch up to 10 news articles for a given cryptocurrency and time period.

Arguments:

cryptocurrency (optional) – symbol like BTC, ETH, SOL

time_period (optional) – breaking | 24hrs | 1week | all_time (default: 24hrs)

whats_happening

Shortcut for “What’s happening in crypto right now?”
Fetches a summary of breaking crypto news from the last 24 hours.


License

MIT License © 2025 Micky Multani
