import requests
from bs4 import BeautifulSoup
import streamlit as st
from forex_python.converter import CurrencyRates

# Function to fetch and convert currency
def fetch_and_convert_currency(usd_value, rate):
    return usd_value * rate

# Function to fetch total collection value and card count
def fetch_total_value_and_count(soup):
    try:
        summary_table = soup.find('table', id='summary')
        total_value_usd = float(summary_table.find('td', class_='js-value js-price').text.strip().replace('$', '').replace(',', ''))
        card_count = int(summary_table.find_all('td', class_='number')[1].text.strip())
        return total_value_usd, card_count
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
    cards = {}
    
    for card in soup.find_all('tr', class_='offer'):
        card_name = card.find('p', class_='title').find('a').text.strip()
        card_link = card.find('p', class_='title').find('a')['href']
        card_image_url = get_high_res_image(card_link)
        grading = card.find('td', class_='includes').text.strip()
        usd_value = float(card.find('span', class_='js-price').text.strip().replace('$', ''))
        aud_value = fetch_and_convert_currency(usd_value, rate_aud)
        yen_value = fetch_and_convert_currency(usd_value, rate_yen)
        
        if card_name not in cards:
            cards[card_name] = {
                "image": card_image_url,
                "gradings": []
            }
        
        cards[card_name]["gradings"].append({
            "grading": grading,
            "usd": usd_value,
            "aud": aud_value,
            "yen": yen_value
        })
    
    for card_name, details in cards.items():
        st.image(details["image"], use_column_width=True)
        st.markdown(f"**{card_name}**")
        
        for grading_info in details["gradings"]:
            st.markdown(f"**Grading:** {grading_info['grading']}")
            st.markdown(f"USD: ${grading_info['usd']:.2f}")
            st.markdown(f"AUD: ${grading_info['aud']:.2f}")
            st.markdown(f"YEN: ¥{grading_info['yen']:.2f}")
            st.markdown("---")

# Main function
def main():
    st.markdown("<h1 style='text-align: center; font-family: Pokemon; color: #FFCC00;'>PokéDan</h1>", unsafe_allow_html=True)
    
    url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Fetch total value and card count
    total_value_usd, card_count = fetch_total_value_and_count(soup)
    c = CurrencyRates()
    rate_aud = c.get_rate('USD', 'AUD')
    rate_yen = c.get_rate('USD', 'JPY')
    
    if total_value_usd and card_count:
        total_value_aud = fetch_and_convert_currency(total_value_usd, rate_aud)
        total_value_yen = fetch_and_convert_currency(total_value_usd, rate_yen)
        st.markdown(f"<p style='text-align: center; color: lightgray;'>Total Collection Value: ${total_value_usd:.2f} USD / ${total_value_aud:.2f} AUD / ¥{total_value_yen:.2f} YEN</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: lightgray;'>Total Cards: {card_count}</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='text-align: center; color: lightgray;'>Total Collection Value: Not available</p>", unsafe_allow_html=True)

    # Display card info
    display_card_info(soup, rate_aud, rate_yen)

if __name__ == "__main__":
    main()
