# Currency Exchange Agent

A LangChain + Claude-powered agent that provides live currency exchange rates, UK political news, and AI-driven buy recommendations — with a Streamlit web UI.

---

## Features

- **Live Exchange Rates** — real-time currency conversion via Alpha Vantage API
- **Large Difference Alert** — flags conversions where the difference exceeds $5
- **UK Political News** — automatically fetches the latest BBC Politics headlines when converting USD → GBP
- **AI Buy Recommendation** — Claude analyzes UK political sentiment and recommends whether to buy GBP
- **Streamlit UI** — clean web interface for interactive currency lookups
- **CLI Agent** — conversational agent you can query in natural language

---

## Project Structure

```
.
├── agent.py          # LangChain agent with tools (CLI)
├── ui.py             # Streamlit web UI
├── requirements.txt  # Python dependencies
├── .env              # Your API keys (not committed)
└── .env.example      # Template for .env
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/madandivvela/currencyagent.git
cd currencyagent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```env
ANTHROPIC_API_KEY=your-anthropic-api-key
ALPHAVANTAGE_API_KEY=your-alphavantage-api-key
```

- **Anthropic API key** — get one at [console.anthropic.com](https://console.anthropic.com)
- **Alpha Vantage API key** — free key at [alphavantage.co](https://www.alphavantage.co/support/#api-key)

---

## Usage

### Streamlit UI

```bash
python3 -m streamlit run ui.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### CLI Agent

```bash
python3 agent.py
```

Or call the agent programmatically:

```python
from agent import run_agent

print(run_agent("What is the exchange rate from USD to GBP?"))
print(run_agent("What is 42 + 17?"))
print(run_agent("What is the weather in Tokyo?"))
```

---

## Agent Tools

| Tool | Description |
|------|-------------|
| `add` | Adds two numbers |
| `get_weather` | Returns weather for a city (mock data) |
| `get_exchange_rate` | Live currency exchange rate via Alpha Vantage |
| `get_uk_political_news` | Latest UK political headlines from BBC News RSS |

---

## USD → GBP Flow

When you query USD to GBP, the agent automatically:

1. Fetches the live exchange rate
2. Pulls the 5 latest UK political headlines from BBC News
3. Sends the headlines to Claude for sentiment analysis
4. Displays a **Buy GBP** or **Hold — Do Not Buy** recommendation based on the political climate

---

## Notes

- Alpha Vantage free tier allows **5 requests per minute**
- The `get_weather` tool uses mock data; replace with a live weather API for production use
- Never commit your `.env` file — it is excluded via `.gitignore`
