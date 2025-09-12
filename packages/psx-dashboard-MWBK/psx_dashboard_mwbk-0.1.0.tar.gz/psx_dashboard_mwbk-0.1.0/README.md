### 📈 PSX Dashboard

A powerful, interactive dashboard built with **Streamlit** to fetch and visualize real-time and historical data from the Pakistan Stock Exchange (PSX). This tool is designed for investors, traders, and analysts to perform quick fundamental and technical analysis on KMI-30 companies.

-----

### ✨ Features

  * **Real-Time Data**: Fetches live trading metrics, including price, volume, and bid/ask spread, for a chosen stock.
  * **Historical Analysis**: Displays interactive historical price and volume charts for any selected date range.
  * **Fundamental Metrics**: Retrieves and presents key fundamental data such as P/E Ratio, profit margins, and earnings per share (EPS).
  * **Financials at a Glance**: Provides detailed annual and quarterly financial statements, including sales, profit, and key ratios.
  * **Payout History**: Shows a comprehensive history of dividends and bonus payouts.
  * **User-Friendly Interface**: An intuitive, web-based interface built with Streamlit, making it easy to use for all levels of users.

-----

### 🛠️ Installation

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/psx-dashboard.git
    cd psx-dashboard
    ```

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

    This will install all required libraries, including `streamlit`, `pandas`, `requests`, `beautifulsoup4`, `plotly`, and `numpy`.

-----

### 🚀 Usage

To run the dashboard, execute the following command in your terminal from the project's root directory:

```bash
streamlit run psx_dashboard.py
```

This command will start a local web server and open the dashboard in your browser.

#### How to use the dashboard:

1.  **Select a Company**: Use the dropdown menu in the sidebar to choose a company from the KMI-30 index.
2.  **Set Date Range**: Select a start and end date to view historical data for a specific period.
3.  **Fetch Data**: Click the "Fetch Data" button to load all the information.

-----

### 💡 Data Source & Limitations

All data is scraped from the **Pakistan Stock Exchange (PSX) website**.

  * **Data Accuracy**: The data presented is dependent on the information available on the PSX website. Occasional discrepancies or missing data points may occur.
  * **No API**: This tool relies on web scraping rather than an official API, which means its functionality may be affected by changes to the PSX website's structure.
  * **Delay**: Data is fetched in real-time but may have a slight delay depending on network speed and the time required for scraping.

-----

### 📝 License

This project is licensed under the **MIT License** - see the `LICENSE` file for details.