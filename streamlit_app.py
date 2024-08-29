import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from forex_python.converter import CurrencyRates

# Function to fetch and convert currency
def fetch_and_convert_currency(usd_value):
    c = CurrencyRates()
    try:
        rate_aud = c.get_rate('USD', 'AUD')
        rate_yen = c.get_rate('USD', 'JPY')
    except Exception as e:
        st.error(f"Error fetching currency rates: {e}")
        rate_aud = None
        rate_yen = None

    if rate_aud and rate_yen:
        value_aud = float(usd_value) * rate_aud
        value_yen = float(usd_value) * rate_yen
        return value_aud, value_yen
    else:
        return None, None

# Function to fetch the total value and count of cards
def fetch_total_value_and_count(soup):
    try:
        summary_table = soup.find('table', {'id': 'summary'})
        if summary_table:
            total_value_usd = summary_table.find('td', class_='js-value js-price')
            if total_value_usd:
                total_value_usd = total_value_usd.text.strip().replace('$', '').replace(',', '')
            else:
                total_value_usd = None

            card_count = summary_table.find_all('td', class_='number')
            if card_count:
                card_count = card_count[-1].text.strip()
            else:
                card_count = None

            return total_value_usd, card_count
        else:
            return None, None
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
def display_card_info(soup, rate_aud, rate_yen):
    card_rows = soup.find_all('tr', class_='offer')
    
    for card in card_rows:
        title_element = card.find('p', class_='title')
        card_name = title_element.find('a').text.strip() if title_element else "No name found"
        
        grading_element = card.find('td', class_='includes')
        grading = grading_element.text.strip() if grading_element else "Ungraded"
        
        price_element = card.find('span', class_='js-price')
        price_usd = price_element.text.strip().replace('$', '').replace(',', '') if price_element else "0.00"
        
        card_link_tag = card.find('a')
        card_link = card_link_tag['href'] if card_link_tag else None
        
        if card_link:
            img_url = get_high_res_image(card_link)
            st.image(img_url, use_column_width=True)
        
        st.markdown(f"### {card_name}")
        st.markdown(f"**Grading**: {grading}")
        st.markdown(f"**USD**: ${price_usd}")
        
        if rate_aud and rate_yen:
            value_aud = float(price_usd) * rate_aud
            value_yen = float(price_usd) * rate_yen
            st.markdown(f"**AUD**: ${value_aud:.2f}")
            st.markdown(f"**YEN**: ¥{value_yen:.2f}")
        st.markdown("---")

# Main app function
def main():
    st.markdown(
        """
        <style>
        @font-face {
            font-family: "Pokémon";
            src: url("path_to_your_font_file");
        }
        h1 {
            font-family: "Pokémon", sans-serif;
            color: #FFCC00;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <h1 style='text-align: center; font-family: "Pokémon"; color: #FFCC00;'>PokéDan</h1>
        """,
        unsafe_allow_html=True,
    )

    url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    total_value_usd, card_count = fetch_total_value_and_count(soup)
    
    if total_value_usd:
        rate_aud, rate_yen = fetch_and_convert_currency(total_value_usd)
        st.markdown(f"### Total Collection Value: ${total_value_usd} USD")
        if rate_aud and rate_yen:
            st.markdown(f"### Total Collection Value: ${rate_aud:.2f} AUD / ¥{rate_yen:.2f} JPY")
        st.markdown(f"### Total Cards in Collection: {card_count}")
    else:
        st.markdown("### Total Collection Value: Not available")
        rate_aud, rate_yen = None, None
    
    display_card_info(soup, rate_aud, rate_yen)

if __name__ == "__main__":
    main()
