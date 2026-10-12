# Crypto Trader

Crypto Trader is a Python application for researching digital assets, reporting
on cryptocurrency accounts, and running an AI-assisted trading workflow. It
combines language-model agents with market-data, account, and blockchain tools
served through the Model Context Protocol (MCP). A Gradio interface presents
account holdings, portfolio history, transactions, and activity logs.

The project is an experimental trading and research tool, not financial advice.
Market data may be delayed or incomplete, and model-generated analysis can be
wrong. Trading and token approvals can move or expose real funds. Run it only
with accounts and keys you are prepared to use, and supervise any live trading.

## Capabilities

- **Research:** retrieve cryptocurrency metadata, current listings, and
  historical market data through CoinMarketCap.
- **Account reporting:** create and inspect accounts, review holdings and
  transactions, and generate validated portfolio reports.
- **Portfolio dashboard:** launch a Gradio UI with account summaries, holdings,
  portfolio-value charts, transaction tables, and logs.
- **AI-assisted trading:** query Uniswap for swap routes and quotes, inspect
  allowances, create token approvals, and submit swaps through configured
  blockchain services.
- **Agent memory and traces:** use SQLite-backed agent sessions, local account
  storage, Qdrant-backed research memory, and file-based trace logging.
- **Optional notifications:** send push notifications through Pushover when
  that integration is configured.

## Technology

- Python 3.12 or newer, managed with [uv](https://docs.astral.sh/uv/)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) using an
  OpenAI-compatible API endpoint (configured for OpenRouter by default)
- [MCP](https://modelcontextprotocol.io/) with Python MCP servers for research,
  accounts, trading, blockchain data, and notifications
- Gradio for the web UI; Pandas and Plotly for portfolio tables and charts
- CoinMarketCap API for cryptocurrency data
- Uniswap APIs, Web3.py, and Ethereum account tooling for swap workflows
- SQLite for local account data and agent sessions; Qdrant for vector memory

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) with `uvx`
- Docker, if you want the application to start its local Qdrant container
  automatically (or a separately managed Qdrant server on port `6333`)
- API credentials for whichever integrations you plan to use
- A compatible Ethereum RPC endpoint and correctly configured wallet for
  blockchain or swap features

The application can start without every optional integration configured, but
the associated feature will not work until its service and credentials are
available.

## Setup

1. Clone the repository and enter its directory:

   ```bash
   git clone https://github.com/anton-kovachev/crypto_trader.git
   cd crypto_trader
   ```

2. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in credentials for the features you intend to use.
   `.env` is excluded from Git. Never commit API tokens, wallet addresses that
   you consider private, or private keys.

3. Install the project dependencies:

   ```bash
   uv sync
   ```

4. Start the dashboard:

   ```bash
   uv run python app.py
   ```

   Open the local URL printed by Gradio in your browser.

The dashboard starts local Qdrant with Docker if it cannot connect to a Qdrant
server on `127.0.0.1:6333`. If Docker is unavailable, start Qdrant yourself on
that address before using research features. The application runs the
`mcp-server-qdrant` MCP server via `uvx` when connecting the research agent.

## Running the trading agent

To run the recurring trading workflow without the dashboard:

```bash
uv run python trading_floor.py
```

It creates a trader and researcher, runs their MCP tools, and repeats according
to `RUN_EVERY_N_MINUTES` (10 minutes by default). This workflow can submit
on-chain transactions. Start with a dedicated test account and test network,
review permissions and transaction details, and do not use a wallet holding
funds you cannot afford to lose.

## Configuration

Set values in `.env`. The template documents all supported project settings:

| Variable | Purpose |
| --- | --- |
| `OPENROUTER_API_KEY` | API key for the language model provider |
| `OPENROUTER_BASE_URL` | OpenAI-compatible provider endpoint; defaults to OpenRouter |
| `MODEL_NAME` | Model name displayed/selected by the UI; defaults to `gpt-5-mini` |
| `COINMARKETCAP_API_KEY` | CoinMarketCap API access for price and listing research |
| `CHAIN_RPC_URL` | RPC endpoint for the configured blockchain |
| `CHAIN_ID`, `CHAIN_NAME` | Blockchain network identifier and display name |
| `USD_TOKEN_SYMBOL`, `USD_TOKEN_ADDRESS` | Stablecoin symbol and contract address used by the account |
| `INITIAL_USDC_AMOUNT` | Initial stablecoin amount used for account setup |
| `USER_PRIVATE_KEY`, `USER_ADDRESS` | Wallet credentials and address for account operations |
| `RELAYER_PRIVATE_KEY` | Private key used by relayer-related transaction flows |
| `UNISWAP_API_KEY`, `UNISWAP_ROUTER_ADDRESS` | Uniswap API and router configuration |
| `PUSHOVER_API_URL`, `PUSHOVER_API_TOKEN`, `PUSHOVER_USER_KEY` | Optional Pushover notifications |
| `TRADER_NAME`, `RESEARCHER_NAME` | Agent names for the recurring trading workflow |
| `RUN_EVERY_N_MINUTES` | Delay between trading workflow runs; defaults to `10` |

Protect wallet private keys as production secrets: do not paste them into
issues, logs, or commits. Use a dedicated, minimally funded account and grant
only the permissions needed for your test.

## Project layout

| Path | Description |
| --- | --- |
| `app.py` | Gradio application entry point and report/research orchestration |
| `trading_floor.py` | Recurring autonomous trading workflow |
| `crypto_agents/` | Researcher, reporter, trader, and validation agents |
| `mcp_servers/` | MCP servers and adapters for market data, accounts, and swaps |
| `services/` | CoinMarketCap, blockchain, and Uniswap service clients |
| `ui/` | Gradio dashboard and portfolio presentation |
| `entities/`, `database/`, `models/`, `output_models/` | Account, persistence, and typed data models |
| `instructions/` | Agent prompts, strategies, and task instructions |
| `tracers/`, `app_logging/`, `logs/` | Trace and application logging |
| `resources/` | Static resources such as the Uniswap router ABI |
| `tests/` | Small account inspection/helper scripts |

## Local data and generated files

Runtime account databases, SQLite agent sessions, Qdrant data, logs, virtual
environments, and `.env` are local data and are ignored by Git. Back up any
local account data you need to retain; it is not synchronized to the
repository.

## Development notes

- Dependencies and the lockfile are declared in `pyproject.toml` and
  `uv.lock`.
- Run project commands in the managed environment with `uv run ...`.
- `tests/check_accounts.py` is a local account inspection helper rather than a
  configured automated test suite.
