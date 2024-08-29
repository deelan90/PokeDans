import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from forex_python.converter import CurrencyRates

# Function to fetch and convert currency
def fetch_and_convert_currency(usd_value):
    c = CurrencyRates()
    usd_value = float(usd_value.replace('$', '').replace(',', ''))
    aud_value = c.convert('USD', 'AUD', usd_value)
    jpy_value = c.convert('USD', 'JPY', usd_value)
    return aud_value, jpy_value

# Function to scrape card data
def scrape_card_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Get total collection value
    summary_table = soup.find('table', id='summary')
    total_value_usd = summary_table.find('td', class_='number js-value js-price').text.strip()
    aud_value, jpy_value = fetch_and_convert_currency(total_value_usd)
    
    # Get card details
    card_data = []
    cards = soup.select('.card')  # Adjust this to the correct class name
    for card in cards:
        title = card.select_one('.card-title').text.strip()
        img_url = card.select_one('.card-image img')['src']
        grading_info = card.select('.card-grading')  # Adjust this to the correct class name
        
        gradings = []
        for grade in grading_info:
            grade_name = grade.select_one('.grading-name').text.strip()
            grade_value = grade.select_one('.grading-value').text.strip()
            gradings.append(f"{grade_name}: {grade_value}")
        
        card_data.append({
            'title': title,
            'img_url': img_url,
            'gradings': ' | '.join(gradings)
        })

    return card_data, aud_value, jpy_value

# Streamlit app layout
def main():
    st.title('PokéDan')
    
    # Scrape data
    collection_url = st.text_input('Enter the link to your Pokémon card collection:')
    if collection_url:
        card_data, total_value_aud, total_value_jpy = scrape_card_data(collection_url)
        
        # Display total value
        st.markdown(f"<p style='color: lightgray; font-size: 18px;'>Total Collection Value: ¥{total_value_jpy:,.2f} | ${total_value_aud:,.2f} AUD</p>", unsafe_allow_html=True)
        
        # Display cards
        cols = st.columns(2)
        for idx, card in enumerate(card_data):
            with cols[idx % 2]:
                st.image(card['img_url'], use_column_width=True)
                st.markdown(f"**{card['title']}**")
                st.markdown(f"<p style='font-size: 14px;'>{card['gradings']}</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
