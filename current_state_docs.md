# Polymarket Trading Bot: Project Documentation

This document describes the current state, architecture, and recent improvements of the Polymarket Trading Bot project as of March 18, 2026.

## 1. Project Overview
The project is a specialized trading bot for Polymarket, focusing on short-term high-probability outcomes. It consists of a backend trading engine (`bot.py`) and a control dashboard API (`server.py`).

## 2. Architecture

### Backend Core (`bot.py`)
- **API Interaction**: 
    - **Gamma API**: Used for market discovery and fetching events.
    - **CLOB API**: Used for fetching orderbooks, midpoints, last trade prices, and place/cancel orders via the `py-clob-client` SDK.
    - **Data API**: Used for real-time position tracking and historical PnL analysis.
- **Trading Logic**:
    - Scans for markets closing within 24 hours.
    - Filters for outcomes with prices >= 0.85 (85% probability).
    - Places BUY orders for 1.0 USDC (configurable).
- **Take-Profit System (Enhanced)**:
    - Automatically monitors active positions.
    - **Triggers**:
        1. **ROI Target**: 5% above entry price.
        2. **Huge Profit**: > 100% gain (e.g., entry at 0.38, current at 0.99).
        3. **Max Cap**: Current Price >= 0.98 (near-certain outcome, locking in profits before resolution).
    - **Execution Strategy**:
        - Fetches `best bid` from the orderbook for accurate valuation.
        - Falls back to `midpoint` or `last trade price` if orderbook is thin.
        - Ensures `token allowance` for the Polymarket exchange using `update_balance_allowance`.
        - Places `SELL` orders with a 0.5% discount to the best price to ensure immediate fill.
- **Robustness**: 
    - Full error handling with tracebacks.
    - Automated re-polling every 15 seconds.
    - Proxy support for all outgoing API requests.

### Dashboard API (`server.py`)
- **Technology**: FastAPI with Uvicorn.
- **Endpoints**:
    - `GET /api/status`: Returns current bot status, balance, trades, and active positions.
    - `POST /api/start`: Spawns the trading loop in a background daemon thread.
    - `POST /api/stop`: Stops the trading loop.

## 3. Current State of Positions
As of the last check:
- **Shanghai Temperature Market**: 
    - **Question**: "Will the highest temperature in Shanghai be 13°C on March 18?"
    - **Entry Price**: ~$0.38
    - **Current Price**: ~$0.9995
    - **ROI**: ~163%
    - **Status**: Identified for Take-Profit. The bot has been updated to handle the `allowance` requirement and the correct `py-clob-client` method calls.

## 4. Operational Instructions

### Setup
- Ensure the Python virtual environment is active: `.\venv\Scripts\activate` on Windows.
- The `.env` file must contain: `PRIVATE_KEY`, `API_KEY`, `API_SECRET`, `API_PASSPHRASE`, `PROXY_URL`.

### Starting the System
1. **Start the Server**:
   ```bash
   python backend/server.py
   ```
2. **Start the Bot**:
   Hit the start endpoint:
   ```bash
   curl -X POST http://localhost:8000/api/start
   ```

### Logs
- `server_stdout.log`: Real-time trading activity, balance updates, and take-profit notifications.
- `server_stderr.log`: Startup errors and system-level exceptions.

## 5. Recent Fixes
- **Allowance Issue**: Fixed a `not enough balance / allowance` error by implementing proactive token allowance updates via the SDK.
- **Price Fetching**: Upgraded price detection to use full orderbook data with fallbacks, ensuring the bot can "see" current liquidity.
- **SDK Compatibility**: Resolved several `py-clob-client` method name mismatches (e.g., `get_order_book` vs `get_orderbook`).

## 6. Known Considerations
- The bot relies on a proxy (`PROXY_URL`) to bypass potential rate limits or regional restrictions for Polymarket APIs.
- Negative Risk markets require careful share handling; the current bot is calibrated to handle YES/NO outcomes in these markets.
