# AWS deployment

This stack deploys two ZIP-based Lambda functions in the `eu-north-1` default
VPC:

- `crypto-trader-backend` consumes separate trading and reporting SQS queues,
  loads/saves `accounts.db` in S3, and publishes reporter output to ElastiCache.
- `crypto-trader-ui` runs Gradio through AWS Lambda Web Adapter and reads reports
  from ElastiCache.

EventBridge Scheduler sends `{"workflow":"trading_floor"}` and
`{"workflow":"reporter"}` to their respective SQS queues. The schedules default
to every 30 minutes for trading and hourly at minute 5 for reporting; override
the cron expressions in `terraform.tfvars`.

## Prerequisites

- Terraform 1.6+, AWS CLI credentials for `eu-north-1`, and `uv`.
- A default VPC with at least two subnets and an attached Internet Gateway.
- An unused private-subnet CIDR inside the default VPC. The example uses
  `172.31.240.0/24`, split into two /25 subnets.
- A network-accessible Qdrant endpoint; Lambda cannot use localhost.
- An AWS Secrets Manager secret containing a JSON object with the backend
  credentials listed below.

The backend secret must include string values for:

```json
{
  "OPENROUTER_API_KEY": "...",
  "COINMARKETCAP_API_KEY": "...",
  "CHAIN_RPC_URL": "...",
  "USER_PRIVATE_KEY": "...",
  "RELAYER_PRIVATE_KEY": "...",
  "UNISWAP_API_KEY": "..."
}
```

Optional keys are `QDRANT_API_KEY`, `PUSHOVER_API_TOKEN`,
`PUSHOVER_USER_KEY`, and `OPENAI_API_KEY`. Terraform receives only the secret
ARN, not its contents. The backend Lambda role gets `secretsmanager:GetSecretValue`
for that ARN.

## Build and deploy

1. Copy the example variables file and replace the placeholders:

   ```bash
   cp terraform/terraform.tfvars.example terraform/terraform.tfvars
   ```

2. Package both functions and deploy the infrastructure:

   ```bash
   uv run python scripts/package_lambda_zips.py
   uv run python scripts/deploy.py
   ```

The packaging script exports the locked dependencies into temporary build
directories and writes `dist/backend.zip` and `dist/ui.zip`. The backend ZIP
includes the `uv` executable used to launch the Qdrant MCP server; it installs
`mcp-server-qdrant` into `/tmp` on first use, so backend networking must allow
access to PyPI, Qdrant, OpenRouter, and CoinMarketCap.
The UI ZIP omits `boto3` and `botocore`; the Python 3.12 Lambda runtime supplies
them for ElastiCache IAM token signing. It also removes type stubs and source
maps to stay within Lambda's combined code-and-layer size limit.

The Lambda execution role uses the AWS credential provider chain to sign
ElastiCache IAM tokens; it does not receive Bedrock permissions. S3 access is
limited to the account database object. Redis uses separate IAM users: backend
can read/write the `accounts` hash, while the UI user is read-only. The built-in
Redis `default` user is replaced with a disabled user so it cannot bypass IAM
authentication.

The UI Function URL is intentionally public (`AuthType=NONE`), as requested.
Anyone with the URL can view reporter data. ElastiCache itself remains private
inside the VPC.

The private Lambda subnets use one NAT Gateway for outbound access to external
services. NAT Gateway and ElastiCache incur ongoing AWS charges.

For an existing local database, seed the S3 object once after deployment:

```bash
aws s3 cp database/accounts.db s3://ACCOUNT_DATABASE_BUCKET/accounts/accounts.db
```

The two EventBridge schedules are enabled after `terraform apply`. The trading
schedule may execute on-chain transactions, so use a dedicated, minimally
funded wallet and review the cron expression before deployment.

## Destroy

```bash
uv run python scripts/destroy.py
```

Destroying the stack permanently deletes the ElastiCache data and the S3
account database. Back up `accounts.db` first if you need to keep account data.
