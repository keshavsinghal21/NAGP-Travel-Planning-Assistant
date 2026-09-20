from mcp.server.fastmcp import FastMCP
import requests

mcp = FastMCP(
    "Currency Service",
    instructions=(
        "This MCP server provides currency conversion information. "
        "Use the convert_currency tool to convert an amount from "
        "one currency to another using the available exchange rate."
    ),
)

@mcp.tool()
def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> str:
    """
    Convert an amount from one currency to another
    using the current exchange rate.
    """

    try:
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        url = f"https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        rates = data.get("rates", {})

        if to_currency not in rates:
            return (
                f"Could not find an exchange rate from "
                f"{from_currency} to {to_currency}."
            )

        rate = rates[to_currency]
        converted_amount = amount * rate

        result = {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": rate,
            "converted_amount": round(converted_amount, 2),
            "rate_date": data.get("date"),
        }

        return str(result)

    except requests.RequestException as e:
        return f"Currency service failed: {e}"

    except Exception as e:
        return f"Unable to convert currency: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")