#!/usr/bin/env python3
"""
Small agent using LangChain + Claude.

Setup:
    pip install -r requirements.txt

Environment variables:
    ANTHROPIC_API_KEY
"""

import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain.agents import create_agent

load_dotenv()
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

model = ChatAnthropic(model="claude-opus-4-7")

_MOCK_WEATHER = {
    "tokyo": "18°C, partly cloudy",
    "paris": "22°C, sunny",
    "london": "14°C, rainy",
    "new york": "20°C, clear",
    "sydney": "25°C, windy",
}


@tool
def add(a: float, b: float) -> str:
    """Add two numbers together and return the sum."""
    return str(a + b)


@tool
def get_weather(city: str) -> str:
    """Get current weather for a city (mock data)."""
    return _MOCK_WEATHER.get(city.lower(), f"72°F, clear skies in {city}")


@tool
def get_uk_political_news() -> str:
    """Fetch the latest UK political news headlines from BBC News. Call this whenever a USD to GBP conversion is requested."""
    url = "https://feeds.bbci.co.uk/news/politics/rss.xml"
    print("[→] Fetching UK political news from BBC RSS feed...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = root.findall("./channel/item")[:5]
    if not items:
        return "No UK political news found."
    headlines = []
    for item in items:
        title = item.findtext("title", "").strip()
        description = item.findtext("description", "").strip()
        pub_date = item.findtext("pubDate", "").strip()
        headlines.append(f"• {title} — {description} ({pub_date})")
    print(f"[✓] Retrieved {len(headlines)} UK political headlines")
    return "Latest UK Political News:\n" + "\n".join(headlines)


@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """Get the live exchange rate between two currencies (e.g. USD to EUR). If converting USD to GBP, also call get_uk_political_news."""
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "apikey": ALPHAVANTAGE_API_KEY,
    }
    response = requests.get(url, params=params)
    data = response.json()
    rate_info = data.get("Realtime Currency Exchange Rate")
    if not rate_info:
        return f"Could not retrieve exchange rate for {from_currency} to {to_currency}."
    rate = float(rate_info["5. Exchange Rate"])
    diff = abs(rate - 1.0)
    flag = f" ⚠️ FLAG: Rate difference of {diff:.4f} exceeds the $5 threshold." if diff > 5 else ""
    return (
        f"1 {rate_info['1. From_Currency Code']} ({rate_info['2. From_Currency Name']}) "
        f"= {rate_info['5. Exchange Rate']} {rate_info['3. To_Currency Code']} ({rate_info['4. To_Currency Name']}) "
        f"as of {rate_info['6. Last Refreshed']} {rate_info['7. Time Zone']}."
        f"{flag}"
    )


agent = create_agent(model, [add, get_weather, get_exchange_rate, get_uk_political_news])


def run_agent(user_message: str) -> str:
    result = agent.invoke({"messages": [HumanMessage(content=user_message)]})
    return result["messages"][-1].content


if __name__ == "__main__":
    answer = run_agent("What is the exchange rate from USD to GBP?")
    print(answer)
