import streamlit as st
import requests
from bs4 import BeautifulSoup
import time

# Function to fetch currency rates
def get_exchange_rates():
    try:
        url_aud = "https://www.xe.com/currencycharts/?from=USD&to=AUD"
        url_jpy = "https://www.xe.com/currencycharts/?from=USD&to=JPY"
        
        response_aud = requests.get(url_aud)
        response_jpy = requests.get(url_jpy)
        
        soup_aud = BeautifulSoup(response_aud.content, 'html.parser')
        soup_jpy = BeautifulSoup(response_jpy.content, 'html.parser')
        
        # Add error handling for cases where the expected HTML structure is not found
        rate_aud = None
        rate_yen = None
        
        aud_row = soup_aud.find('tr', {'data-sleek-node-id': '240706'})
        if aud_row:
            rate_aud = float(aud_row.find_all('td')[1].text.strip())
        
        jpy_row = soup_jpy.find('tr', {'data-sleek-node-id': 'e604a2'})
        if jpy_row:
            rate_yen = float(jpy_row.find_all('td')[1].text.strip())
        
        if rate_aud is None or rate_yen is None:
            raise ValueError("Currency rates could not be fetched.")
        
        return rate_aud, rate_yen
    except Exception as e:
        st.error(f"Error fetching currency rates: {e}")
        return None, None

# Function to fetch total collection value and count
def fetch_total_value(soup):
    try:
        summary_table = soup.find('table', id='summary')
        if summary_table:
            total_value_usd = summary_table.find('td', class_='js-value js-price')
            total_count = summary_table.find_all('td', class_='number')
            
            if total_value_usd and total_count:
                total_value_usd = float(total_value_usd.text.strip().replace('$', '').replace(',', ''))
                total_count = int(total_count[1].text.strip())
                return total_value_usd, total_count
        raise ValueError("Total value or count not found in the summary table.")
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
            # Skip header rows by checking if the row contains the expected data elements
            if not card.find('p', class_='title'):
                continue

            card_name_tag = card.find('p', class_='title')
            if card_name_tag is None:
                raise ValueError("Card name tag not found.")
            
            card_name = card_name_tag.find('a').text.strip()
            card_link = card_name_tag.find('a')['href']
            card_image_url = get_high_res_image(card_link)
            grading = card.find('td', class_='includes').text.strip()
            price_usd_tag = card.find('td', class_='price').find('span', class_='js-price')
            if price_usd_tag is None:
                raise ValueError("Price tag not found.")
            
            price_usd = float(price_usd_tag.text.strip().replace('$', ''))
            
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
            aud_display = f"${price_aud:.2f} AUD" if price_aud is not None else "N/A AUD"
            yen_display = f"¥{price_yen:.2f} JPY" if price_yen is not None else "N/A JPY"
            st.markdown(f"**{grading}:** {aud_display} | {yen_display}")
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
