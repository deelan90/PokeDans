import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict

# Function to fetch and convert currency using real-time rates from XE.com
def fetch_and_convert_currency(usd_value):
    try:
        # Fetch exchange rates from XE.com
        rate_aud = fetch_exchange_rate("USD", "AUD")
        rate_yen = fetch_exchange_rate("USD", "JPY")
        
        value_usd = float(usd_value.replace('$', '').replace(',', '').strip())
        value_aud = value_usd * rate_aud
        value_yen = value_usd * rate_yen
        return value_aud, value_yen
    except ValueError:
        return None, None

# Function to fetch exchange rates from XE.com
def fetch_exchange_rate(from_currency, to_currency):
    url = f"https://www.xe.com/currencycharts/?from={from_currency}&to={to_currency}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the rate in the page based on the provided HTML structure
    rate_tag = soup.find('p', class_='sc-b39d611a-0 hjhFZZ', text=lambda x: x and f"1 {from_currency} = " in x)
    if rate_tag:
        rate_text = rate_tag.text.strip()
        rate_value = rate_text.split('=')[1].strip().split(' ')[0]
        return float(rate_value)
    else:
        st.error(f"Could not fetch exchange rate for {from_currency} to {to_currency}")
        return None

# Function to fetch total value and card count
def fetch_total_value_and_count(soup):
    try:
        summary_table = soup.find('table', id='summary')
        total_value_usd = summary_table.find('td', class_='js-value js-price').text.strip().replace('$', '').replace(',', '')
        total_count = summary_table.find_all('td', class_='number')[-1].text.strip()
        return total_value_usd, total_count
    except AttributeError:
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
def display_card_info(soup):
    card_groups = defaultdict(list)
    
    # Group cards by name
    card_rows = soup.find_all('tr', class_='offer')
    for card in card_rows:
        try:
            card_name_tag = card.find('p', class_='title')
            if not card_name_tag:
                continue
            card_name = card_name_tag.text.strip()
            card_link = card.find('a')['href']
            grading = card.find('td', class_='includes').text.strip()
            price_usd = card.find('span', class_='js-price').text.strip()
            card_groups[card_name].append({
                'link': card_link,
                'grading': grading,
                'price_usd': price_usd,
            })
        except Exception as e:
            st.error(f"An error occurred while processing a card: {e}")
    
    # Display grouped cards
    cols = st.columns(4)  # Create 4 columns
    for index, (card_name, cards) in enumerate(card_groups.items()):
        try:
            # Fetch high-resolution image (using the link of the first card in the group)
            image_url = get_high_res_image(cards[0]['link'])
            
            # Display the card in the appropriate column
            with cols[index % 4]:
                st.image(image_url, caption=card_name, use_column_width=True)
                for card in cards:
                    # Convert currency
                    price_aud, price_yen = fetch_and_convert_currency(card['price_usd'])
                    if price_aud is not None and price_yen is not None:
                        st.write(f"Grading: **{card['grading']}**")
                        st.write(f"Value: ${price_aud:.2f} AUD / ¥{price_yen:.2f} Yen")
                    else:
                        st.write("Could not fetch conversion rates.")
        except Exception as e:
            st.error(f"An error occurred while displaying the card: {e}")

def main():
    # Set the title and subtitle
    st.markdown("<h1 style='text-align: center; color: #FFCC00; font-family: \"Pokemon Solid\";'>PokéDan</h1>", unsafe_allow_html=True)
    
    # Link to collection page
    url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Fetch total value and count
    total_value_usd, total_count = fetch_total_value_and_count(soup)
    if total_value_usd:
        total_value_aud, total_value_yen = fetch_and_convert_currency(total_value_usd)
        st.write(f"Total Collection Value: **${total_value_aud:.2f} AUD / ¥{total_value_yen:.2f} Yen**", unsafe_allow_html=True)
    else:
        st.write("Total Collection Value: Not available", unsafe_allow_html=True)

    if total_count:
        st.write(f"Total Cards: **{total_count}**", unsafe_allow_html=True)
    else:
        st.write("Total Cards: Not available", unsafe_allow_html=True)

    # Display card info
    display_card_info(soup)

    # Last updated time
    st.markdown(f"**Last updated:** {datetime.now()}")

if __name__ == "__main__":
    main()
