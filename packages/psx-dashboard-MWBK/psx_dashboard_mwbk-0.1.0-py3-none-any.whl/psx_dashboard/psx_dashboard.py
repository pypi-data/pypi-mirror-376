import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import requests
from bs4 import BeautifulSoup
import re
import os

# Import your functions from the other scripts
from psx_price_and_volume import fetch_psx_data_html
from psx_fundamental_analysis import fetch_quote_data, fetch_financials_data, fetch_ratios_data, fetch_payouts_data

# Function to load KMI-30 companies from a CSV file
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_kmi30_from_csv():
    """
    Loads a list of KMI-30 companies from a local CSV file.
    
    The CSV file should have at least two columns: 'Ticker' and 'Company Name'.
    """
    # Construct the absolute path to the CSV file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "KMI30", "kmi30_companies.csv")

    if os.path.exists(file_path):
        try:
            # Use pandas to read the CSV file
            df = pd.read_csv(file_path)
            # Create a dictionary mapping Ticker to Company Name, using the correct column names
            companies = dict(zip(df['Stock Symbol'], df['Company Name']))
            return companies
        except Exception as e:
            st.error(f"Error reading the CSV file: {e}")
            return {}
    else:
        st.error(f"File not found at: {file_path}")
        return {}


# Set page configuration
st.set_page_config(layout="wide", page_title="PSX Stock Dashboard")

# Create a sidebar for user input
st.sidebar.header("User Input")

# Fetch the dynamic list of KMI-30 companies from the CSV file
kmi30_companies = load_kmi30_from_csv()

if kmi30_companies:
    # Create the dropdown menu with the fetched list
    selected_option = st.sidebar.selectbox(
        "Choose Company from KMI-30",
        options=list(kmi30_companies.keys()),
        format_func=lambda x: f"{kmi30_companies[x]} - ({x})"
    )
    # The selected_option is the ticker (e.g., "ENGRO")
    ticker = selected_option
else:
    st.sidebar.warning("Could not find or read the company list. Using a default ticker.")
    ticker = st.sidebar.text_input("Choose Company", "ENGRO").upper()


# Add a date range selector
today = date.today()
start_date = st.sidebar.date_input("Start Date", today - timedelta(days=90))
end_date = st.sidebar.date_input("End Date", today)

# Main dashboard layout
st.title(f"📊 PSX Stock Dashboard for {ticker}")
st.write("---")

# Fetch and display data
if st.button("Fetch Data"):
    with st.spinner("Fetching data..."):
        historical_df = fetch_psx_data_html(ticker, start_date, end_date)
        quote_df = fetch_quote_data(ticker)
        # Call the new, separate functions
        financials_data = fetch_financials_data(ticker)
        ratios_data = fetch_ratios_data(ticker)
        payouts_data = fetch_payouts_data(ticker)
        
    # Historical Data Section
    if historical_df is not None and not historical_df.empty:
        st.header("Price and Volume Chart")
        historical_df['DATE'] = pd.to_datetime(historical_df['DATE'], format='%b %d, %Y', errors='coerce')
        historical_df.dropna(subset=['DATE'], inplace=True)
        filtered_historical_df = historical_df[(historical_df['DATE'].dt.date >= start_date) & (historical_df['DATE'].dt.date <= end_date)]
        
        if not filtered_historical_df.empty:
            fig = px.line(filtered_historical_df, x='DATE', y='CLOSE', title=f'{ticker} Historical Price')
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("Historical Data Table")
            st.dataframe(filtered_historical_df)
        else:
            st.warning("No historical data found for the selected date range.")
    else:
        st.warning("Historical data not found for the selected date range.")

    st.write("---")

    # Fundamental Analysis Section (with tooltips)
    if quote_df is not None and not quote_df.empty:
        st.header("Fundamental Analysis")
        df_display = quote_df.T.reset_index().rename(columns={'index': 'Metric', 0: 'Value'})
        tooltips = {
            'Close': 'The final price of the stock at the end of the trading day.',
            'Change': 'The difference between the current day\'s closing price and the previous day\'s closing price.',
            'Change %': 'The percentage change in the stock\'s price from the previous day\'s close.',
            'Open': 'The price at which the stock first traded at the start of the trading day.',
            'High': 'The highest price the stock reached during the current trading day.',
            'Low': 'The lowest price the stock reached during the current trading day.',
            'Volume': 'The total number of shares that were traded during the day.',
            'LDCP': 'The closing price of the stock from the previous trading day.',
            'Ask Price': 'The lowest price a seller is willing to accept for the stock.',
            'Ask Volume': 'The number of shares available for sale at the current Ask Price.',
            'Bid Price': 'The highest price a buyer is willing to pay for the stock.',
            'Bid Volume': 'The number of shares a buyer is willing to purchase at the current Bid Price.',
            'P/E Ratio TTM **': 'The price-to-earnings ratio, calculated using the stock\'s current price and its earnings per share over the past 12 months.',
            '1-Year Change * ^': 'The percentage change in the stock\'s price over the last year.',
            'YTD Change * ^': 'The percentage change in the stock\'s price from the first trading day of the current calendar year to the present.',
            '52-WEEK RANGE ^': 'The highest and lowest prices at which the stock has traded over the past 52 weeks.',
            'DAY RANGE': 'The range between the highest and lowest prices of the stock for the current trading day.',
            'CIRCUIT BREAKER': 'These are price limits set by the exchange to temporarily halt trading when a stock\'s price moves by a predefined percentage, which is designed to prevent excessive volatility and panic selling.',
            'VAR': 'A risk management metric that estimates the potential loss in the value of a stock or portfolio over a specific time period, typically one day, with a certain level of confidence.',
            'HAIRCUT': 'A percentage reduction applied to the market value of a security when it\'s used as collateral for a loan or margin requirement. It serves as a buffer to protect lenders against potential losses from price drops.'
        }
        df_display['Description'] = df_display['Metric'].map(tooltips)
        df_display.fillna('', inplace=True)
        st.dataframe(
            df_display,
            column_config={
                "Metric": st.column_config.TextColumn("Metric"),
                "Value": st.column_config.TextColumn("Value"),
                "Description": st.column_config.TextColumn("Info", help="Hover over a metric to see its description."),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("Quote data not found.")

    st.write("---")

    # Financials, Ratios, and Payouts Section
    st.header("Financials & Ratios")
    
    if financials_data:
        # Check for Annual Financials
        if 'Annually' in financials_data:
            st.subheader("Annual Financials")
            ad = financials_data['Annually']
            headers = ['Metric'] + ad['headers'][1:]
            
            # Filter for specific annual metrics (Sales, Profit, EPS)
            annual_metrics = ['Sales', 'Profit after Taxation', 'EPS']
            annual_rows = [[m] + ad.get(m, ['N/A'] * (len(headers) - 1)) for m in annual_metrics]
            
            # Tooltips for annual financials
            annual_fin_tooltips = {
                'Sales': 'The total revenue generated by the company over the year.',
                'Profit after Taxation': 'The company\'s net profit after all taxes have been deducted for the fiscal year.',
                'EPS': 'The portion of a company\'s annual profit allocated to each outstanding share of common stock.'
            }
            annual_df = pd.DataFrame(annual_rows, columns=headers)
            annual_df['Info'] = annual_df['Metric'].map(annual_fin_tooltips)
            
            st.dataframe(
                annual_df,
                column_config={"Info": st.column_config.TextColumn("Info", help="Hover over a metric to see its description.")},
                use_container_width=True
            )

        # Check for Quarterly Financials
        if 'Quarterly' in financials_data:
            st.subheader("Quarterly Financials")
            qd = financials_data['Quarterly']
            headers = ['Metric'] + qd['headers'][1:]
            
            # Filter for specific quarterly metrics (Sales, Profit, EPS)
            quarterly_metrics = ['Sales', 'Profit after Taxation', 'EPS']
            quarterly_rows = [[m] + qd.get(m, ['N/A'] * (len(headers) - 1)) for m in quarterly_metrics]

            # Tooltips for quarterly financials
            quarterly_tooltips = {
                'Sales': 'The total revenue generated by the company over the quarter.',
                'Profit after Taxation': 'The company\'s net profit after all taxes have been deducted for the quarter.',
                'EPS': 'The portion of a company\'s quarterly profit allocated to each outstanding share of common stock.'
            }
            quarterly_df = pd.DataFrame(quarterly_rows, columns=headers)
            quarterly_df['Info'] = quarterly_df['Metric'].map(quarterly_tooltips)
            
            st.dataframe(
                quarterly_df, 
                column_config={"Info": st.column_config.TextColumn("Info", help="Hover over a metric to see its description.")},
                use_container_width=True
            )
            
    if ratios_data:
        st.subheader("Annual Ratios")
        headers = ['Metric'] + ratios_data['headers'][1:]
        rows = [[m] + v for m, v in ratios_data.items() if m != 'headers']
        
        # Tooltips for ratios
        annual_tooltips = {
            'Gross Profit Margin (%)': 'This profitability ratio measures the percentage of revenue remaining after deducting the cost of goods sold.',
            'Net Profit Margin (%)': 'This metric indicates the percentage of revenue left after all expenses, including taxes, have been deducted.',
            'EPS Growth (%)': 'It shows the rate at which a company\'s earnings per share (EPS) is increasing or decreasing over a period.',
            'PEG': 'A valuation tool that combines the P/E ratio with a company\'s earnings growth rate to provide a more comprehensive view of its value.'
        }
        ratios_df = pd.DataFrame(rows, columns=headers)
        ratios_df['Info'] = ratios_df['Metric'].map(annual_tooltips)
        
        st.dataframe(
            ratios_df,
            column_config={"Info": st.column_config.TextColumn("Info", help="Hover over a metric to see its description.")},
            use_container_width=True
        )

    if payouts_data:
        st.subheader("Payouts")
        headers = payouts_data['headers']
        rows = [v for k, v in payouts_data.items() if k != 'headers']
        payouts_df = pd.DataFrame(rows, columns=headers)
        st.dataframe(payouts_df, use_container_width=True)
    
    # If no financial data is found at all
    if not financials_data and not ratios_data and not payouts_data:
        st.warning("No financials, ratios, or payouts data found.")