import requests
import pandas as pd
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup

# The URL for the POST request
API_URL = "https://dps.psx.com.pk/historical"

def fetch_psx_data_html(ticker, start_date, end_date):
    """
    Fetches historical stock data by parsing an HTML response from PSX.
    
    This function sends a POST request to the PSX historical data page,
    which returns an HTML response containing a data table. It then uses
    Beautiful Soup to parse this table and convert it into a pandas DataFrame.
    """
    try:
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        payload = {
            'symbol': ticker,
            'from': start_str,
            'to': end_str,
        }

        print(f"Fetching HTML data for {ticker} using a POST request...")

        response = requests.post(API_URL, data=payload)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        data_table = soup.find('table', id='historicalTable')

        if data_table:
            headers = [header.text.strip() for header in data_table.find_all('th')]
            rows = []
            for row in data_table.find_all('tr')[1:]:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                rows.append(cols)
            if rows:
                df = pd.DataFrame(rows, columns=headers)
                return df
            else:
                return pd.DataFrame()
        else:
            print("Error: Could not find the data table in the HTML response.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def main():
    """
    Main function to run the interactive scraper.
    """
    print("\n--- PSX Data Scraper ---")
    
    ticker_symbol = input("Enter the stock ticker symbol (e.g., 'ENGRO'): ").upper()
    
    while True:
        try:
            start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

    # Get end date from user, with an option to press Enter for the same date
    while True:
        try:
            end_date_str = input("Enter the end date (YYYY-MM-DD) or press Enter for the same date: ")
            if end_date_str == "":
                end_date = start_date
            else:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            
            if end_date < start_date:
                print("End date cannot be before start date. Please try again.")
            else:
                break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            
    engro_data = fetch_psx_data_html(ticker_symbol, start_date, end_date)

    if engro_data is not None:
        print(f"\nSuccessfully fetched data for {ticker_symbol}.")
        
        engro_data['DATE'] = pd.to_datetime(engro_data['DATE'], format='%b %d, %Y', errors='coerce')
        engro_data.dropna(subset=['DATE'], inplace=True)
        
        engro_data = engro_data[(engro_data['DATE'] >= pd.to_datetime(start_date)) & (engro_data['DATE'] <= pd.to_datetime(end_date))]
        
        if not engro_data.empty:
            print("Here is the data for the requested date range:")
            print(engro_data.to_string())
        else:
            print("\nNo data found for the date range.")
    else:
        print(f"\nFailed to fetch data for {ticker_symbol}.")

if __name__ == "__main__":
    main()
