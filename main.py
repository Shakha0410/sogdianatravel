import os
import re
import  requests
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, CallbackContext
from amadeus import Client, ResponseError
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

load_dotenv()

# Set up Telegram bot
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
app = ApplicationBuilder().token(TOKEN).build()

# Retrieve the API credentials
AMADEUS_API_KEY = os.getenv('AMADEUS_API_KEY')
AMADEUS_API_SECRET = os.getenv('AMADEUS_API_SECRET')

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
AGENT_EMAIL = os.getenv('AGENT_EMAIL')

# Initialize the Amadeus client with both credentials
amadeus = Client(client_id=AMADEUS_API_KEY, client_secret=AMADEUS_API_SECRET)

translations = {
    'uz': {
        
        'go_back_to_main_menu': 'Biz bilan bron qiling',
        'contact_agents_button': 'asasdasdasd',
        'invalid_city_message': 'Shahar nomi notogri.',
        'enter_year_message': "Iltimos, jo'nab ketish yilini kiriting (masalan, 2024):",
        'enter_month_message': "Iltimos, jo'nab ketish oyini kiriting (masalan, 08):",
        'enter_day_message': "Iltimos, jo'nab ketish kunini kiriting (masalan, 15):",
        'start_message': "Xush kelibsiz! Tilni tanlash bilan boshlaylik.",
        'contact_request_subject': 'Aloqa so\'rovi',
        'hotel_search_city_message': "Shaharni kiriting: Masalan Kodi(PAR) - Paris",
        'language_selection_message': "Iltimos, tilni tanlang:",
        'country_selection_message': "Endi mamlakatingizni tanlang.",
        'main_menu_message': "Nimani qilishni xohlaysiz?",
        'hotel_search_option_message': "Eng qimmat yoki eng arzon mehmonxonalarni qidirmoqchimisiz?",
        'hotel_search_details_message': "Qaysi shaharni tanlaysiz?",
        'check_in_date_message': "Qachon kirishni xohlaysiz? (format: 2024-08-15)",
        'nights_message': "Necha kechani qoldirishni xohlaysiz?",
        'guests_message': "Qancha odam qoladi?",
        'searching_hotels_message': "Mehmonxonalarni qidiryapmiz... 🔍",
        'searching_flights_message': "Parvozlarni qidirish ... 🔍",
        'no_hotels_found_message': "Mehmonxonalar topilmadi.",
        'contact_agents_message': "Mana, siz bog'lanishingiz mumkin bo'lgan agentlar:\n\n",
        'flight_search_message': "Qayerdan uchyapsiz? (format(airaport kodi), SKD) 🛫",
        'arrival_city_message': "Qayerga uchyapsiz? (format(airaport kodi), LOS) 🛬",
        'departure_date_message': "Qachon uchmoqchisiz? (format(airaport kodi), 2024-08-15) 🕔",
        'no_flights_found_message': "Reyslar topilmadi.",
        'share_links_message': "Ulashingiz mumkin bo'lgan havolalar:\n\n",
        'thank_you_message': "Rahmat! Ma'lumotlaringizni oldik va tez orada siz bilan bog'lanamiz.",
        'flight_airline_message': "Aviakompaniya",
        'flight_price_message': "Narx",
        'shareitwith': "Buni do'stlaringiz bilan baham ko'ring",
        'flight_departure_message': "Jo'nash vaqti",
        'flight_arrival_message': "Qabul qilish vaqti",
        'flight_options_message': "Mana, reyslar uchun variantlar:",
        'selected_flight_message': "Tanlangan reys",
        'flight_duration_message': "Davomiyligi",
        'flight_seats_message': "Mavjud joylar soni",
        'flight_amenities_message': "Imtiyozlar",
        'leave_contact_message': "Kontakt ma'lumotlarini qoldiring",
        'contact_agent_prompt': "Ushbu reys uchun buyurtma berish uchun agent bilan bog'laning.",
        'name_prompt_message': "Ismingizni kiriting:",
        'search_flights': "Parvozlarni qidirish",
        'search_hotels': "Mexmonxonalarni qidirish",
        'expensive_hotels': "Qimmat mehmonxonalar",
        'cheapest_hotels': "Arzon mehmonxonalar",
        'telegram_username_message': 'Iltimos, Telegram foydalanuvchi nomingizni kiriting.',
        'phone_number_message': 'Iltimos, telefon raqamingizni kiriting.',
        'thank_you_contact_message': 'Ma\'lumotlaringiz uchun rahmat!',
    },
    'ru': {
        'go_back_to_main_menu': 'Забронируйте у нас',
        'contact_agents_button': 'asasdasdasd',
        'invalid_city_message': 'Shahar nomi notogri.',
        'enter_year_message': "Пожалуйста, введите год вылета (например, 2024):",
        'enter_month_message': "Пожалуйста, введите месяц вылета (например, 08):",
        'enter_day_message': "Пожалуйста, введите день вылета (например, 15):",
        'start_message': "Добро пожаловать! Давайте начнем с выбора языка.",
        'contact_request_subject': 'Контактный запрос',
        'hotel_search_city_message': "Введите город:Например Коди(PAR) - Paris",
        'language_selection_message': "Пожалуйста, выберите ваш язык:",
        'country_selection_message': "Теперь выберите вашу страну.",
        'main_menu_message': "Что бы вы хотели сделать?",
        'hotel_search_option_message': "Вы хотите искать самые дорогие или самые дешевые отели?",
        'hotel_search_details_message': "В каком городе вы хотите забронировать отель?",
        'check_in_date_message': "Когда вы хотите заехать? (формат: 2024-08-15)",
        'nights_message': "На сколько ночей вы хотите остановиться?",
        'guests_message': "Сколько человек будет проживать?",
        'searching_hotels_message': "Ищем отели... 🔍",
        'searching_flights_message': "поиск рейсов... 🔍",
        'no_hotels_found_message': "Отелей не найдено.",
        'contact_agents_message': "Вот агенты, с которыми вы можете связаться:\n\n",
        'flight_search_message': "Откуда вы летите? (формат(код аэропорта), SKD) 🛫",
        'arrival_city_message': "Куда вы летите? (формат(код аэропорта), LOS) 🛬",
        'departure_date_message': "Когда вы хотите лететь? (формат(код аэропорта), 2024-08-15) 🕔",
        'no_flights_found_message': "Рейсов не найдено.",
        'shareitwith': "Поделитесь этим с друзьями",
        'share_links_message': "Ссылки для обмена:\n\n",
        'thank_you_message': "Спасибо! Мы получили ваши данные и свяжемся с вами в ближайшее время.",
        'flight_airline_message': "Авиакомпания",
        'flight_price_message': "Цена",
        'flight_departure_message': "Время отправления",
        'flight_arrival_message': "Время прибытия",
        'flight_options_message': "Вот варианты перелета:",
        'selected_flight_message': "Выбранный рейс",
        'flight_duration_message': "Продолжительность",
        'flight_seats_message': "Количество доступных мест",
        'flight_amenities_message': "Удобства",
        'leave_contact_message': "Оставить контактные данные",
        'contact_agent_prompt': "Чтобы забронировать этот рейс, свяжитесь с агентом.",
        'name_prompt_message': "Пожалуйста, укажите свое имя:",
        'search_flights':"Поиск рейсов",
        'search_hotels': "Поиск отелей",
        'expensive_hotels': "Дорогие отели",
        'cheapest_hotels': "Дешевые отели",
        'telegram_username_message': 'Пожалуйста, введите свое имя пользователя Telegram.',
        'phone_number_message': 'Пожалуйста, введите свой номер телефона.',
        'thank_you_contact_message': 'Спасибо за вашу информацию!',
    }
}

# Define bot commands
async def start(update: Update, context: CallbackContext):
    language = context.user_data.get('language', 'uz')  # Default to 'uz'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['start_message'])
    await show_language_selection(update, context)
    
async def show_language_selection(update: Update, context: CallbackContext):
    language = context.user_data.get('language', 'uz')  # Default to 'uz'
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data='lang_uz')],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['language_selection_message'], reply_markup=reply_markup)
    
async def handle_language_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    language = query.data.split('_')[1]
    context.user_data['language'] = language

    await query.answer()
    await context.bot.send_message(chat_id=query.message.chat.id, text=translations[language]['country_selection_message'])
    await show_country_selection(update, context)
    
async def show_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')  # Default to 'uz'
    
    # List of countries
    countries = ["🇺🇿 Uzbekistan", "🇷🇺 Russia", "🇹🇯 Tajikistan", "🇹🇲 Turkmenistan", "🇰🇿 Kazakhstan", "🇰🇬 Kyrgyzstan"]
    
    # Create a keyboard with country buttons
    keyboard = [[KeyboardButton(country)] for country in countries]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    # Send message with custom keyboard
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=translations[language]['country_selection_message'],
        reply_markup=reply_markup
    )

async def handle_country_selection(update: Update, context: CallbackContext):
    # Get the user's selected country
    country = update.message.text

    # Store the selected country in user data
    context.user_data['country'] = country

    # Optionally set the state if you use a state management system
    context.user_data['state'] = 'main_menu'

    # Show the main menu
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    keyboard = [
        [InlineKeyboardButton("✈️ " + translations[language]['search_flights'], callback_data='search_flights')],
        [InlineKeyboardButton("🏨 " + translations[language]['search_hotels'], callback_data='search_hotels')],
        [InlineKeyboardButton("📞 " + translations[language]['contact_agents_message'], callback_data='contact_agents')],
        [InlineKeyboardButton("🔗 " + translations[language]['share_links_message'], callback_data='share_links')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['main_menu_message'], reply_markup=reply_markup)

async def search_hotels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💰 " + translations[language]['expensive_hotels'].split()[0], callback_data='hotel_expensive')],
        [InlineKeyboardButton("💵 " + translations[language]['cheapest_hotels'].split()[0], callback_data='hotel_cheap')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['hotel_search_option_message'], reply_markup=reply_markup)

async def handle_hotel_search_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=query.message.chat.id, text=translations[language]['hotel_search_city_message'])
    context.user_data['state'] = 'getting_city'

async def get_hotel_search_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    text = update.message.text
    current_state = context.user_data.get('state')

    if current_state != 'getting_city':
        # Ignore messages if not in 'getting_city' state
        return

    context.user_data['city'] = text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['searching_hotels_message'])

    try:
        # Step 1: Fetch the IATA city code using the city name
        location_response = amadeus.reference_data.locations.get(
            keyword=context.user_data['city'],
            subType='CITY'
        )

        if location_response.data:
            city_code = location_response.data[0]['iataCode']  # Get the first city's IATA code

            # Step 2: Use the IATA city code to search for hotels
            hotel_response = amadeus.reference_data.locations.hotels.by_city.get(cityCode=city_code)
            hotels = hotel_response.data[:10]

            if hotels:
                # Prepare a detailed message with hotel information
                hotel_info_list = []
                for i, hotel in enumerate(hotels):
                    hotel_name = hotel.get('name', 'N/A')
                    hotel_address = hotel.get('address', 'N/A')
                    hotel_rating = hotel.get('rating', 'N/A')
                    hotel_price = hotel.get('price', {}).get('total', 'N/A')  # Assuming 'price' is a dict with 'total'
                    hotel_picture = hotel.get('media', [{}])[0].get('url', 'No image available')  # Assuming 'media' is a list of dicts
                    hotel_info = f"Hotel {i+1}:\n" \
                                 f"Name: {hotel_name}\n" \
                                 f"Address: {hotel_address}\n" \
                                 f"Rating: {hotel_rating}\n" \
                                 f"Price: {hotel_price}\n" \
                                 f"Picture: {hotel_picture}\n"
                                 
                    hotel_info_list.append(hotel_info)

                # Combine all hotel info into one message
                hotel_message = "\n\n".join(hotel_info_list)
                
                
                main_menu_button = [[InlineKeyboardButton(translations[language]['go_back_to_main_menu'], callback_data='contact_agents')]]
                reply_markup = InlineKeyboardMarkup(main_menu_button)

                # Send the hotel information as a message
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Here are the top 10 hotels:\n\n{hotel_message}")

                # Save hotels for later use and update state
                context.user_data['hotels'] = hotels  # Save hotels for later use
                context.user_data['state'] = 'viewing_hotels'  # Update state to viewing hotels
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['no_hotels_found_message'])
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['invalid_city_message'])

    except ResponseError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error occurred: {e}")
        
async def handle_location_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    query = update.callback_query
    callback_data = query.data

    if callback_data == 'main_menu':
        await show_main_menu(update, context)
        return

    # Check if in the 'viewing_hotels' state
    if context.user_data.get('state') != 'viewing_hotels':
        await query.answer()
        await context.bot.send_message(chat_id=query.message.chat.id, text="Please select a hotel from the list.")
        return

    try:
        # Extract hotel index from callback data
        hotel_index = int(callback_data.split('_')[1])

        # Retrieve the selected hotel from saved context data
        hotels = context.user_data.get('hotels', [])
        if not hotels or hotel_index >= len(hotels):
            raise IndexError("Selected hotel index out of range.")

        selected_hotel = hotels[hotel_index]
        hotel_id = selected_hotel.get('hotelId')  # Ensure this key matches the API response

        if not hotel_id:
            raise ValueError("Hotel ID not found.")

        # Request detailed information about the selected hotel
        response = amadeus.shopping.hotel_offers_by_hotel.get(hotelId=hotel_id)
        hotel_details = response.data

        if not hotel_details:
            raise ValueError("No detailed information available for this hotel.")

        # Parse detailed information
        hotel_info = (
            f"{translations[language]['selected_hotel_message']}:\n"
            f"Hotel Name: {hotel_details['hotel']['name']}\n"
            f"Address: {hotel_details['hotel']['address']['lines'][0]}, {hotel_details['hotel']['address'].get('cityName', 'N/A')}\n"
            f"Country: {hotel_details['hotel']['address'].get('countryCode', 'N/A')}\n\n"
            f"Latitude: {hotel_details['hotel']['latitude']}\n"
            f"Longitude: {hotel_details['hotel']['longitude']}\n"
            f"Rating: {hotel_details.get('rating', 'N/A')}\n"
            f"Price: {hotel_details['offers'][0]['price']['total']} {hotel_details['offers'][0]['price']['currency']}\n"
        )

        # Add more details if available
        if 'description' in hotel_details['hotel']:
            hotel_info += f"Description: {hotel_details['hotel']['description']}\n"
        if 'amenities' in hotel_details['hotel']:
            hotel_info += f"Amenities: {', '.join(hotel_details['hotel']['amenities'])}\n"

        await query.answer()
        await context.bot.send_message(chat_id=query.message.chat.id, text=hotel_info)

    except IndexError as index_err:
        await query.answer()
        await context.bot.send_message(chat_id=query.message.chat.id, text="Sorry, there was an error retrieving the hotel details. Please try again.")
    except ResponseError as e:
        await query.answer()
        await context.bot.send_message(chat_id=query.message.chat.id, text=f"Error occurred: {e}")
    except ValueError as val_err:
        await query.answer()
        await context.bot.send_message(chat_id=query.message.chat.id, text=f"Error: {val_err}")

async def leave_contact_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=query.message.chat.id, text=translations[language]['name_prompt_message'])

async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    text = update.message.text

    if context.user_data.get('state') == 'getting_user_info':
        user_info = {
            'name': text,
            'flight': context.user_data.get('flight'),
            'hotel': context.user_data.get('hotel')
        }

        await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['thank_you_message'])

        send_email(user_info)

        context.user_data.clear()

def send_email(user_info):
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    from_email = Email(AGENT_EMAIL)
    to_email = To(user_info['name'])
    subject = "New Flight/Hotel Booking Request"
    content = Content(
        "text/plain",
        f"Name: {user_info['name']}\n\n"
        f"Flight Details: {user_info['flight']}\n\n"
        f"Hotel Details: {user_info['hotel']}"
    )
    mail = Mail(from_email, to_email, subject, content)

    try:
        response = sg.send(mail)
        print(f"Email sent with status code {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")
    
async def handle_contact_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    query = update.callback_query
    await query.answer()

    agents = [
        {"name": "Agent A", "username": "@agent_a"},
        {"name": "Agent B", "username": "@agent_b"},
        {"name": "Agent C", "username": "@agent_c"}
    ]
    
    message = translations[language]['contact_agents_message']
    for agent in agents:
        message += f"{agent['name']}: {agent['username']}\n"
    
    await context.bot.send_message(chat_id=query.message.chat.id, text=message)
    
    
async def search_flights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')

    # List of airports in Uzbekistan
    uzbekistan_airports = [
        {'code': 'TAS', 'name': 'Tashkent International Airport'},
        {'code': 'SKD', 'name': 'Samarkand International Airport'},
        {'code': 'BHK', 'name': 'Bukhara International Airport'},
        {'code': 'NMA', 'name': 'Namangan Airport'},
        {'code': 'FEG', 'name': 'Fergana Airport'},
        {'code': 'UGC', 'name': 'Urgench Airport'},
        {'code': 'TMJ', 'name': 'Termez Airport'},
        {'code': 'KSQ', 'name': 'Karshi Khanabad Airport'},
        {'code': 'AZN', 'name': 'Andizhan Airport'},
    ]

    # Create a custom keyboard with the airports
    keyboard = [[KeyboardButton(f"{airport['name']} ({airport['code']})")] for airport in uzbekistan_airports]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=translations[language]['flight_search_message'],
        reply_markup=reply_markup
    )
    context.user_data['state'] = 'getting_departure_city'


async def get_search_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    text = update.message.text

    if context.user_data.get('state') == 'getting_departure_city':
        # Extract the airport code from the user input
        departure_code = text.split('(')[-1].strip(')')
        context.user_data['departure_city'] = departure_code

        # List of popular destination airports
        popular_airports = [
            {'code': 'SVO', 'name': 'Sheremetyevo International Airport, Moscow, Russia'},
            {'code': 'LED', 'name': 'Pulkovo Airport, St. Petersburg, Russia'},
            {'code': 'ALA', 'name': 'Almaty International Airport, Kazakhstan'},
            {'code': 'NQZ', 'name': 'Nursultan Nazarbayev International Airport, Kazakhstan'},
            {'code': 'IST', 'name': 'Istanbul International Airport, Turkey'},
            {'code': 'AYT', 'name': 'Fraport TAV Antalya Airport, Turkey'},
            {'code': 'TBS', 'name': 'Tbilisi Airport, Georgia'},
            {'code': 'BUS', 'name': 'Batumi Airport, Georgia'},
            {'code': 'DXB', 'name': 'Dubai International Airport, UAE'},
            {'code': 'AUH', 'name': 'Zayed International Airport, Abu Dhabi, UAE'},
            {'code': 'GMP', 'name': 'Gimpo International Airport,  Seoul, South Korea'},
            {'code': 'KWJ', 'name': 'Gwangju Airport, South Korea '},
            {'code': 'BKK', 'name': 'Bangkok - Suvarnabhumi Airport, Thailand '},
            {'code': 'HKT', 'name': 'Phuket International Airport, Thailand'},
            {'code': 'PEK', 'name': 'Beijing Capital International Airport, China'},
            {'code': 'PVG', 'name': 'Shanghai Pudong International Airport, China'},
            {'code': 'HND', 'name': 'Tokyo International Airport, Tokyo, Japan'},
            {'code': 'ITM', 'name': 'Osaka International Airport, Osaka, Japan'},
            {'code': 'CDG', 'name': 'Charles de Gaulle Airport, Paris, France'},
            {'code': 'LBG', 'name': 'Paris-Le Bourget Airport, Paris, France'},
            {'code': 'LCY', 'name': 'London City Airport, England'},
            {'code': 'LHR', 'name': 'London Heathrow Airport, England'},
            {'code': 'LPL', 'name': 'Liverpool John Lennon Airport, England'},  
            {'code': 'SIN', 'name': 'Singapore Changi Airport'},
            {'code': 'SIN', 'name': 'Seletar Airport, Singapore'},
            {'code': 'MAD', 'name': 'Madrid Barajas Airport, Spain'},
            {'code': 'MAD', 'name': 'Josep Tarradellas Barcelona-El Prat Airport, Spain'},
            {'code': 'EWR', 'name': 'Newark Liberty International Airport, New York, USA'},
            {'code': 'JFK', 'name': 'John F. Kennedy International Airport, New York, USA'},
            {'code': 'FCO', 'name': 'Roma Fiumicino Airport, Italy'},
            {'code': 'MXP', 'name': 'Milan Malpensa Airport, Italy'},
            {'code': 'CAI', 'name': 'Cairo International Airport, Egypt'},
            {'code': 'YYZ', 'name': 'Toronto Pearson International Airport, Canada'},
            {'code': 'YVR', 'name': 'Vancouver International Airport, Canada'},
        ]

        # Create a custom keyboard with popular airports
        keyboard = [[KeyboardButton(f"{airport['name']} ({airport['code']})")] for airport in popular_airports]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=translations[language]['arrival_city_message'],
            reply_markup=reply_markup
        )
        context.user_data['state'] = 'getting_arrival_city'

    elif context.user_data.get('state') == 'getting_arrival_city':
        # Extract the airport code for the destination city
        arrival_code = text.split('(')[-1].strip(')')
        context.user_data['arrival_city'] = arrival_code

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=translations[language]['enter_year_message']
        )
        context.user_data['state'] = 'getting_year'

    elif context.user_data.get('state') == 'getting_year':
        context.user_data['depart_year'] = text
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=translations[language]['enter_month_message']
        )
        context.user_data['state'] = 'getting_month'

    elif context.user_data.get('state') == 'getting_month':
        context.user_data['depart_month'] = text
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=translations[language]['enter_day_message']
        )
        context.user_data['state'] = 'getting_day'

    elif context.user_data.get('state') == 'getting_day':
        context.user_data['depart_day'] = text

        # Construct the departure date and validate its format
        try:
            context.user_data['depart_date'] = f"{context.user_data['depart_year']}-{context.user_data['depart_month']}-{context.user_data['depart_day']}"
            datetime.strptime(context.user_data['depart_date'], "%Y-%m-%d")  # Validate the date format
        except ValueError:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=translations[language]['invalid_date_message']
            )
            return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=translations[language]['searching_flights_message']
        )

        # Log the parameters used for the API call
        logging.info(f"Searching flights with params: Departure: {context.user_data['departure_city']}, "
                     f"Arrival: {context.user_data['arrival_city']}, Date: {context.user_data['depart_date']}")

        try:
            # Make the Amadeus flight search API request
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=context.user_data['departure_city'],
                destinationLocationCode=context.user_data['arrival_city'],
                departureDate=context.user_data['depart_date'],
                adults=1
            )
            flights = response.data[:20]  # Limit results to top 20 flights

            if flights:
                flight_details = []
                for i, flight in enumerate(flights):
                    flight_info = (
                        f"{i + 1}. {translations[language]['flight_airline_message']} 🛩: "
                        f"{flight['itineraries'][0]['segments'][0]['carrierCode']}\n"
                        f"{translations[language]['flight_price_message']} 💲: "
                        f"{flight['price']['total']} {flight['price']['currency']}\n"
                        f"{translations[language]['flight_departure_message']} 🛫: "
                        f"{flight['itineraries'][0]['segments'][0]['departure']['at']}\n"
                        f"{translations[language]['flight_arrival_message']} 🛬: "
                        f"{flight['itineraries'][0]['segments'][0]['arrival']['at']}"
                    )
                    flight_details.append(flight_info)

                # Create a "Go back to main menu" button
                main_menu_button = [[InlineKeyboardButton(translations[language]['go_back_to_main_menu'], callback_data='contact_agents')]]
                reply_markup = InlineKeyboardMarkup(main_menu_button)

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="\n\n".join(flight_details),
                    reply_markup=reply_markup
                )
            else:
                main_menu_button = [[InlineKeyboardButton(translations[language]['go_back_to_main_menu'], callback_data='contact_agents')]]
                reply_markup = InlineKeyboardMarkup(main_menu_button)
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=translations[language]['no_flights_found_message']
                )

        except ResponseError as e:
            logging.error(f"Amadeus API Error: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=translations[language]['api_error_message']
            )

async def handle_flight_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    query = update.callback_query
    flight_index = int(query.data.split('_')[1])

    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=context.user_data.get('departure_city', ''),
            destinationLocationCode=context.user_data.get('arrival_city', ''),
            departureDate=context.user_data.get('depart_date', ''),
            adults=1
        )
        flights = response.data
        selected_flight = flights[flight_index]

        flight_details = f"{translations[language]['selected_flight_message']}:\n" \
                         f"{translations[language]['flight_airline_message']} 🛩: {selected_flight['itineraries'][0]['segments'][0]['carrierCode']}\n" \
                         f"{translations[language]['flight_price_message']} 💲: {selected_flight['price']['total']} {selected_flight['price']['currency']}\n" \
                         f"{translations[language]['flight_departure_message']} 🛫: {selected_flight['itineraries'][0]['segments'][0]['departure']['at']}\n" \
                         f"{translations[language]['flight_arrival_message']} 🛬: {selected_flight['itineraries'][0]['segments'][0]['arrival']['at']}\n" \
                         f"{translations[language]['flight_duration_message']} ⏱: {selected_flight['itineraries'][0]['duration']}\n" \
                         f"{translations[language]['flight_seats_message']} 💺: {selected_flight['numberOfBookableSeats']}\n" \
                         f"{translations[language]['flight_amenities_message']}:\n"

        keyboard = [
            [InlineKeyboardButton(translations[language]['leave_contact_message'], callback_data='leave_contact')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.answer()
        await context.bot.send_message(chat_id=query.message.chat.id, text=flight_details, reply_markup=reply_markup)

        context.user_data['flight'] = selected_flight
        context.user_data['state'] = 'getting_user_info'

    except ResponseError as e:
        await query.answer()
        await context.bot.send_message(chat_id=query.message.chat.id, text=f"Error: {e}")
        
async def handle_user_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    user_id = update.message.from_user.id
    state = context.user_data.get('state')

    if state == 'getting_contact_info':
        text = update.message.text.strip()

        if 'full_name' not in context.user_data:
            context.user_data['full_name'] = text
            await update.message.reply_text(translations[language]['telegram_username_message'])
        elif 'telegram_username' not in context.user_data:
            context.user_data['telegram_username'] = text
            await update.message.reply_text(translations[language]['phone_number_message'])
        elif 'phone_number' not in context.user_data:
            context.user_data['phone_number'] = text
            await update.message.reply_text(translations[language]['thank_you_contact_message'])

            sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
            from_email = Email('shakhzodumarov0410@gmail.com')
            to_email = To(AGENT_EMAIL)
            subject = translations[language]['contact_request_subject']
            content = Content(
                'text/plain',
                (f"{translations[language]['user_contact_details_message']}:\n"
                 f"{translations[language]['full_name_message']}: {context.user_data['full_name']}\n"
                 f"{translations[language]['telegram_username_message']}: {context.user_data['telegram_username']}\n"
                 f"{translations[language]['phone_number_message']}: {context.user_data['phone_number']}")
            )

            mail = Mail(from_email, to_email, subject, content)

            try:
                response = sg.send(mail)
                print(f"Email sent with status code: {response.status_code}")
            except Exception as e:
                print(f"Failed to send email: {e}")

            context.user_data.pop('state', None)
            context.user_data.pop('full_name', None)
            context.user_data.pop('telegram_username', None)
            context.user_data.pop('phone_number', None)

# New handler for leaving contact details
async def handle_leave_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    query = update.callback_query
    await query.answer()

    await context.bot.send_message(chat_id=query.message.chat.id, text=translations[language]['name_prompt_message'])

    context.user_data['state'] = 'getting_contact_info'
            
async def share_search_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    query = update.callback_query
    await query.answer()

    flight_search_link = f"https://t.me/sogdianatravelbot"

    message = f"{translations[language]['share_links_message']}:\n\n" \
              f"🔍 **{translations[language]['shareitwith']}**:({flight_search_link})\n" \

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_state = context.user_data.get('state', None)

    if current_state == 'getting_user_info':
        await get_user_info(update, context)  
    elif current_state == 'getting_city':
        await get_hotel_search_details(update, context)
    elif current_state in ['getting_check_in_date', 'getting_nights', 'getting_guests']:
        await get_hotel_search_details(update, context)
    elif current_state in ['getting_departure_city', 'getting_arrival_city', 'getting_departure_date', 'getting_year', 'getting_month', 'getting_day']:
        await get_search_details(update, context)
    elif current_state == 'getting_contact_info':
        await handle_user_contact_info(update, context)
    else:
        await show_main_menu(update, context)
    
# Set up bot handlers
app.add_handler(CommandHandler('start', start))

app.add_handler(CallbackQueryHandler(search_flights, pattern='^search$'))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

app.add_handler(CallbackQueryHandler(handle_flight_selection, pattern='^flight_'))
app.add_handler(CallbackQueryHandler(search_flights, pattern='^search_flights$'))
app.add_handler(CallbackQueryHandler(handle_language_selection, pattern='^lang_'))
app.add_handler(CallbackQueryHandler(handle_country_selection, pattern='^country_'))
app.add_handler(CallbackQueryHandler(handle_contact_agents, pattern='^contact_agents$'))
app.add_handler(CallbackQueryHandler(share_search_links, pattern='^share_links$'))
app.add_handler(CallbackQueryHandler(handle_leave_contact, pattern='^leave_contact$'))

app.add_handler(CallbackQueryHandler(handle_hotel_search_option, pattern='^hotel_'))
app.add_handler(CallbackQueryHandler(search_hotels, pattern='^search_hotels$'))

# Start the bot
app.run_polling()
