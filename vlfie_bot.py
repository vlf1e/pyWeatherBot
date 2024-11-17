import telebot
import requests

from telebot.types import KeyboardButton, ReplyKeyboardMarkup

bot = telebot.TeleBot('id')

# Клавиатура для стартового меню
#Создание кнопок "Дать доступ к местоположению" и "Ввести название города"
auto_location_button = KeyboardButton("Дать доступ к местоположению", request_location=True) #request_location после нажатия кнопки запрашивает местоположение пользователя
set_location_button = KeyboardButton("Ввести название города")
#Создание клавиатуры resize_keyboard для масштабирования кнопок
start_kb = ReplyKeyboardMarkup(resize_keyboard=True)
#Добавление кнопок в клавиатуру
start_kb.add(auto_location_button)
start_kb.add(set_location_button)

#Клавиатура для показа погоды
#Создание кнопок "Узнать текущую погоду" и "Узнать погоду через 3 часа"
current_forecast_button = KeyboardButton("Узнать текущую погоду")
forecast_after_3hour = KeyboardButton("Узнать погоду через 3 часа")
back_button = KeyboardButton("Назад") # Кнопка "Назад"
#Создание клавиатуры
forecast_kb = ReplyKeyboardMarkup(resize_keyboard=True)
#Добавление кнопок в клавиатуру
forecast_kb.add(current_forecast_button)
forecast_kb.add(forecast_after_3hour)
forecast_kb.add(back_button)

longitude = 0.0 #Долгота
latitude = 0.0 #Ширина
message_ids = [] #Массив для id сообщений, чтобы потом их удалять

#Получение координат по имени города
def get_coords(message):
    res = requests.get('http://api.openweathermap.org/geo/1.0/direct', params={ #Отправляем запрос и преобразуем его в json формат
        'q': message.text, #город
        'lang': 'ru', #язык
        'appid': 'id' #id для доступа к api
    }).json()
    try:
        global longitude
        longitude = res[0]['lon']
        global latitude
        latitude = res[0]['lat']
        temp = bot.send_message(message.chat.id, 'Местоположение найдено!', reply_markup=forecast_kb)
        message_ids.append(temp.id)
    except IndexError:
        temp = bot.send_message(message.chat.id, 'Местоположение не найдено', reply_markup=start_kb)
        message_ids.append(temp.id)

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start_reply(message):
    bot.delete_message(message.chat.id, message.id) #Удаление присланного сообщения
    temp = bot.send_message(message.chat.id,
                     "Привет, я бот vlfie!\nЯ умею показывать погоду, но для начала дай мне доступ к своему местоположению.",
                     reply_markup=start_kb) #Отправка текстового сообщения и клавиатуры start_kb
    message_ids.append(temp.id)

# Обработка сообщения содержащего местоположение
@bot.message_handler(content_types=['location']) #"Ловит" сообщение с местоположением
def get_location(message):
    global message_ids
    message_ids.append(message.id) #добавляем ID сообщения в массив
    if len(message_ids) != 0: #если в массиве есть ID сообщений, то удаляем их
        bot.delete_messages(message.chat.id, message_ids)
        message_ids = []
    global longitude, latitude
    if message.location:
        # обрезаем до 2 цифр после точки
        longitude = str(message.location.longitude)[:5]
        latitude = str(message.location.latitude)[:5]
        temp = bot.send_message(message.chat.id, "Местоположение получено!", reply_markup=forecast_kb) #отправляем сообщение
        message_ids.append(temp.id) #Добавляем ID сообщения в массив для последующего удаления

# Обработка сообщения содержащего текст
@bot.message_handler(content_types=['text']) #"Ловит" сообщение с текстом
def get_forecast(message):
    global message_ids
    if len(message_ids) != 0:
        bot.delete_messages(message.chat.id, message_ids)
        message_ids = []
    bot.delete_message(message.chat.id, message.id)
    match message.text:
        case 'Дать доступ к местоположению':
            pass
        case 'Ввести название города':
            temp = bot.send_message(message.chat.id, 'Введите название города')
            message_ids.append(temp.id)
        case 'Узнать текущую погоду':
            send_current_weather(message)
        case 'Узнать погоду через 3 часа':
            send_3hour_forecast(message)
        case 'Назад':
            temp = bot.send_message(message.chat.id, 'Для отображения погоды необходим доступ к вашему местоположению', reply_markup=start_kb)
            message_ids.append(temp.id)
        case _:
            get_coords(message)

def send_current_weather(message):
    global latitude, longitude
    res = requests.get("http://api.openweathermap.org/data/2.5/find",
                       params={
                           'lon': longitude,
                           'lat': latitude,
                           'type': 'like',
                           'lang': 'ru',
                           'units': 'metric',
                           'APPID': 'a4cdfe7972c946e9b3b26c0571b79dca'
                       }
                       )
    aqi_res = requests.get("http://api.openweathermap.org/data/2.5/air_pollution",
                           params={
                               'lon': longitude,
                               'lat': latitude,
                               'lang': 'ru',
                               'APPID': 'a4cdfe7972c946e9b3b26c0571b79dca'
                           }
                           )
    if res.status_code == 200 and aqi_res.status_code == 200:
        data = res.json()
        aqi = aqi_res.json()
        air_quality = 'Не определено'
        if data['list']:
            weather = data['list'][0]
            match weather['weather'][0]['description']:
                case "солнечно":
                    temp = bot.send_message(message.chat.id, "☀")
                    message_ids.append(temp.id)
                case "облачно с прояснениями":
                    temp = bot.send_message(message.chat.id, "⛅")
                    message_ids.append(temp.id)
                case "переменная облачность":
                    temp = bot.send_message(message.chat.id, "⛅")
                    message_ids.append(temp.id)
                case "туман":
                    temp = bot.send_message(message.chat.id, "🌫")
                    message_ids.append(temp.id)
                case "облачно":
                    temp = bot.send_message(message.chat.id, "☁")
                    message_ids.append(temp.id)
                case "снег":
                    temp = bot.send_message(message.chat.id, "🌨")
                    message_ids.append(temp.id)
                case "дождь":
                    temp = bot.send_message(message.chat.id, "🌧")
                    message_ids.append(temp.id)
                case "пасмурно":
                    temp = bot.send_message(message.chat.id, "🌥")
                    message_ids.append(temp.id)
                case "небольшой дождь":
                    temp = bot.send_message(message.chat.id, "💧")
                    message_ids.append(temp.id)
                case "ливень":
                    temp = bot.send_message(message.chat.id, "☔️")
                    message_ids.append(temp.id)
                case "небольшой снег":
                    temp = bot.send_message(message.chat.id, "❄️")
                    message_ids.append(temp.id)
                case "ветренно":
                    temp = bot.send_message(message.chat.id, "💨")
                    message_ids.append(temp.id)
                case "дождь с прояснениями":
                    temp = bot.send_message(message.chat.id, "🌦")
                    message_ids.append(temp.id)
                case "Дождь с грозами":
                    temp = bot.send_message(message.chat.id, "⛈")
                    message_ids.append(temp.id)
                case "облачно с молниями":
                    temp = bot.send_message(message.chat.id, "🌩")
                    message_ids.append(temp.id)
                case "гроза":
                    temp = bot.send_message(message.chat.id, "⚡️")
                    message_ids.append(temp.id)
            temp = bot.send_message(message.chat.id, f"Сегодня: {weather['weather'][0]['description']}")
            message_ids.append(temp.id)
            temp = bot.send_message(message.chat.id, f"Температура: {weather['main']['temp']}°C")
            message_ids.append(temp.id)
            temp = bot.send_message(message.chat.id, f"Ощущается как: {weather['main']['feels_like']}°C")
            message_ids.append(temp.id)
            temp = bot.send_message(message.chat.id, f"Скорость ветра: {weather['wind']['speed']} м/с")
            message_ids.append(temp.id)
            match aqi['list'][0]['main']['aqi']:
                case 1:
                    air_quality = 'хорошее'
                case 2:
                    air_quality = 'удовлетворительное'
                case 3:
                    air_quality = 'умеренное'
                case 4:
                    air_quality = 'плохое'
                case 5:
                    air_quality = 'очень плохое'
            temp = bot.send_message(message.chat.id, f"Качество воздуха: {air_quality}", reply_markup=forecast_kb)
            message_ids.append(temp.id)
        else:
            temp = bot.send_message(message.chat.id, "Не удалось найти информацию о погоде.", reply_markup=forecast_kb)
            message_ids.append(temp.id)
    else:
        temp = bot.send_message(message.chat.id, f"Error: {res.status_code}; {res.text}", reply_markup=forecast_kb)
        message_ids.append(temp.id)


def send_3hour_forecast(message):
    res = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                       params={
                           'lon': longitude,
                           'lat': latitude,
                           'type': 'like',
                           'lang': 'ru',
                           'units': 'metric',
                           'APPID': 'a4cdfe7972c946e9b3b26c0571b79dca'
                       }
                       )
    aqi_res = requests.get("http://api.openweathermap.org/data/2.5/air_pollution",
                           params={
                               'lon': longitude,
                               'lat': latitude,
                               'lang': 'ru',
                               'APPID': 'a4cdfe7972c946e9b3b26c0571b79dca'
                           }
                           )
    if res.status_code == 200:
        data = res.json()
        aqi = aqi_res.json()
        i = 0
        weather = data['list'][0]
        for forecast in data['list']:
            if i == 1:
                temp = bot.send_message(message.chat.id, 'Погода через 3 часа')
                message_ids.append(temp.id)
                match forecast['weather'][0]['description']:
                    case "солнечно":
                        temp = bot.send_message(message.chat.id, "☀")
                        message_ids.append(temp.id)
                    case "облачно с прояснениями":
                        temp = bot.send_message(message.chat.id, "⛅")
                        message_ids.append(temp.id)
                    case "переменная облачность":
                        temp = bot.send_message(message.chat.id, "⛅")
                        message_ids.append(temp.id)
                    case "туман":
                        temp = bot.send_message(message.chat.id, "🌫")
                        message_ids.append(temp.id)
                    case "облачно":
                        temp = bot.send_message(message.chat.id, "☁")
                        message_ids.append(temp.id)
                    case "снег":
                        temp = bot.send_message(message.chat.id, "🌨")
                        message_ids.append(temp.id)
                    case "дождь":
                        temp = bot.send_message(message.chat.id, "🌧")
                        message_ids.append(temp.id)
                    case "пасмурно":
                        temp = bot.send_message(message.chat.id, "🌥")
                        message_ids.append(temp.id)
                    case "небольшой дождь":
                        temp = bot.send_message(message.chat.id, "💧")
                        message_ids.append(temp.id)
                    case "ливень":
                        temp = bot.send_message(message.chat.id, "☔️")
                        message_ids.append(temp.id)
                    case "небольшой снег":
                        temp = bot.send_message(message.chat.id, "❄️")
                        message_ids.append(temp.id)
                    case "ветренно":
                        temp = bot.send_message(message.chat.id, "💨")
                        message_ids.append(temp.id)
                    case "дождь с прояснениями":
                        temp = bot.send_message(message.chat.id, "🌦")
                        message_ids.append(temp.id)
                    case "Дождь с грозами":
                        temp = bot.send_message(message.chat.id, "⛈")
                        message_ids.append(temp.id)
                    case "облачно с молниями":
                        temp = bot.send_message(message.chat.id, "🌩")
                        message_ids.append(temp.id)
                    case "гроза":
                        temp = bot.send_message(message.chat.id, "⚡️")
                        message_ids.append(temp.id)
                temp = bot.send_message(message.chat.id, f"Будет: {weather['weather'][0]['description']}")
                message_ids.append(temp.id)
                temp = bot.send_message(message.chat.id, f"Температура: {weather['main']['temp']}°C")
                message_ids.append(temp.id)
                temp = bot.send_message(message.chat.id, f"Ощущается как: {weather['main']['feels_like']}°C")
                message_ids.append(temp.id)
                temp = bot.send_message(message.chat.id, f"Скорость ветра: {weather['wind']['speed']} м/с")
                message_ids.append(temp.id)
                match aqi['list'][0]['main']['aqi']:
                    case 1:
                        air_quality = 'хорошее'
                    case 2:
                        air_quality = 'удовлетворительное'
                    case 3:
                        air_quality = 'умеренное'
                    case 4:
                        air_quality = 'плохое'
                    case 5:
                        air_quality = 'очень плохое'
                temp = bot.send_message(message.chat.id, f"Качество воздуха: {air_quality}", reply_markup=forecast_kb)
                message_ids.append(temp.id)
            i += 1
    else:
        temp = bot.send_message(message.chat.id, f"Error: {res.status_code}; {res.text}")
        message_ids.append(temp.id)

bot.infinity_polling()
