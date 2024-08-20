import os
import re
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
        'start_message': "Xush kelibsiz! Tilni tanlash bilan boshlaylik.",
        'language_selection_message': "Iltimos, tilni tanlang:",
        'country_selection_message': "Endi mamlakatingizni tanlang.",
        'main_menu_message': "Nimani qilishni xohlaysiz?",
        'hotel_search_option_message': "Eng qimmat yoki eng arzon mehmonxonalarni qidirmoqchimisiz?",
        'hotel_search_details_message': "Qaysi shaharni tanlaysiz?",
        'check_in_date_message': "Qachon kirishni xohlaysiz? (format(airaport kodi), 2024-08-15)",
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
    },
    'ru': {
        'start_message': "Добро пожаловать! Давайте начнем с выбора языка.",
        'language_selection_message': "Пожалуйста, выберите ваш язык:",
        'country_selection_message': "Теперь выберите вашу страну.",
        'main_menu_message': "Что бы вы хотели сделать?",
        'hotel_search_option_message': "Вы хотите искать самые дорогие или самые дешевые отели?",
        'hotel_search_details_message': "В каком городе вы хотите забронировать отель?",
        'check_in_date_message': "Когда вы хотите заехать? (формат(код аэропорта), 2024-08-15)",
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
    # List of countries or use an API to get countries
    countries = ["🇺🇿 Uzbekistan", "🇷🇺 Russia", "🇹🇯 Tadjikistan", "🇹🇲 Turkmenistan", "🇰🇿 Kazakhstan", "🇰🇬 Kyrgyzstan"]
    keyboard = [[InlineKeyboardButton(country, callback_data=f'country_{country}')] for country in countries]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['country_selection_message'], reply_markup=reply_markup)

async def handle_country_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    country = query.data.split('_')[1]
    context.user_data['country'] = country

    language = context.user_data.get('language', 'uz')
    await query.answer()
    # await context.bot.send_message(chat_id=query.message.chat.id, text=translations[language]['main_menu_message'])
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
    option = query.data.split('_')[1]
    context.user_data['hotel_search_option'] = option

    await query.answer()
    await context.bot.send_message(chat_id=query.message.chat.id, text=translations[language]['hotel_search_details_message'])
    context.user_data['state'] = 'getting_city'

async def get_hotel_search_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    text = update.message.text
    current_state = context.user_data.get('state')

    if current_state == 'getting_city':
        context.user_data['city'] = text
        await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['check_in_date_message'])
        context.user_data['state'] = 'getting_check_in_date'

    elif current_state == 'getting_check_in_date':
        context.user_data['check_in_date'] = text
        await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['nights_message'])
        context.user_data['state'] = 'getting_nights'

    elif current_state == 'getting_nights':
        context.user_data['nights'] = text
        await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['guests_message'])
        context.user_data['state'] = 'getting_guests'

    elif current_state == 'getting_guests':
        context.user_data['guests'] = text
        await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['searching_hotels_message'])

        try:
            response = amadeus.shopping.hotel_offers_search.get(
                cityCode=context.user_data['city'],
                checkInDate=context.user_data['check_in_date'],
                checkOutDate=(datetime.strptime(context.user_data['check_in_date'], "%Y-%m-%d") + timedelta(days=int(context.user_data['nights']))).strftime("%Y-%m-%d"),
                guests=int(context.user_data['guests']),
                sort=context.user_data['hotel_search_option']  # 'PRICE' for cheapest, 'PRICE_DESC' for most expensive
            )
            hotels = response.data[:5]  # Limit to 5 options

            if hotels:
                keyboard = []
                for i, hotel in enumerate(hotels):
                    hotel_info = f"{i + 1}. Hotel: {hotel['hotel']['name']}\n" \
                                 f"Price per night 💲: {hotel['offers'][0]['price']['total']} {hotel['offers'][0]['price']['currency']}\n" \
                                 f"Check-in 📅: {context.user_data['check_in_date']}\n" \
                                 f"Check-out 📅: {datetime.strptime(context.user_data['check_in_date'], '%Y-%m-%d') + timedelta(days=int(context.user_data['nights'])).strftime('%Y-%m-%d')}\n" \
                                 f"Rating ⭐: {hotel['hotel']['rating']}\n" \
                                 f"Address 🏠: {hotel['hotel']['address']['lines'][0]}, {hotel['hotel']['address']['cityName']}\n" \
                                 f"Description: {hotel['hotel']['description']}"
                    keyboard.append([InlineKeyboardButton(hotel_info, callback_data=f'hotel_{i}')])

                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Here are the top 5 hotel options:", reply_markup=reply_markup)
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['no_hotels_found_message'])

        except ResponseError as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {e}")

async def handle_hotel_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    query = update.callback_query
    hotel_index = int(query.data.split('_')[1]) 

    try:
        response = amadeus.shopping.hotel_offers_search.get(
            cityCode=context.user_data.get('city', ''),
            checkInDate=context.user_data.get('check_in_date', ''),
            checkOutDate=(datetime.strptime(context.user_data.get('check_in_date', ''), "%Y-%m-%d") + timedelta(days=int(context.user_data.get('nights', '0')))).strftime("%Y-%m-%d"),
            guests=int(context.user_data.get('guests', 1)),
            sort=context.user_data.get('hotel_search_option', 'PRICE')  # Default to cheapest
        )
        hotels = response.data
        selected_hotel = hotels[hotel_index]

        hotel_details = f"{translations[language]['selected_hotel_message']}:\n" \
                        f"{translations[language]['hotel_name_message']}: {selected_hotel['hotel']['name']}\n" \
                        f"{translations[language]['price_per_night_message']} 💲: {selected_hotel['offers'][0]['price']['total']} {selected_hotel['offers'][0]['price']['currency']}\n" \
                        f"{translations[language]['check_in_message']} 📅: {context.user_data['check_in_date']}\n" \
                        f"{translations[language]['check_out_message']} 📅: {(datetime.strptime(context.user_data['check_in_date'], '%Y-%m-%d') + timedelta(days=int(context.user_data['nights']))).strftime('%Y-%m-%d')}\n" \
                        f"{translations[language]['rating_message']} ⭐: {selected_hotel['hotel']['rating']}\n" \
                        f"{translations[language]['address_message']} 🏠: {selected_hotel['hotel']['address']['lines'][0]}, {selected_hotel['hotel']['address']['cityName']}\n" \
                        f"{translations[language]['description_message']}: {selected_hotel['hotel']['description']}\n\n" \
                        f"{translations[language]['contact_agent_prompt']}"

        keyboard = [
            [InlineKeyboardButton(translations[language]['leave_contact_message'], callback_data='leave_contact')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.answer()
        await context.bot.send_message(chat_id=query.message.chat.id, text=hotel_details, reply_markup=reply_markup)
        await context.bot.send_message(chat_id=query.message.chat.id, text=translations[language]['name_prompt_message'])

        context.user_data['hotel'] = selected_hotel
        context.user_data['state'] = 'getting_user_info'

    except ResponseError as e:
        await query.answer()
        await context.bot.send_message(chat_id=query.message.chat.id, text=f"Error: {e}")

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
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['flight_search_message'])
    context.user_data['state'] = 'getting_departure_city'

async def get_search_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = context.user_data.get('language', 'uz')
    text = update.message.text

    if context.user_data.get('state') == 'getting_departure_city':
        context.user_data['departure_city'] = text
        await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['arrival_city_message'])
        context.user_data['state'] = 'getting_arrival_city'
    
    elif context.user_data.get('state') == 'getting_arrival_city':
        context.user_data['arrival_city'] = text
        await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['departure_date_message'])
        context.user_data['state'] = 'getting_departure_date'
    
    elif context.user_data.get('state') == 'getting_departure_date':
        context.user_data['depart_date'] = text
        await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['searching_flights_message'])

        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=context.user_data['departure_city'],
                destinationLocationCode=context.user_data['arrival_city'],
                departureDate=context.user_data['depart_date'],
                adults=1
            )
            flights = response.data[:20]

            if flights:
                keyboard = []
                for i, flight in enumerate(flights):
                    flight_info = f"{i + 1}. {translations[language]['flight_airline_message']} 🛩: {flight['itineraries'][0]['segments'][0]['carrierCode']}\n" \
                                  f"{translations[language]['flight_price_message']} 💲: {flight['price']['total']} {flight['price']['currency']}\n" \
                                  f"{translations[language]['flight_departure_message']} 🛫: {flight['itineraries'][0]['segments'][0]['departure']['at']}\n" \
                                  f"{translations[language]['flight_arrival_message']} 🛬: {flight['itineraries'][0]['segments'][0]['arrival']['at']}"
                    keyboard.append([InlineKeyboardButton(flight_info, callback_data=f'flight_{i}')])

                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['flight_options_message'], reply_markup=reply_markup)
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=translations[language]['no_flights_found_message'])

        except ResponseError as e:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {e}")

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
    hotel_search_link = f"https://t.me/sogdianatravelbot"

    message = f"{translations[language]['share_links_message']}:\n\n" \
              f"🔍 **{translations[language]['flight_search_message']}**:({flight_search_link})\n" \

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_state = context.user_data.get('state', None)

    if current_state == 'getting_user_info':
        await get_user_info(update, context)
    elif current_state == 'getting_city':
        await get_hotel_search_details(update, context)
    elif current_state in ['getting_check_in_date', 'getting_nights', 'getting_guests']:
        await get_hotel_search_details(update, context)
    elif current_state in ['getting_departure_city', 'getting_arrival_city', 'getting_departure_date']:
        await get_search_details(update, context)
    elif current_state == 'getting_contact_info':
        await handle_user_contact_info(update, context)
    
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


# app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_search_details))
# app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_hotel_search_details))
# app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_info))