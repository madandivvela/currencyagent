#!/usr/bin/env python3
import os
import requests
import xml.etree.ElementTree as ET
import streamlit as st
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

load_dotenv()
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
_llm = ChatAnthropic(model="claude-opus-4-7")

COMMON_CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "INR", "AUD", "CAD", "CHF",
    "CNY", "HKD", "SGD", "MXN", "BRL", "ZAR", "AED", "NZD",
]


def analyze_sentiment(headlines: list[str]) -> dict:
    joined = "\n".join(f"- {h}" for h in headlines)
    prompt = (
        "You are a financial analyst. Based on the following UK political news headlines, "
        "determine if the overall sentiment is POSITIVE or NEGATIVE for the British Pound (GBP).\n\n"
        f"{joined}\n\n"
        "Reply in this exact format:\n"
        "SENTIMENT: <POSITIVE or NEGATIVE>\n"
        "REASON: <one sentence explanation>\n"
        "RECOMMENDATION: <BUY GBP or HOLD — DO NOT BUY>"
    )
    print("[→] Analyzing news sentiment with Claude...")
    response = _llm.invoke([HumanMessage(content=prompt)])
    text = response.content.strip()
    print(f"[✓] Sentiment analysis:\n{text}")
    result = {"sentiment": "UNKNOWN", "reason": "", "recommendation": "HOLD — DO NOT BUY"}
    for line in text.splitlines():
        if line.startswith("SENTIMENT:"):
            result["sentiment"] = line.split(":", 1)[1].strip()
        elif line.startswith("REASON:"):
            result["reason"] = line.split(":", 1)[1].strip()
        elif line.startswith("RECOMMENDATION:"):
            result["recommendation"] = line.split(":", 1)[1].strip()
    return result


def fetch_uk_political_news() -> list[dict]:
    url = "https://feeds.bbci.co.uk/news/politics/rss.xml"
    print("[→] Fetching UK political news from BBC RSS feed...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = root.findall("./channel/item")[:5]
    news = []
    for item in items:
        news.append({
            "title": item.findtext("title", "").strip(),
            "description": item.findtext("description", "").strip(),
            "link": item.findtext("link", "").strip(),
            "pubDate": item.findtext("pubDate", "").strip(),
        })
    print(f"[✓] Retrieved {len(news)} UK political headlines")
    return news


def fetch_exchange_rate(from_currency: str, to_currency: str) -> dict:
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "apikey": ALPHAVANTAGE_API_KEY,
    }
    print(f"[→] Fetching exchange rate: {from_currency.upper()} → {to_currency.upper()}")
    print(f"[→] Calling Alpha Vantage API: {url}")
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    print(f"[✓] Response received (status {response.status_code})")
    return response.json()


st.set_page_config(page_title="Currency Exchange", page_icon="💱", layout="centered")
st.title("💱 Live Currency Exchange Rate")
st.caption("Powered by Alpha Vantage")

col1, col2 = st.columns(2)

with col1:
    from_currency = st.selectbox("From", COMMON_CURRENCIES, index=0)

with col2:
    to_currency = st.selectbox("To", COMMON_CURRENCIES, index=1)

amount = st.number_input("Amount", min_value=0.01, value=1.0, step=1.0)

if st.button("Get Exchange Rate", type="primary", use_container_width=True):
    if from_currency == to_currency:
        st.warning("Please select two different currencies.")
    else:
        with st.spinner("Fetching live rate..."):
            try:
                data = fetch_exchange_rate(from_currency, to_currency)
                rate_info = data.get("Realtime Currency Exchange Rate")

                if not rate_info:
                    print("[✗] No rate data returned — possible rate limit hit")
                    st.error("Could not retrieve exchange rate. You may have hit the free-tier rate limit (5 req/min). Try again shortly.")
                else:
                    rate = float(rate_info["5. Exchange Rate"])
                    converted = amount * rate

                    diff = abs(converted - amount)

                    print(f"[✓] Exchange rate: 1 {rate_info['1. From_Currency Code']} = {rate} {rate_info['3. To_Currency Code']}")
                    print(f"[✓] Conversion: {amount} {rate_info['1. From_Currency Code']} = {converted:.4f} {rate_info['3. To_Currency Code']}")
                    print(f"[i] Difference: {diff:.4f}")
                    if diff > 5:
                        print(f"[!] FLAG: Difference of {diff:.4f} exceeds $5 threshold")
                    print(f"[i] Last refreshed: {rate_info['6. Last Refreshed']} {rate_info['7. Time Zone']}")

                    st.success("Live rate fetched successfully!")

                    if diff > 5:
                        st.warning(f"⚠️ Large difference detected: the converted amount differs by **{diff:.4f}** from the original amount, which exceeds the $5 threshold.")

                    m1, m2 = st.columns(2)
                    m1.metric("Exchange Rate", f"{rate:.4f}", f"1 {from_currency} → {to_currency}")
                    m2.metric("Converted Amount", f"{converted:,.4f} {to_currency}", f"{amount} {from_currency}")

                    st.divider()
                    st.caption(
                        f"Last refreshed: {rate_info['6. Last Refreshed']} {rate_info['7. Time Zone']}  |  "
                        f"Bid: {rate_info['8. Bid Price']}  |  Ask: {rate_info['9. Ask Price']}"
                    )

                    if from_currency == "USD" and to_currency == "GBP":
                        st.divider()
                        st.subheader("🇬🇧 UK Political News")
                        st.caption("Latest headlines from BBC Politics")
                        try:
                            news = fetch_uk_political_news()
                            for article in news:
                                with st.container(border=True):
                                    st.markdown(f"**[{article['title']}]({article['link']})**")
                                    st.caption(article["description"])
                                    st.caption(f"🕐 {article['pubDate']}")

                            with st.spinner("Analyzing sentiment..."):
                                headlines = [a["title"] for a in news]
                                analysis = analyze_sentiment(headlines)

                            st.divider()
                            st.subheader("📊 Buy Recommendation")
                            if analysis["sentiment"] == "POSITIVE":
                                st.success(f"✅ **{analysis['recommendation']}**")
                            else:
                                st.error(f"🚫 **{analysis['recommendation']}**")
                            st.caption(f"Sentiment: **{analysis['sentiment']}** — {analysis['reason']}")

                        except requests.exceptions.RequestException as e:
                            st.warning(f"Could not load UK political news: {e}")

            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")
