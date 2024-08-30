import streamlit as st
from bs4 import BeautifulSoup
import requests
from datetime import datetime

# Function to fetch the collection page
def fetch_collection_page():
    try:
        url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"  # Replace with the actual URL
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        print("Page fetched successfully.")
        return soup
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching the collection page: {e}")
        print(f"Page Fetching Error: {e}")
        return None

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        full_url = f"https://www.pricecharting.com{card_link}"
        response = requests.get(full_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tag = soup.find('img', {'id': 'main-image'})
        if img_tag:
            return img_tag['src']
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        print(f"Image Fetching Error: {e}")
        return None

# Function to fetch and convert currency
def fetch_and_convert_currency(amount_in_usd):
    try:
        response = requests.get("https://www.xe.com/currencycharts/?from=USD&to=AUD")
        soup = BeautifulSoup(response.text, 'html.parser')
        aud_rate = float(soup.find_all('td', class_='sc-621fdd77-1 keQHwf')[1].text.strip())
        
        response = requests.get("https://www.xe.com/currencycharts/?from=USD&to=JPY")
        soup = BeautifulSoup(response.text, 'html.parser')
        jpy_rate = float(soup.find_all('td', class_='sc-621fdd77-1 keQHwf')[1].text.strip())
        
        rate_aud = amount_in_usd * aud_rate
        rate_yen = amount_in_usd * jpy_rate

        print(f"Rates fetched: AUD/USD={rate_aud}, USD/JPY={rate_yen}")
        return rate_aud, rate_yen
    except Exception as e:
        st.error(f"Error fetching currency rates: {e}")
        print(f"Currency Fetching Error: {e}")
        return None, None

# Function to fetch and display card information
def display_card_info(soup, rate_aud, rate_yen):
    cards = {}
    try:
        for card in soup.find_all('tr', class_='offer'):
            try:
                card_name = card.find('p', class_='title').find('a').text.strip()
                card_link = card.find('p', class_='title').find('a')['href']
                card_image_url = get_high_res_image(card_link)

                grading = card.find('td', class_='includes').text.strip()
                price = card.find('td', class_='price').text.strip().replace('$', '').replace(',', '')

                price_aud = float(price) * rate_aud if price else 'N/A'
                price_yen = float(price) * rate_yen if price else 'N/A'

                if card_name not in cards:
                    cards[card_name] = {
                        'image': card_image_url,
                        'gradings': {}
                    }

                cards[card_name]['gradings'][grading] = (price_aud, price_yen)
                print(f"Card Processed: {card_name} | Grading: {grading} | Prices: {price_aud} AUD | {price_yen} JPY")
            except Exception as e:
                st.error(f"An error occurred while processing a card: {e}")
                print(f"Card Processing Error: {e}")
                continue

        for card_name, card_data in cards.items():
            st.image(card_data['image'], caption=card_name, width=200)
            for grading, (price_aud, price_yen) in card_data['gradings'].items():
                st.markdown(f"**{grading}:** {price_aud:.2f} AUD | {price_yen:.2f} JPY")
            st.write("---")
    
    except Exception as e:
        st.error(f"An error occurred while displaying cards: {e}")
        print(f"Display Error: {e}")

# Function to fetch total value and count
def fetch_total_value_and_count(soup):
    try:
        summary_table = soup.find('table', {'id': 'summary'})
        if summary_table:
            total_value_usd = summary_table.find('td', class_='js-value').text.strip().replace('$', '').replace(',', '')
            card_count = summary_table.find_all('td', class_='number')[1].text.strip()
            return float(total_value_usd), int(card_count)
        else:
            st.error("Total value or count not found in the summary table.")
            print("Summary Table Parsing Error")
            return None, None
    except Exception as e:
        st.error(f"Error fetching total value and count: {e}")
        print(f"Total Value Fetching Error: {e}")
        return None, None

# Main function
def main():
    # Fetch and parse the page
    soup = fetch_collection_page()

    if soup:
        print("Page fetched successfully.")
        
        # Fetch currency rates
        rate_aud, rate_yen = fetch_and_convert_currency(1.0)
        
        if rate_aud and rate_yen:
            # Fetch total collection value and count
            total_value_usd, card_count = fetch_total_value_and_count(soup)
            if total_value_usd is not None:
                total_value_aud, total_value_yen = total_value_usd * rate_aud, total_value_usd * rate_yen
                st.markdown(f"<h3 style='text-align: center;'>Total Collection Value: {total_value_aud:.2f} AUD | {total_value_yen:.2f} JPY</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: lightgray;'>Total Cards: {card_count}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<h3 style='text-align: center;'>Total Collection Value: Not available</h3>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='text-align: center;'>Total Collection Value: Not available</h3>", unsafe_allow_html=True)
        
        # Display card info
        display_card_info(soup, rate_aud, rate_yen)
        
        # Last updated time
        st.markdown(f"**Last updated:** {datetime.now()}")
    else:
        st.error("Failed to fetch the collection page.")

if __name__ == "__main__":
    main()
