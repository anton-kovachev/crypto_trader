from pydantic import BaseModel, Field


class AccountHoldingOutput(BaseModel):
    token_symbol: str = Field(
        ..., description="Symbol of the token held in the account"
    )
    token_amount: str = Field(
        ..., description="Amount of the token held in the account"
    )
    token_amount_in_usdc: float = Field(
        ..., description="Amount of the token held in the account, converted to USDC"
    )
    token_average_acquisition_price_in_usdc: float = Field(
        ...,
        description="Average acquisition price of the token held in the account in USDC",
    )
    token_current_price_in_usdc: float = Field(
        ..., description="Current price of the token in USDC"
    )
    token_amount_in_btc: float = Field(
        ..., description="Amount of the token held in the account, converted to BTC"
    )
    token_average_acquisition_price_in_btc: float = Field(
        ...,
        description="Average acquisition price of the token held in the account in BTC",
    )
    token_amount_profit_or_loss_in_usdc: float = Field(
        ...,
        description="Profit or loss of the token amount held in the account in USDC based on the average acquisition price",
    )
    token_amount_profit_or_loss_in_btc: float = Field(
        ...,
        description="Profit or loss of the token amount held in the account in BTC based on the average acquisition price",
    )


class AccountHoldingSnapshot(BaseModel):
    total_holding_value_in_usdc: float = Field(
        ..., description="Total holding value (all tokens) of the account in USDC"
    )
    total_holding_value_in_btc: float = Field(
        ..., description="Total holding value (all tokens) of the account in BTC"
    )
    timestamp: str = Field(
        ...,
        description="Timestamp of the account holding snapshot formatted in ISO 8601",
    )


class AccountTransaction(BaseModel):
    timestamp: str = Field(
        ..., description="Timestamp of the transaction formatted in ISO 8601"
    )
    token_in_symbol: str = Field(
        ...,
        description="Symbol of the token being sent in the transaction (e.g., sold)",
    )
    token_out_symbol: str = Field(
        ...,
        description="Symbol of the token being received in the transaction (e.g., bought)",
    )
    token_in_quantity: str = Field(
        ...,
        description="Quantity of the token being sent in the transaction (e.g., sold)",
    )
    token_out_quantity: str = Field(
        ...,
        description="Quantity of the token being received in the transaction (e.g., bought)",
    )
    timestamp: str = Field(
        ..., description="Timestamp of the transaction formatted in ISO 8601"
    )
    rationale: str = Field(..., description="Rationale for the transaction")


class AccountLog(BaseModel):
    message: str = Field(..., description="Message of the account log")
    timestamp: str = Field(
        ..., description="Timestamp of the account log formatted in ISO 8601"
    )


class AccountOutput(BaseModel):
    account_name: str = Field(..., description="Name of the account holding the assets")
    holdings: list[AccountHoldingOutput] = Field(
        ..., description="List of token holdings in the account"
    )
    total_holding_values_time_series: list[AccountHoldingSnapshot] = Field(
        ...,
        description="List of account holding snapshots for the account ordered by timestamp in descending order",
    )
    logs: list[AccountLog] = Field(
        ...,
        description="List of the last twenty account operational logs for the account ordered by timestamp in descending order retrieved from the account's activity (not the agent's actions)",
    )
    transactions: list[AccountTransaction] = Field(
        ...,
        description="List of the last five account transactions for the account ordered by timestamp in descending order retrieved from the account's activity (not the agent's actions)",
    )


class ReporterOutput(BaseModel):
    account: AccountOutput = Field(
        ..., description="Account for which the report is generated"
    )
    error_message: str | None = Field(
        None,
        description="Optional error message if any error occurred during the report generation",
    )
