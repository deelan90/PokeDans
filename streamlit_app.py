import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Function to fetch high-resolution image
def get_high_res_image(card_link):
    try:
        response = requests.get(card_link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            image_url = soup.find('img', class_='js-card-image')['src']
            return image_url
        else:
            st.error(f"Error fetching high-resolution image: {response.status_code}")
    except Exception as e:
        st.error(f"Error fetching high-resolution image: {e}")
    return None

# Function to fetch and convert currency rates
def fetch_and_convert_currency(price_usd):
    try:
        response = requests.get("https://www.xe.com/currencycharts/?from=USD&to=AUD")
        soup = BeautifulSoup(response.content, 'html.parser')
        rate_aud = float(soup.find_all('td', class_='sc-621fdd77-1 keQHwf')[1].text.strip())
        
        response = requests.get("https://www.xe.com/currencycharts/?from=USD&to=JPY")
        soup = BeautifulSoup(response.content, 'html.parser')
        rate_yen = float(soup.find_all('td', class_='sc-621fdd77-1 keQHwf')[1].text.strip())

        st.write(f"Rates fetched: AUD/USD={rate_aud}, USD/JPY={rate_yen}")

        price_aud = price_usd * rate_aud
        price_yen = price_usd * rate_yen

        return price_aud, price_yen
    except Exception as e:
        st.error(f"Error fetching currency rates: {e}")
        st.write(f"Currency rates could not be fetched.")
        return None, None

# Function to fetch total value and count from the summary table
# Function to fetch total value and count from the summary table
def fetch_total_value_and_count(soup):
    try:
        summary_table = soup.find('table', id='summary')
        if not summary_table:
            raise ValueError("Summary table not found.")

        value_elements = summary_table.find_all('td', class_='number js-value js-price')
        count_elements = summary_table.find_all('td', class_='number')

        if not value_elements or not count_elements:
            raise ValueError("Value or count elements not found in summary table.")

        total_value_usd = float(value_elements[0].text.strip().replace('$', '').replace(',', ''))
        card_count = int(count_elements[1].text.strip().replace(',', ''))
        return total_value_usd, card_count

    except Exception as e:
        st.error(f"Error fetching total value and count: {e}")
        st.write(f"Total value and count could not be fetched.")
        return None, None

# Function to display card information
# Function to fetch and display card information
def display_card_info(soup, rate_aud, rate_yen):
    cards = {}
    try:
        for card in soup.find_all('tr', class_='offer'):
            try:
                card_name = card.find('p', class_='title').find('a').text.strip()
                card_link = card.find('p', class_='title').find('a')['href']
                card_image_url = get_high_res_image(card_link)

                # Fetching grading and price
                grading = card.find('td', class_='includes').text.strip()
                price = card.find('td', class_='price').text.strip().replace('$', '').replace(',', '')

                # Convert prices to AUD and JPY
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

    for card_name, card_data in cards.items():
        st.image(card_data['image'], width=300)
        st.markdown(f"**{card_name}**")
        for grading, price_aud, price_yen in card_data['gradings']:
            aud_display = f"${price_aud:.2f} AUD" if price_aud is not None else "N/A AUD"
            yen_display = f"¥{price_yen:.2f} JPY" if price_yen is not None else "N/A JPY"
            st.markdown(f"**{grading}:** {aud_display} | {yen_display}")
        st.write("---")

# Main function to run the app
def main():
    st.title("PokéDan")
    
    # Fetch and parse the collection page
    try:
        response = requests.get('https://www.example.com/your-collection-page')
        soup = BeautifulSoup(response.content, 'html.parser')
        st.write("Page fetched successfully.")
    except Exception as e:
        st.error(f"Error fetching the page: {e}")
        return
    
    # Fetch currency rates
    rate_aud, rate_yen = fetch_and_convert_currency(1.0)

    # Fetch total collection value and count
    total_value_usd, card_count = fetch_total_value_and_count(soup)
    if total_value_usd is not None:
        total_value_aud, total_value_yen = fetch_and_convert_currency(total_value_usd)
        st.markdown(f"<h3 style='text-align: center;'>Total Collection Value: ${total_value_aud:.2f} AUD | ¥{total_value_yen:.2f} JPY</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: lightgray;'>Total cards: {card_count}</p>", unsafe_allow_html=True)
        st.markdown(f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.markdown(f"<h3 style='text-align: center;'>Total Collection Value: Not available</h3>", unsafe_allow_html=True)

    # Display card info
    st.markdown("---")
    display_card_info(soup, rate_aud, rate_yen)
    st.markdown(f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
