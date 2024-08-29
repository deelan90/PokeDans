import requests
from bs4 import BeautifulSoup
import streamlit as st
from PIL import Image
from io import BytesIO

# Function to fetch high-resolution images
def get_high_res_image(card_link):
    try:
        card_page_response = requests.get(f"https://www.pricecharting.com{card_link}")
        card_page_response.raise_for_status()
        card_page_soup = BeautifulSoup(card_page_response.content, 'html.parser')

        # Find the highest resolution image available
        card_image_element = card_page_soup.find('img', {'src': lambda x: x and ('jpeg' in x.lower() or 'jpg' in x.lower())})
        return card_image_element.get('src') if card_image_element else None
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
        return None

# Function to fetch the exchange rates manually
def get_exchange_rates():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    response = requests.get(url, verify=False)  # Disable SSL verification
    data = response.json()
    
    rate_aud = data['rates']['AUD']
    rate_yen = data['rates']['JPY']
    
    return rate_aud, rate_yen

# Function to fetch the total value and card count from the summary table
def fetch_total_value_and_count(soup):
    summary_table = soup.find('table', id='summary')
    if summary_table:
        total_value_element = summary_table.find('td', class_='js-value js-price')
        card_count_element = summary_table.find_all('td', class_='number')[1]  # Assuming the count is the second number

        if total_value_element and card_count_element:
            total_value_usd = total_value_element.text.strip().replace('$', '').replace(',', '')
            card_count = card_count_element.text.strip()
            return float(total_value_usd), int(card_count)
    
    return None, None  # Return None if the values can't be found

# Function to fetch and display card images and prices
def display_card_info(soup, rate_aud, rate_yen):
    card_elements = soup.select('div.panel.panel-default')
    card_data = []
    for card in card_elements:
        title = card.select_one('h3').text.strip()
        card_link = card.select_one('a')['href']
        img_url = get_high_res_image(card_link)  # Use high-resolution image

        grade_rows = card.select('table tr')
        
        grading_info = []
        for row in grade_rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                grading_name = cols[2].text.strip()
                price_usd = cols[0].text.strip().replace('$', '').replace(',', '')
                if price_usd != 'N/A':
                    price_aud = float(price_usd) * rate_aud
                    price_yen = float(price_usd) * rate_yen
                    grading_info.append((grading_name, price_aud, price_yen))
        
        card_data.append((title, img_url, grading_info))
    
    for title, img_url, grading_info in card_data:
        st.image(img_url, caption=title, width=200)
        for grading_name, price_aud, price_yen in grading_info:
            st.write(f"**{grading_name}**: ${price_aud:,.2f} AUD / ¥{price_yen:,.0f} JPY")
        st.write("---")

# Main function to run the Streamlit app
def main():
    st.title("PokéDan")
    st.write("### Pokémon Card Collection")
    
    # Fixed link to the Pokémon card collection
    url = "https://www.pricecharting.com/offers?status=collection&seller=yx5zdzzvnnhyvjeffskx64pus4&sort=name&category=all&folder-id=&condition-id=all"
    
    # Fetch and parse the collection page
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Get the exchange rates
    rate_aud, rate_yen = get_exchange_rates()

    # Fetch and display the total collection value and card count
    total_value_usd, card_count = fetch_total_value_and_count(soup)
    if total_value_usd is not None and card_count is not None:
        total_value_aud = total_value_usd * rate_aud
        total_value_yen = total_value_usd * rate_yen
        st.write(f"Total Collection Value: ${total_value_aud:,.2f} AUD / ¥{total_value_yen:,.0f} JPY", style="color: lightgray;")
        st.write(f"Total Cards: {card_count}", style="color: lightgray;")
    else:
        st.write("Total Collection Value and Card Count: Not available", style="color: lightgray;")
    
    # Display the Pokémon cards and their grading values
    display_card_info(soup, rate_aud, rate_yen)

if __name__ == "__main__":
    main()
