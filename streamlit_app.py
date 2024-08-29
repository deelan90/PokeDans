def display_card_info(soup, rate_aud, rate_yen):
    cards = {}

    for card in soup.find_all('tr', class_='offer'):
        # Check if card name exists
        card_name_tag = card.find('p', class_='title')
        if card_name_tag and card_name_tag.find('a'):
            card_name = card_name_tag.find('a').text.strip()
        else:
            st.warning("Card name tag not found, skipping entry.")
            continue

        card_link = card_name_tag.find('a')['href']
        card_image_url = get_high_res_image(card_link)
        grading = card.find('td', class_='includes').text.strip()
        price = card.find('span', class_='js-price').text.strip().replace('$', '').replace(',', '')

        # Store card data
        if card_name not in cards:
            cards[card_name] = {
                'link': card_link,
                'image_url': card_image_url,
                'gradings': {}
            }

        # Add grading and price
        cards[card_name]['gradings'][grading] = float(price)

    # Display cards
    for card_name, card_data in cards.items():
        st.markdown(f"### {card_name}")
        if card_data['image_url']:
            st.image(card_data['image_url'], use_column_width=True)
        for grading, price in card_data['gradings'].items():
            st.markdown(f"**{grading}:** ${price:.2f} USD")

    st.markdown(f"<p style='text-align: center; color: lightgray;'>Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)
