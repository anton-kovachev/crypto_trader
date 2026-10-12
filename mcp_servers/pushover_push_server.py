import requests
import os
import asyncio
from mcp.server import FastMCP
from dotenv import load_dotenv

load_dotenv(override=True)

mcp = FastMCP("pushover_push_server")


@mcp.tool()
def push_message(message: str) -> str:
    """
    Record a contact request or email for follow-up by pushing it via Pushover notification API.
    Use this when a user wants to be contacted or leaves their email address.

    Args:
        message (str): The contact information (email, message, or request) to record.
    Returns:
        str: A confirmation message indicating that the contact request has been pushed successfully.
    """
    # Here you can implement the logic to push a message using push notification API
    requests.post(
        os.getenv("PUSHOVER_API_URL", "https://api.pushover.net/1/messages.json"),
        data={
            "message": message,
            "token": os.getenv("PUSHOVER_API_TOKEN"),
            "user": os.getenv("PUSHOVER_USER_KEY"),
        },
    )

    return f"Message pushed successfully: {message}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
