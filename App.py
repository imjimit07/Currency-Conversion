from flask import Flask, render_template_string, jsonify, request
import requests
from datetime import datetime
import os

app = Flask(__name__)

# --- API Configuration ---
# IMPORTANT: Replace with your actual API keys
EXCHANGERATE_API_KEY = "3d80829106921d41c9623da0"  # Get from https://www.exchangerate-api.com/
GNEWS_API_KEY = "dbce34b2f59cf435c4852495eee2369e"      # Get from https://gnews.io/
FINNHUB_API_KEY = "d42q0s1r01qorlesihpg"        # Get from https://finnhub.io/

# --- HTML & Frontend ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Markets Dashboard</title>
    <style>
        :root {
            --primary-color: #031F3D;
            --secondary-color: #03045e;
            --background-color: #ade8f4;
            --card-background: #caf0f8;
            --text-color: #263238;
            --header-text-color: #ffffff;
            --gradient-start: #0077b6;
            --gradient-end: #FAFAFA;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--background-color);
            color: var(--text-color);
            padding: 20px;
        }

        .container {
            max-width: 1300px;
            margin: 0 auto;
        }

        .header {
            background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
            color: var(--header-text-color);
            padding: 30px 20px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }

        .header h1 {
            font-size: 2.8em;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .last-updated {
            text-align: center;
            color: var(--secondary-color);
            margin-bottom: 25px;
            font-size: 0.95em;
        }

        .main-grid, .secondary-grid {
            display: grid;
            gap: 25px;
            margin-bottom: 25px;
        }

        .main-grid {
            grid-template-columns: 1fr 1.5fr;
        }
        
        .secondary-grid {
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }

        .card {
            background: var(--card-background);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
        }

        .card h2 {
            color: var(--primary-color);
            margin-bottom: 20px;
            font-size: 1.6em;
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 10px;
        }

        .converter-form { display: flex; flex-direction: column; gap: 18px; }
        .input-group { display: flex; flex-direction: column; gap: 8px; }
        .input-group label { font-weight: 600; color: #555; }
        .input-group input, .input-group select {
            width: 100%; padding: 12px; border: 1px solid #ccc;
            border-radius: 8px; font-size: 1em;
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        .input-group input:focus, .input-group select:focus {
            outline: none; border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(0, 121, 107, 0.2);
        }

        .convert-btn {
            background: var(--primary-color); color: white; border: none;
            padding: 14px; border-radius: 8px; font-size: 1.1em;
            font-weight: 600; cursor: pointer;
            transition: background-color 0.3s, transform 0.2s; margin-top: 10px;
        }
        .convert-btn:hover { background: var(--secondary-color); transform: translateY(-2px); }

        .result {
            background: var(--background-color); padding: 20px; border-radius: 8px;
            margin-top: 18px; text-align: center; font-size: 1.4em;
            font-weight: 700; color: var(--primary-color); display: none;
        }

        .rates-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px; overflow-y: auto; max-height: 450px;
        }

        .rate-card, .info-card {
            background: #f7f9f9; padding: 15px; border-radius: 8px;
            border-left: 5px solid var(--primary-color);
        }
        .info-card { display: flex; justify-content: space-between; align-items: center; }

        .rate-card .currency, .info-card .name { font-weight: 700; color: #333; font-size: 1.2em; }
        .rate-card .rate, .info-card .price { color: var(--primary-color); font-size: 1.3em; font-weight: 700; }
        .info-card .change { font-size: 1em; font-weight: 600; }
        .info-card .change.positive { color: #2e7d32; }
        .info-card .change.negative { color: #c62828; }

        .news-section { background: var(--card-background); border-radius: 15px; padding: 25px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
        .news-section h2 { color: var(--primary-color); margin-bottom: 20px; font-size: 1.6em; border-bottom: 3px solid var(--primary-color); padding-bottom: 10px; }
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .news-item { background: #f7f9f9; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s; }
        .news-item:hover { transform: translateY(-5px); box-shadow: 0 12px 20px rgba(0,0,0,0.1); }
        .news-image { width: 100%; height: 180px; object-fit: cover; }
        .news-content { padding: 15px; flex-grow: 1; display: flex; flex-direction: column; }
        .news-title a { font-weight: 700; color: var(--secondary-color); text-decoration: none; font-size: 1.15em; }
        .news-title a:hover { text-decoration: underline; }
        .news-description { color: #555; font-size: 0.9em; margin: 10px 0; flex-grow: 1; }
        .news-meta { display: flex; justify-content: space-between; font-size: 0.8em; color: #777; margin-top: 10px; }

        .loading, .error { text-align: center; padding: 40px; font-size: 1.2em; border-radius: 8px; }
        .loading { color: var(--primary-color); }
        .error { background: #ffdddd; color: #d32f2f; }

        @media (max-width: 992px) { .main-grid { grid-template-columns: 1fr; } }
        @media (max-width: 768px) {
            .header h1 { font-size: 2em; } .header p { font-size: 1em; }
            .card h2 { font-size: 1.4em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🌐 Global Markets Dashboard</h1>
            <p>Your real-time window into currency, crypto, and stock markets</p>
        </header>

        <div class="last-updated" id="lastUpdated">Updating...</div>

        <main class="main-grid">
            <div class="card">
                <h2>Currency Converter</h2>
                <div class="converter-form">
                    <div class="input-group"><label for="amount">Amount:</label><input type="number" id="amount" value="100" min="0" step="0.01"></div>
                    <div class="input-group"><label for="fromCurrency">From:</label><select id="fromCurrency"></select></div>
                    <div class="input-group"><label for="toCurrency">To:</label><select id="toCurrency"></select></div>
                    <button class="convert-btn" onclick="convertCurrency()">Convert</button>
                    <div class="result" id="result"></div>
                </div>
            </div>
            <div class="card">
                <h2>Live Exchange Rates (Base: USD)</h2>
                <div id="ratesContainer" class="rates-grid"><div class="loading">Loading rates...</div></div>
            </div>
        </main>

        <div class="secondary-grid">
            <div class="card">
                <h2>🪙 Cryptocurrency Prices</h2>
                <div id="cryptoContainer" class="rates-grid"><div class="loading">Loading crypto prices...</div></div>
            </div>
            <div class="card">
                <h2>🏢 Major Stock Prices</h2>
                <div id="stocksContainer" class="rates-grid"><div class="loading">Loading stock prices...</div></div>
            </div>
        </div>

        <section class="news-section">
            <h2>📰 Latest Market News</h2>
            <div id="newsContainer" class="news-grid"><div class="loading">Loading news...</div></div>
        </section>
    </div>

    <script>
        const API_KEYS = {
            exchangeRate: "{{ EXCHANGERATE_API_KEY }}",
            gnews: "{{ GNEWS_API_KEY }}",
            finnhub: "{{ FINNHUB_API_KEY }}"
        };

        const popularCurrencies = ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "CNY", "INR", "BRL", "ZAR", "SGD"];

        function populateCurrencySelectors(rates) {
            const fromSelect = document.getElementById('fromCurrency');
            const toSelect = document.getElementById('toCurrency');
            const currencies = Object.keys(rates);
            fromSelect.innerHTML = currencies.map(c => `<option value="${c}" ${c === 'USD' ? 'selected' : ''}>${c}</option>`).join('');
            toSelect.innerHTML = currencies.map(c => `<option value="${c}" ${c === 'EUR' ? 'selected' : ''}>${c}</option>`).join('');
        }

        async function loadExchangeRates() {
            const ratesContainer = document.getElementById('ratesContainer');
            if (API_KEYS.exchangeRate === "your_exchangerate_api_key") { ratesContainer.innerHTML = `<div class="error">ExchangeRate API key not set.</div>`; return; }
            try {
                const response = await fetch('/api/rates');
                const data = await response.json();
                if (data.error) { ratesContainer.innerHTML = `<div class="error">${data.error}</div>`; return; }
                populateCurrencySelectors(data.rates);
                displayRates(data.rates);
                document.getElementById('lastUpdated').textContent = `Last Updated: ${new Date(data.timestamp * 1000).toLocaleString()}`;
            } catch (error) { ratesContainer.innerHTML = `<div class="error">Failed to load rates: ${error.message}</div>`; }
        }

        function displayRates(rates) {
            const container = document.getElementById('ratesContainer');
            container.innerHTML = popularCurrencies.map(currency => {
                const rate = rates[currency];
                if (!rate) return '';
                return `<div class="rate-card"><div class="currency">${currency}</div><div class="rate">${rate.toFixed(4)}</div></div>`;
            }).join('');
        }

        async function convertCurrency() {
            const amount = document.getElementById('amount').value;
            const from = document.getElementById('fromCurrency').value;
            const to = document.getElementById('toCurrency').value;
            const resultDiv = document.getElementById('result');
            if (!amount || amount <= 0) { resultDiv.innerHTML = 'Please enter a valid amount'; resultDiv.style.display = 'block'; return; }
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = 'Converting...';
            try {
                const response = await fetch(`/api/convert?amount=${amount}&from=${from}&to=${to}`);
                const data = await response.json();
                if (data.error) { resultDiv.innerHTML = `<div class="error">${data.error}</div>`; return; }
                resultDiv.innerHTML = `${amount} ${from} = <strong>${data.result.toFixed(2)} ${to}</strong>`;
            } catch (error) { resultDiv.innerHTML = `<div class="error">Conversion failed: ${error.message}</div>`; }
        }

        async function loadNews() {
            const newsContainer = document.getElementById('newsContainer');
            if (API_KEYS.gnews === "your_gnews_api_key") { newsContainer.innerHTML = `<div class="error">GNews API key not set.</div>`; return; }
            try {
                const response = await fetch('/api/news');
                const data = await response.json();
                if (data.error) { newsContainer.innerHTML = `<div class="error">${data.error}</div>`; return; }
                displayNews(data.articles);
            } catch (error) { newsContainer.innerHTML = `<div class="error">Failed to load news: ${error.message}</div>`; }
        }

        function displayNews(articles) {
            const container = document.getElementById('newsContainer');
            if (!articles || articles.length === 0) { container.innerHTML = '<div class="loading">No news available.</div>'; return; }
            container.innerHTML = articles.map(article => `
                <div class="news-item">
                    ${article.image ? `<img src="${article.image}" alt="News Image" class="news-image">` : ''}
                    <div class="news-content">
                        <div class="news-title"><a href="${article.url}" target="_blank" rel="noopener noreferrer">${article.title}</a></div>
                        <p class="news-description">${article.description || ''}</p>
                        <div class="news-meta">
                            <span>${new Date(article.publishedAt).toLocaleDateString()}</span>
                            <span>${article.source.name || 'Unknown'}</span>
                        </div>
                    </div>
                </div>`).join('');
        }

        async function loadCrypto() {
            const cryptoContainer = document.getElementById('cryptoContainer');
            try {
                const response = await fetch('/api/crypto');
                const data = await response.json();
                if (data.error) { cryptoContainer.innerHTML = `<div class="error">${data.error}</div>`; return; }
                displayCrypto(data);
            } catch (error) { cryptoContainer.innerHTML = `<div class="error">Failed to load crypto prices: ${error.message}</div>`; }
        }

        function displayCrypto(coins) {
            const container = document.getElementById('cryptoContainer');
            container.innerHTML = Object.keys(coins).map(coinId => {
                const coin = coins[coinId];
                return `
                    <div class="info-card">
                        <div class="name">${coinId.charAt(0).toUpperCase() + coinId.slice(1)}</div>
                        <div class="price">$${coin.usd.toLocaleString()}</div>
                    </div>`;
            }).join('');
        }

        async function loadStocks() {
            const stocksContainer = document.getElementById('stocksContainer');
            if (API_KEYS.finnhub === "d42q0s1r01qorlesiho0d42q0s1r01qorlesihog") { stocksContainer.innerHTML = `<div class="error">Finnhub API key not set.</div>`; return; }
            try {
                const response = await fetch('/api/stocks');
                const data = await response.json();
                if (data.error) { stocksContainer.innerHTML = `<div class="error">${data.error}</div>`; return; }
                displayStocks(data);
            } catch (error) { stocksContainer.innerHTML = `<div class="error">Failed to load stock prices: ${error.message}</div>`; }
        }

        function displayStocks(stocks) {
            const container = document.getElementById('stocksContainer');
            container.innerHTML = Object.keys(stocks).map(ticker => {
                const stock = stocks[ticker];
                const changeClass = stock.dp >= 0 ? 'positive' : 'negative';
                const sign = stock.dp >= 0 ? '+' : '';
                return `
                    <div class="info-card">
                        <div class="name">${ticker}</div>
                        <div>
                            <div class="price">$${stock.c.toFixed(2)}</div>
                            <div class="change ${changeClass}">${sign}${stock.dp.toFixed(2)}%</div>
                        </div>
                    </div>`;
            }).join('');
        }

        window.onload = function() {
            loadExchangeRates();
            loadNews();
            loadCrypto();
            loadStocks();
            setInterval(loadExchangeRates, 300000);
            setInterval(loadNews, 900000);
            setInterval(loadCrypto, 60000);
            setInterval(loadStocks, 300000);
        };
    </script>
</body>
</html>
'''

# --- API Routes ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
        EXCHANGERATE_API_KEY=EXCHANGERATE_API_KEY, 
        GNEWS_API_KEY=GNEWS_API_KEY,
        FINNHUB_API_KEY=FINNHUB_API_KEY)

@app.route('/api/rates')
def get_rates():
    if EXCHANGERATE_API_KEY == "your_exchangerate_api_key": return jsonify({'error': 'Missing ExchangeRate API Key'}), 400
    try:
        url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/USD"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('result') == 'success':
            return jsonify({'rates': data['conversion_rates'], 'timestamp': data['time_last_update_unix']})
        else:
            return jsonify({'error': data.get('error-type', 'API error')}), 500
    except requests.exceptions.RequestException as e: return jsonify({'error': f'API request failed: {e}'}), 500
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/convert')
def convert():
    if EXCHANGERATE_API_KEY == "your_exchangerate_api_key": return jsonify({'error': 'Missing ExchangeRate API Key'}), 400
    try:
        amount = request.args.get('amount', type=float)
        from_currency, to_currency = request.args.get('from'), request.args.get('to')
        if not all([amount, from_currency, to_currency]): return jsonify({'error': 'Missing parameters'}), 400
        url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/pair/{from_currency}/{to_currency}/{amount}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('result') == 'success':
            return jsonify({'result': data['conversion_result'], 'rate': data['conversion_rate']})
        else:
            return jsonify({'error': data.get('error-type', 'Conversion failed')}), 500
    except requests.exceptions.RequestException as e: return jsonify({'error': f'API request failed: {e}'}), 500
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/news')
def get_news():
    if GNEWS_API_KEY == "your_gnews_api_key": return jsonify({'error': 'Missing GNews API Key'}), 400
    try:
        url = f"https://gnews.io/api/v4/search?q=forex OR currency OR stocks&lang=en&max=9&apikey={GNEWS_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return jsonify({'articles': data.get('articles', [])})
    except requests.exceptions.RequestException as e: return jsonify({'error': f'News API request failed: {e}'}), 500
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/crypto')
def get_crypto():
    try:
        ids = "bitcoin,ethereum,ripple,litecoin,cardano,solana"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e: return jsonify({'error': f'Crypto API request failed: {e}'}), 500
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/stocks')
def get_stocks():
    if FINNHUB_API_KEY == "d42q0s1r01qorlesiho0d42q0s1r01qorlesihog": return jsonify({'error': 'Missing Finnhub API Key'}), 400
    try:
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
        stock_data = {}
        for ticker in tickers:
            url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token=d42q0s1r01qorlesiho0d42q0s1r01qorlesihog"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                stock_data[ticker] = data
        return jsonify(stock_data)
    except requests.exceptions.RequestException as e: return jsonify({'error': f'Stock API request failed: {e}'}), 500
    except Exception as e: return jsonify({'error': str(e)}), 500

# --- Main Execution ---

if __name__ == '__main__':
    print("=" * 60)
    print("        🌐 Global Markets Dashboard Server")
    print("=" * 60)
    print("\n[IMPORTANT] SETUP INSTRUCTIONS:")
    print("1. Open this file (Test.py) in a text editor.")
    print("2. Get API keys from:")
    print("   - ExchangeRate-API: https://www.exchangerate-api.com/")
    print("   - GNews: https://gnews.io/")
    print("   - Finnhub: https://finnhub.io/")
    print("3. Replace the 'your_..._api_key' placeholders with your keys.")
    print("\n[INFO] FEATURES:")
    print("  ✓ Real-time currency conversion & rates")
    print("  ✓ Live cryptocurrency prices")
    print("  ✓ Major company stock prices")
    print("  ✓ Latest market news updates")
    print("\n🚀 Starting Flask server...")
    print("   Access the dashboard at: http://127.0.0.1:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)