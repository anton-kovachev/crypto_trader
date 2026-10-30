# Crypto Trader

Crypto Trader is a Python application for researching digital assets, reporting
on cryptocurrency accounts, and running an AI-assisted trading workflow. It
combines language-model agents with market-data, account, and blockchain tools
served through the Model Context Protocol (MCP). An AWS Lambda handler runs
the trading or reporting workflow. The separate Gradio frontend reads reporter
snapshots from Redis and presents account holdings, portfolio history,
transactions, and activity logs.

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
- **Backend/frontend boundary:** the Lambda reporter writes each
  `ReporterOutput` as JSON in the Redis `accounts` hash, keyed by account name.
  The Gradio app reads reports from this hash and does not invoke the backend.
- **AI-assisted trading:** query Uniswap for swap routes and quotes, inspect
  allowances, create token approvals, and submit swaps through configured
  blockchain services.
- **Agent memory and traces:** use SQLite-backed agent sessions, local account
  storage, Qdrant-backed research memory, and file-based trace logging.
- **Optional notifications:** send push notifications through Pushover when
  that integration is configured.

## Technology

- Python 3.12 or newer, managed with [uv](https://docs.astral.sh/uv/)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) using
  AWS Bedrock Mantle with tokens provided by `aws-bedrock-token-generator`
- [MCP](https://modelcontextprotocol.io/) with Python MCP servers for research,
  accounts, trading, blockchain data, and notifications
- Gradio for the web UI; Pandas and Plotly for portfolio tables and charts
- Redis for sharing reporter output between the Lambda backend and Gradio app
- Boto3 and S3 for deployed account-database snapshots
- CoinMarketCap API for cryptocurrency data
- Uniswap APIs, Web3.py, and Ethereum account tooling for swap workflows
- SQLite for local account data and agent sessions; S3 snapshots for the Lambda
  account database; Qdrant for vector memory

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) with `uvx`
- A Redis instance reachable by both applications
- A Qdrant server reachable by the backend; local development can start one
  with Docker
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

4. Start Redis and Qdrant locally. Set `REDIS_URL` and `QDRANT_URL` in `.env`.

5. Generate a report locally to populate Redis:

   ```bash
   uv run python local_runner.py reporting
   ```

6. Start the dashboard:

   ```bash
   uv run python local_runner.py ui
   ```

   Open the local URL printed by Gradio in your browser.

The dashboard only reads from Redis. It does not start agents, call the
backend, or start Qdrant. The local trading-floor runner can start Qdrant with
Docker if it cannot connect to `127.0.0.1:6333`.

## Running workflows locally

Use the local helper to run one trading cycle, generate and persist a report,
or launch the dashboard:

```bash
uv run python local_runner.py trading
uv run python local_runner.py reporting
uv run python local_runner.py ui
```

The trading command runs one cycle and may submit on-chain transactions. Use a
dedicated test account and network. For recurring trades, use
`uv run python trading_floor.py`.

## Running the Lambda backend

Configure the Lambda handler as `lambda_function.lambda_handler`. Invoke it
with a JSON object selecting one workflow:

```json
{"workflow": "reporter"}
```

or:

```json
{"workflow": "trading_floor"}
```

The `reporter` workflow generates validated account reports and replaces each
matching account field in the Redis hash `accounts` with the JSON-stringified
`ReporterOutput`. The `trading_floor` workflow performs one trading cycle;
invoke it on a schedule if recurring trades are desired. Invalid workflow
names fail the invocation.

Set `ACCOUNT_DB_S3_BUCKET` and optionally `ACCOUNT_DB_S3_KEY` in the Lambda
environment. Each invocation loads the SQLite database from that S3 object to
`/tmp`, uses the existing SQLite account code, then uploads the database back
to S3. The Lambda execution role needs `s3:GetObject` and `s3:PutObject` for
that object. Set the function's reserved concurrency to `1` so simultaneous
invocations cannot overwrite each other's database snapshots.

Set `REDIS_MODE=elasticache`, `ELASTICACHE_HOST`, `ELASTICACHE_USERNAME`, and
`ELASTICACHE_RESOURCE_ID` for ElastiCache IAM authentication. Lambda's
execution role must have `elasticache:Connect`, and the function must have
network access to the cache. Redis commands use `redis-py`; Boto3/botocore
credentials from the Lambda role sign short-lived IAM auth tokens. Set
`ELASTICACHE_CLUSTER_MODE=true` for a cluster-mode or Serverless endpoint.

Also set a network-accessible `QDRANT_URL`. The Qdrant MCP server is launched
through `uvx`, so the deployment image or layer must include `uvx` and allow it
to run `mcp-server-qdrant`. Agent session databases use
`/tmp/crypto-trader/sessions` by default and are temporary.

## Running the trading agent

To run the recurring trading workflow without the dashboard:

```bash
uv run python trading_floor.py
```

It runs the same one-cycle trading workflow as the Lambda backend and repeats
according to `RUN_EVERY_N_MINUTES` (10 minutes by default). This workflow can submit
on-chain transactions. Start with a dedicated test account and test network,
review permissions and transaction details, and do not use a wallet holding
funds you cannot afford to lose.

## Configuration

Set values in `.env`. The template documents all supported project settings:

| Variable | Purpose |
| --- | --- |
| `MODEL_NAME` | Model used by all agents and shown in the UI; defaults to `openai.gpt-oss-120b` when unset or blank |
| `PROJECT_ID` | AWS Bedrock Mantle project ID |
| `AWS_BEDROCK_BASE_URL` | AWS Bedrock Mantle OpenAI-compatible API endpoint |
| `COINMARKETCAP_API_KEY` | CoinMarketCap API access for price and listing research |
| `REDIS_MODE`, `REDIS_URL` | Select local URL or ElastiCache IAM authentication |
| `ELASTICACHE_HOST`, `ELASTICACHE_PORT` | ElastiCache endpoint; port defaults to `6379` |
| `ELASTICACHE_USERNAME`, `ELASTICACHE_RESOURCE_ID` | IAM-enabled ElastiCache user and signed cache identifier |
| `ELASTICACHE_CLUSTER_MODE` | Set `true` for cluster-mode or Serverless caches |
| `QDRANT_URL`, `QDRANT_API_KEY` | Qdrant endpoint and optional API key for research memory |
| `ACCOUNT_DB_S3_BUCKET`, `ACCOUNT_DB_S3_KEY` | S3 bucket and object key for the Lambda SQLite account database |
| `CHAIN_RPC_URL` | RPC endpoint for the configured blockchain |
| `CHAIN_ID`, `CHAIN_NAME` | Blockchain network identifier and display name |
| `USD_TOKEN_SYMBOL`, `USD_TOKEN_ADDRESS` | Stablecoin symbol and contract address used by the account |
| `INITIAL_USDC_AMOUNT` | Initial stablecoin amount used for account setup |
| `USER_PRIVATE_KEY`, `USER_ADDRESS` | Wallet credentials and address for account operations |
| `RELAYER_PRIVATE_KEY` | Private key used by relayer-related transaction flows |
| `UNISWAP_API_KEY`, `UNISWAP_ROUTER_ADDRESS` | Uniswap API and router configuration |
| `PUSHOVER_API_URL`, `PUSHOVER_API_TOKEN`, `PUSHOVER_USER_KEY` | Optional Pushover notifications |
| `TRADER_NAME`, `RESEARCHER_NAME` | Agent names for the recurring trading workflow |
| `REPORTER_NAME` | Agent name for reporter workflow runs |
| `RUN_EVERY_N_MINUTES` | Delay between trading workflow runs; defaults to `10` |

Protect wallet private keys as production secrets: do not paste them into
issues, logs, or commits. Use a dedicated, minimally funded account and grant
only the permissions needed for your test.

## Project layout

| Path | Description |
| --- | --- |
| `app.py` | Redis-backed Gradio frontend entry point |
| `local_runner.py` | Local commands for trading, reporting, and the dashboard |
| `lambda_function.py` | Lambda handler dispatching reporter and trading workflows |
| `trading_floor.py` | Local recurring runner for the shared trading workflow |
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
repository. In Lambda, the account database is loaded from and saved to S3;
`/tmp` is used only as its temporary working copy and for disposable agent
session files.

## Development notes

- Dependencies and the lockfile are declared in `pyproject.toml` and
  `uv.lock`.
- Run project commands in the managed environment with `uv run ...`.
- `tests/check_accounts.py` is a local account inspection helper rather than a
  configured automated test suite.
