import requests
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup
import time
import re

def fetch_quote_data(ticker):
    """
    Fetches key fundamental data from the 'Quote' section of a company's page.
    """
    url = f"https://dps.psx.com.pk/company/{ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    try:
        print(f"Fetching quote data for {ticker} from {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        data = {}

        # --- Extract from the price container ---
        quote_price_container = soup.find('div', class_='quote__price')
        if quote_price_container:
            closed_price_div = quote_price_container.find('div', class_='quote__close')
            change_value_div = quote_price_container.find('div', class_='change__value')
            change_percent_div = quote_price_container.find('div', class_='change__percent')
            
            if closed_price_div:
                data['Close'] = [closed_price_div.text.strip()]
            if change_value_div:
                data['Change'] = [change_value_div.text.strip()]
            if change_percent_div:
                data['Change %'] = [change_percent_div.text.strip()]
        
        # --- Stats Tab ---
        stats_tab_container = soup.find('div', id='statsTab')
        if not stats_tab_container:
            print("Error: Could not find stats container.")
            return pd.DataFrame()
            
        reg_tab_panel = stats_tab_container.find('div', {'class': 'tabs__panel'})
        if not reg_tab_panel:
            print("Error: Could not find REG tab.")
            return pd.DataFrame()

        for stats_item in reg_tab_panel.find_all('div', class_='stats_item'):
            label_div = stats_item.find('div', class_='stats_label')
            value_div = stats_item.find('div', class_='stats_value')
            
            if label_div and value_div:
                label = label_div.text.strip().replace('(', '').replace(')', '')
                value = value_div.text.strip()
                data[label] = [value]

        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)

    except Exception as e:
        print(f"Error fetching quote: {e}")
        return pd.DataFrame()

def fetch_financials_data(ticker):
    """
    Fetches financial data (Quarterly and Annually) from the Financials tab on PSX.
    """
    url = f"https://dps.psx.com.pk/company/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        print(f"Fetching financials for {ticker} from {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        financials_data = {}

        # --- Financials Section ---
        fin_section = soup.find('div', id='financials')
        if not fin_section:
            print("No financials section found.")
            return financials_data

        for wrapper in fin_section.find_all('div', class_='tbl__wrapper'):
            table = wrapper.find('table', class_='tbl')
            if not table:
                continue
            headers = [th.text.strip() for th in table.find('thead').find_all('th')]

            # Quarterly
            if any('Q' in h for h in headers):
                financials_data['Quarterly'] = {'headers': headers}
                for row in table.find('tbody').find_all('tr'):
                    cols = row.find_all('td')
                    metric = cols[0].text.strip()
                    values = [c.text.strip() for c in cols[1:]]
                    financials_data['Quarterly'][metric] = values

            # Annual
            if any(h.isdigit() and len(h) == 4 for h in headers):
                financials_data['Annually'] = {'headers': headers}
                for row in table.find('tbody').find_all('tr'):
                    cols = row.find_all('td')
                    metric = cols[0].text.strip()
                    values = [c.text.strip() for c in cols[1:]]
                    financials_data['Annually'][metric] = values

        return financials_data

    except Exception as e:
        print(f"Error fetching financials: {e}")
        return {}

def fetch_ratios_data(ticker):
    """
    Fetches annual ratios data from the Ratios tab on PSX.
    """
    url = f"https://dps.psx.com.pk/company/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        ratios_data = {}

        ratios_section = soup.find('div', id='ratios')
        if ratios_section:
            table = ratios_section.find('table', class_='tbl')
            if table:
                headers = [th.text.strip() for th in table.find('thead').find_all('th')]
                ratios_data['headers'] = headers

                for row in table.find('tbody').find_all('tr'):
                    cols = row.find_all('td')
                    metric = cols[0].text.strip()
                    values = [c.text.strip() for c in cols[1:]]
                    ratios_data[metric] = values

        return ratios_data

    except Exception as e:
        print(f"Error fetching ratios: {e}")
        return {}

def fetch_payouts_data(ticker):
    """
    Fetches payout data (dividends, bonus, mode, type) from PSX.
    """
    url = f"https://dps.psx.com.pk/company/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        payouts_data = {}

        payouts_section = soup.find('div', id='payouts')
        if payouts_section:
            payouts_table = payouts_section.find('table', class_='tbl')
            if payouts_table:
                headers = [th.text.strip() for th in payouts_table.find('thead').find_all('th')]
                extended_headers = headers + ['Percentage', 'Type', 'Mode']
                payouts_data['headers'] = extended_headers

                for row in payouts_table.find('tbody').find_all('tr'):
                    cols = [td.text.strip() for td in row.find_all('td')]
                    details = cols[2] if len(cols) >= 3 else ""
                    percentage, dtype, mode = "", "", ""

                    match = re.search(r"([\d\.]+%)", details)
                    if match:
                        percentage = match.group(1)

                    matches = re.findall(r"\((.*?)\)", details)
                    if matches:
                        dtype = matches[0]
                        if len(matches) > 1:
                            mode = matches[-1]

                    payouts_data[cols[0]] = cols + [percentage, dtype, mode]

        return payouts_data

    except Exception as e:
        print(f"Error fetching payouts: {e}")
        return {}

def main():
    print("\n--- PSX Quote Data Scraper ---")
    ticker_symbol = input("Enter stock ticker (e.g., 'EFERT'): ").upper()

    quote_data_df = fetch_quote_data(ticker_symbol)
    financials_data = fetch_financials_data(ticker_symbol)
    ratios_data = fetch_ratios_data(ticker_symbol)
    payouts_data = fetch_payouts_data(ticker_symbol)

    # --- Quote ---
    if not quote_data_df.empty:
        print(f"\nSuccessfully fetched quote for {ticker_symbol}.\n")
        df = quote_data_df.T.reset_index()
        df.columns = ['Metric', 'Value']

        print("\n--- Price & Trading Metrics ---")
        print(df[df['Metric'].isin(['Close','Change','Change %','Open','High','Low','Volume','LDCP'])].to_string(index=False))

        print("\n--- Valuation & Performance Metrics ---")
        print(df[df['Metric'].isin(['P/E Ratio TTM **','1-Year Change * ^','YTD Change * ^','52-WEEK RANGE ^','DAY RANGE','CIRCUIT BREAKER'])].to_string(index=False))

        print("\n--- Other Key Indicators ---")
        print(df[df['Metric'].isin(['VAR','HAIRCUT','Ask Price','Ask Volume','Bid Price','Bid Volume'])].to_string(index=False))
    else:
        print("No quote data found.")

    # --- Financials ---
    if financials_data:
        if 'Annually' in financials_data:
            ad = financials_data['Annually']
            headers = ['Metric'] + ad['headers'][1:]
            rows = [[m]+v for m,v in ad.items() if m!='headers']
            print("\n--- FINANCIALS (Annual) ---")
            print(pd.DataFrame(rows, columns=headers).to_string(index=False))

        if 'Quarterly' in financials_data:
            qd = financials_data['Quarterly']
            headers = ['Metric'] + qd['headers'][1:]
            rows = [[m]+qd[m] for m in ['Sales','Profit after Taxation','EPS'] if m in qd]
            print("\n--- FINANCIALS (Quarterly) ---")
            print(pd.DataFrame(rows, columns=headers).to_string(index=False))

    # --- Ratios ---
    if ratios_data:
        headers = ['Metric'] + ratios_data['headers'][1:]
        rows = [[m]+v for m,v in ratios_data.items() if m!='headers']
        print("\n--- RATIOS (Annual) ---")
        print(pd.DataFrame(rows, columns=headers).to_string(index=False))
    else:
        print("No ratios data found.")

    # --- Payouts ---
    if payouts_data:
        headers = payouts_data['headers']
        rows = [v for k,v in payouts_data.items() if k!='headers']
        print("\n--- PAYOUTS ---")
        print(pd.DataFrame(rows, columns=headers).to_string(index=False))
    else:
        print("No payouts data found.")

if __name__ == "__main__":
    main()
