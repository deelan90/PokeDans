import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# Function to fetch currency rates by scraping XE
def get_exchange_rates():
    try:
        url = "https://www.xe.com/currencycharts/?from=USD&to=JPY"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        rate_jpy = soup.find('td', text='USD / JPY').find_next_sibling('td').text.strip()
        
        url = "https://www.xe.com/currencycharts/?from=USD&to=AUD"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        rate_aud = soup.find('td', text='AUD / USD').find_next_sibling('td').text.strip()

        return float(rate_aud), float(rate_jpy)
    except Exception as e:
        st.error(f"Error fetching currency rates: {e}")
        return None, None

# Function to fetch total value and count of cards
def fetch_total_value(soup):
    try:
        summary_table = soup.find('table', {'id': 'summary'})
        if summary_table:
            total_value_usd = summary_table.find('td', class_='js-value js-price').text.strip().replace('$', '').replace(',', '')
            total_count = summary_table.find_all('td', class_='number')[1].text.strip()
            return float(total_value_usd), int(total_count)
        else:
            raise ValueError("Summary table not found")
    except Exception as e:
        st.error(f"Error fetching total value and count: {e}")
        return None, None

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        return card_image_element.get('src') if card_image_element else None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

# Function to display card information
def display_card_info(soup, rate_aud, rate_jpy):
    cards = {}
    for card in soup.find_all('tr', class_='offer'):
        try:
            card_name = card.find('p', class_='title').find('a').text.strip()
            card_link = card.find('p', class_='title').find('a')['href']
            card_image_url = get_high_res_image(card_link)
            grading = card.find('td', class_='includes').text.strip()
            price_usd = card.find('span', class_='js-price').text.strip().replace('$', '').replace(',', '')

            if card_name not in cards:
                cards[card_name] = {'image_url': card_image_url, 'gradings': {}}
            cards[card_name]['gradings'][grading] = float(price_usd)
        
        except AttributeError as e:
            st.error(f"Card name tag not found, skipping entry. Error: {e}")
            continue

    for card_name, card_data in cards.items():
        st.image(card_data['image_url'], width=200)
        st.markdown(f"**{card_name}**")
        for grading, price_usd in card_data['gradings'].items():
            price_aud = price_usd * rate_aud if rate_aud else 'N/A'
            price_jpy = price_usd * rate_jpy if rate_jpy else 'N/A'
            st.markdown(f"**{grading}:** ${price_usd} USD | ${price_aud} AUD | ¥{price_jpy} JPY")

# Main function
def main():
    st.title("PokéDan")
    
    # Fetching data
    url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Debugging output
    print("Page fetched successfully.")

    rate_aud, rate_jpy = get_exchange_rates()

    if rate_aud is None or rate_jpy is None:
        st.error("Currency rates could not be fetched.")
    else:
        print(f"Rates fetched: AUD/USD={rate_aud}, USD/JPY={rate_jpy}")

    total_value_usd, total_count = fetch_total_value(soup)
    if total_value_usd and total_count:
        st.markdown(f"<p style='text-align: center; color: lightgray;'>Total Collection Value: ${total_value_usd} USD | ¥{total_value_usd * rate_jpy} JPY | ${total_value_usd * rate_aud} AUD</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: lightgray;'>Total Count: {total_count} cards</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='text-align: center; color: lightgray;'>Total Collection Value: Not available</p>", unsafe_allow_html=True)

    # Display card info
    display_card_info(soup, rate_aud, rate_jpy)

    # Auto-update every 3 hours
    st.text(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(10800)

if __name__ == "__main__":
    main()
