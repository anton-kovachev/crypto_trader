import os
import gradio as gr
import pandas as pd
import plotly.express as px
from crypto_agents import CryptoCurrencyReporter
from output_models import AccountOutput

from .trader_ui_util import Color, css, js

from collections.abc import Callable, Coroutine
from typing import Any
import asyncio

mapper = {
    "trace": Color.WHITE,
    "agent": Color.CYAN,
    "function": Color.GREEN,
    "generation": Color.YELLOW,
    "response": Color.MAGENTA,
    "account": Color.RED,
}

from datetime import datetime


class Trader:
    def __init__(
        self,
        reporter: Callable[[], Coroutine[Any, Any, AccountOutput]],
        account: AccountOutput,
        model_name: str = os.getenv("MODEL_NAME", "gpt-5-mini"),
    ):
        # reporter: async callable that returns AccountOutput when awaited
        self.reporter = reporter
        self.name = account.account_name
        # self.model_name = account.model_name
        self.account = account
        self.model_name = model_name

    async def reload(self):
        self.account = await self.reporter()

    def get_title(self) -> str:
        return f"<div style='text-align: center;font-size:34px;'>{self.name}<span style='color:#ccc;font-size:24px;'> ({self.model_name})</span></div>"

    # def get_strategy(self) -> str:
    #     return self.account.get_strategy()

    def get_portfolio_value_df(self) -> pd.DataFrame:
        df = pd.DataFrame(
            [
                {
                    "Value (USDC)": holding.total_holding_value_in_usdc,
                    "Date": pd.to_datetime(datetime.fromisoformat(holding.timestamp)),
                }
                for holding in self.account.total_holding_values_time_series
            ],
        )
        return df

    def get_portfolio_value_chart(self):
        df = self.get_portfolio_value_df()
        df["Value (USDC)"] = pd.to_numeric(df["Value (USDC)"])
        df = df.sort_values("Date")
        fig = px.line(df, x="Date", y="Value (USDC)")
        margin = dict(l=40, r=20, t=20, b=40)
        fig.update_layout(
            height=300,
            margin=margin,
            xaxis_title="Date",
            yaxis_title="Value (USDC)",
            paper_bgcolor="#bbb",
            plot_bgcolor="#dde",
        )
        fig.update_traces(line=dict(color="yellow", width=4))
        fig.update_xaxes(
            dtick=86_400_000,
            tickformat="%m/%d",
            tickangle=45,
            tickfont=dict(size=8),
        )
        fig.update_yaxes(tickfont=dict(size=8), tickformat=",.0f")
        return fig

    def get_holdings_df(self) -> pd.DataFrame:
        """Convert holdings to DataFrame for display"""
        if not self.account.holdings:
            return pd.DataFrame(columns=["Symbol", "Quantity"])

        df = pd.DataFrame(
            [
                {
                    "Symbol": holding.token_symbol,
                    "Quantity": holding.token_amount,
                    "Value (USDC)": holding.token_amount_in_usdc,
                    "Average Price (USDC)": holding.token_average_acquisition_price_in_usdc,
                    "Current Price (USDC)": holding.token_current_price_in_usdc,
                    "Profit/Loss (USDC)": holding.token_amount_profit_or_loss_in_usdc,
                }
                for holding in self.account.holdings
            ]
        )
        return df

    def get_transactions_df(self) -> pd.DataFrame:
        """Convert transactions to DataFrame for display"""
        if not self.account.transactions:
            return pd.DataFrame(
                columns=[
                    "Timestamp",
                    "Token In Symbol",
                    "Token Out Symbol",
                    "Token In Quantity",
                    "Token Out Quantity",
                    "Rationale",
                ]
            )

        return pd.DataFrame(
            [
                {
                    "Timestamp": datetime.fromisoformat(transaction.timestamp),
                    "Token In Symbol": transaction.token_in_symbol,
                    "Token Out Symbol": transaction.token_out_symbol,
                    "Token In Quantity": transaction.token_in_quantity,
                    "Token Out Quantity": transaction.token_out_quantity,
                    "Rationale": transaction.rationale,
                }
                for transaction in self.account.transactions
            ]
        )

    def get_portfolio_value(self) -> str:
        """Calculate total portfolio value based on current prices"""
        portfolio_value = (
            0.0
            if not len(self.account.total_holding_values_time_series)
            else float(
                min(
                    self.account.total_holding_values_time_series,
                    key=lambda x: datetime.fromisoformat(x.timestamp),
                ).total_holding_value_in_usdc
            )
        )

        pnl = sum(
            [
                float(
                    holding.token_amount_profit_or_loss_in_usdc
                    if holding.token_amount_profit_or_loss_in_usdc
                    else 0.0
                )
                for holding in self.account.holdings
            ]
        )
        color = "green" if pnl >= 0 else "red"
        sign = "+" if pnl >= 0 else "-"
        return f"<div style='text-align: center;background-color:{color};'><span style='font-size:32px'>${portfolio_value:,.0f}</span><span style='font-size:24px'>&nbsp;&nbsp;&nbsp;{sign}${abs(pnl):,.0f}</span></div>"

    def get_logs(self, previous=None) -> str:
        response = ""
        for log in sorted(
            self.account.logs,
            key=lambda x: datetime.fromisoformat(x.timestamp),
            reverse=True,
        ):
            # Support multiple log formats: AccountLog objects, dicts, or tuples/lists
            timestamp = None
            type = "account"
            message = None

            # Pydantic model or object with attributes
            if hasattr(log, "timestamp") and hasattr(log, "message"):
                timestamp = getattr(log, "timestamp")
                message = getattr(log, "message")
            # dict-like
            elif isinstance(log, dict):
                timestamp = log.get("timestamp")
                message = log.get("message")
                type = log.get("type", type)
            # tuple/list
            elif isinstance(log, (list, tuple)):
                if len(log) == 3:
                    timestamp, type, message = log
                elif len(log) == 2:
                    timestamp, message = log

            if timestamp is None or message is None:
                # fallback to string representation
                entry = str(log)
                response += (
                    f"<span style='color:{Color.WHITE.value}'>{entry}</span><br/>"
                )
                continue

            color = mapper.get(type, Color.WHITE).value
            response += f"<span style='color:{color}'>{timestamp} : [{type}] {message}</span><br/>"
        response = f"<div style='height:250px; overflow-y:auto;'>{response}</div>"
        if response != previous:
            return response
        return gr.update()


class TraderView:
    def __init__(self, trader: Trader):
        self.trader = trader
        self.portfolio_value = None
        self.chart = None
        self.holdings_table = None
        self.transactions_table = None

    def make_ui(self):
        with gr.Column():
            gr.HTML(self.trader.get_title())
            with gr.Row():
                self.portfolio_value = gr.HTML(self.trader.get_portfolio_value)
            with gr.Row():
                self.chart = gr.Plot(
                    self.trader.get_portfolio_value_chart,
                    container=True,
                    show_label=True,
                )
            with gr.Row(variant="panel"):
                self.log = gr.HTML(self.trader.get_logs())
            with gr.Row():
                self.holdings_table = gr.Dataframe(
                    value=self.trader.get_holdings_df,
                    label="Holdings",
                    headers=["Symbol", "Quantity"],
                    row_count=5,
                    column_count=2,
                    max_height=300,
                    elem_classes=["dataframe-fix-small"],
                )
            with gr.Row():
                self.transactions_table = gr.Dataframe(
                    value=self.trader.get_transactions_df,
                    label="Recent Transactions",
                    headers=[
                        "Timestamp",
                        "Token In",
                        "Token Out",
                        "Quantity In",
                        "Quantity Out",
                        "Rationale",
                    ],
                    row_count=5,
                    column_count=6,
                    max_height=300,
                    elem_classes=["dataframe-fix"],
                )

        timer = gr.Timer(value=10)
        timer.tick(
            fn=self.refresh,
            inputs=[],
            outputs=[
                self.portfolio_value,
                self.chart,
                self.holdings_table,
                self.transactions_table,
            ],
            show_progress="hidden",
            queue=False,
        )
        log_timer = gr.Timer(value=0.5)
        log_timer.tick(
            fn=self.trader.get_logs,
            inputs=[self.log],
            outputs=[self.log],
            show_progress="hidden",
            queue=False,
        )

    async def refresh(self):
        await self.trader.reload()
        # return self.trader.get_holdings_df()
        return (
            self.trader.get_portfolio_value(),
            self.trader.get_portfolio_value_chart(),
            self.trader.get_holdings_df(),
            self.trader.get_transactions_df(),
        )


# Main UI construction
async def create_ui(
    account_reporters: list[Callable[[], Coroutine[Any, Any, AccountOutput]]],
):
    """Create the main Gradio UI for the trading simulation

    This function is async because it awaits the initial account reporter
    coroutines on the currently running event loop instead of calling
    `run_until_complete`.
    """

    # Await all account reporter coroutines concurrently to fetch initial accounts
    coros = [reporter() for reporter in account_reporters]
    accounts = await asyncio.gather(*coros)

    traders = [
        Trader(account_reporter, account)
        for account_reporter, account in zip(account_reporters, accounts)
    ]
    trader_views = [TraderView(trader) for trader in traders]

    with gr.Blocks(title="Traders", fill_width=True) as ui:
        with gr.Row():
            for trader_view in trader_views:
                trader_view.make_ui()

    # Return both the UI blocks and the trader views so callers can update
    # the underlying data and push component updates dynamically.
    return ui, trader_views
