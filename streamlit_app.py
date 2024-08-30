import streamlit as st
import requests
from bs4 import BeautifulSoup
import time

# Function to fetch currency rates
def get_exchange_rates():
    try:
        url = "https://www.xe.com/currencycharts/?from=USD&to=AUD"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        rate_aud = float(soup.find('tr', {'data-sleek-node-id': '240706'}).find_all('td')[1].text.strip())

        url = "https://www.xe.com/currencycharts/?from=USD&to=JPY"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        rate_yen = float(soup.find('tr', {'data-sleek-node-id': 'e604a2'}).find_all('td')[1].text.strip())

        return rate_aud, rate_yen
    except Exception as e:
        st.error(f"Error fetching currency rates: {e}")
        return None, None

# Function to fetch total collection value and count
def fetch_total_value(soup):
    try:
        summary_table = soup.find('table', id='summary')
        total_value_usd = summary_table.find('td', class_='js-value js-price').text.strip().replace('$', '').replace(',', '')
        total_count = summary_table.find_all('td', class_='number')[1].text.strip()
        return float(total_value_usd), int(total_count)
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

# Function to display card info
def display_card_info(soup, rate_aud, rate_yen):
    cards = {}
    
    for card in soup.find_all('tr', class_='offer'):
        try:
            card_name = card.find('p', class_='title').find('a').text.strip()
            card_link = card.find('p', class_='title').find('a')['href']
            card_image_url = get_high_res_image(card_link)
            grading = card.find('td', class_='includes').text.strip()
            price_usd = float(card.find('td', class_='price').find('span', class_='js-price').text.strip().replace('$', ''))
            
            # Convert price to AUD and JPY
            if rate_aud and rate_yen:
                price_aud = price_usd * rate_aud
                price_yen = price_usd * rate_yen
            else:
                price_aud = price_yen = None
            
            if card_name not in cards:
                cards[card_name] = {
                    'image': card_image_url,
                    'gradings': []
                }
            
            cards[card_name]['gradings'].append((grading, price_aud, price_yen))
        except Exception as e:
            st.warning(f"Card name tag not found, skipping entry. Error: {e}")
    
    for card_name, card_data in cards.items():
        st.image(card_data['image'], width=300)
        st.markdown(f"**{card_name}**")
        for grading, price_aud, price_yen in card_data['gradings']:
            st.markdown(f"**{grading}:** ${price_aud:.2f} AUD | ¥{price_yen:.2f} JPY")
        st.write("---")

# Main function
def main():
    st.title("PokéDan")
    
    url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    st.markdown("---")
    
    rate_aud, rate_yen = get_exchange_rates()
    if rate_aud is None or rate_yen is None:
        st.error("Currency rates could not be fetched.")
    
    total_value_usd, total_count = fetch_total_value(soup)
    if total_value_usd is None or total_count is None:
        st.error("Total value and count could not be fetched.")
        st.markdown(f"### Total Collection Value: Not available")
    else:
        total_value_aud = total_value_usd * rate_aud if rate_aud else None
        total_value_yen = total_value_usd * rate_yen if rate_yen else None
        st.markdown(f"### Total Collection Value: ${total_value_aud:.2f} AUD | ¥{total_value_yen:.2f} JPY")
        st.markdown(f"#### Total Cards: {total_count}")
    
    st.markdown("---")
    
    display_card_info(soup, rate_aud, rate_yen)
    
    st.markdown(f"**Last updated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
if __name__ == "__main__":
    main()
