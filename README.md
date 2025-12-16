# Quant-Development-assessment

# Real-Time Pair Trading Analytics Dashboard

A high-performance, full-stack analytical platform designed for **Statistical Arbitrage**. This system ingests live tick data from Binance, processes it into OHLCV bars, and computes real-time quantitative metrics including **Hedge Ratio (Beta)**, **Spread**, and **Rolling Z-Scores**.



---

## 🏗️ System Architecture

The project is built with a decoupled architecture to ensure scalability and high-speed data processing, aligning with institutional-grade development standards.

### **1. Data Ingestion (WebSocket Client)**
Managed in `websocket_client.py`, this module maintains a persistent connection to Binance's `!miniTicker@arr` stream. It uses an asynchronous buffer to capture high-frequency price changes for `BTCUSDT` and `ETHUSDT` without blocking the analytical calculations.

### **2. Storage & Resampling (Data Handler)**
The `data_handler.py` module acts as the "ETL" (Extract, Transform, Load) layer. It resamples raw price ticks into 1-second OHLCV bars using **Pandas** and persists them into an **SQLite** database (`db.sqlite`). This allows the system to maintain the historical state required for rolling window calculations.

### **3. Quantitative Backend (FastAPI)**
The `main.py` script hosts a FastAPI server that acts as the bridge between the database and the UI. It provides high-performance endpoints for:
* **Real-time OHLCV delivery.**
* **On-demand Statistical computation.**
* **ADF Statistical testing.**

### **4. Interactive Frontend (Streamlit)**
The `app.py` file provides a professional dashboard for traders. It features a continuous refresh loop (500ms) that fetches live metrics and renders interactive Plotly charts.

---

## 🛠️ Library Rationale

| Library | Primary Usage | Rationale |
| :--- | :--- | :--- |
| **Pandas** | Data Manipulation | Essential for time-series resampling and efficient rolling window calculations. |
| **NumPy** | Vectorized Math | Provides the speed required for calculating Z-Scores and spreads in a live loop. |
| **Statsmodels** | Statistical Tests | Professional-grade OLS regression for Hedge Ratios and ADF tests for stationarity. |
| **Plotly** | Visualization | Offers high-performance, interactive financial-grade charting. |
| **FastAPI** | API Framework | Supports asynchronous programming, critical for real-time data streaming. |
| **SQLite3** | Persistence | Lightweight, serverless relational storage for local high-frequency data. |

---

## 📂 Project Structure & Logic

* **`analytics.py`**: Encapsulates the quantitative logic. It calculates the **Hedge Ratio (Beta)** using OLS to determine the relationship between Asset X and Asset Y. It then derives a mean-reverting **Spread** and its corresponding **Z-Score**.
* **`websocket_client.py`**: Implements the ingestion pipeline. It buffers ticks and triggers the storage process once a data threshold (50 ticks) is met.
* **`data_handler.py`**: Manages the database schema and the conversion of raw market data into structured time-series bars.
* **`app.py`**: Implements the UI logic, including a unique key-management system for Streamlit components to ensure smooth real-time updates without ID collisions.

---

## ⚡ Setup & Installation

1.  **Clone the Repository**:
    ```bash
    git clone [https://github.com/your-username/pair-trading-dashboard.git](https://github.com/your-username/pair-trading-dashboard.git)
    cd pair-trading-dashboard
    ```

2.  **Install Dependencies**:
    ```bash
    pip install pandas numpy statsmodels plotly fastapi uvicorn requests streamlit websockets
    ```

3.  **Run the Backend**:
    ```bash
    python main.py
    ```

4.  **Launch the Dashboard**:
    ```bash
    streamlit run app.py
    ```

---

## 🤖 AI Assistance Statement
**Note on AI Usage**: Google Gemini was utilized as a thought partner for **frontend UI design patterns** (Streamlit component layout, reactive state management) and **code optimization** (resolving duplicate element ID errors in high-frequency refresh loops). All core quantitative logic, database schema design, and backend architectural decisions were developed independently to fulfill the Quant Development assignment requirements.
