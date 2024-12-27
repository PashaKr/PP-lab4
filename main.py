import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Токены
TELEGRAM_TOKEN = '7589269344:AAEUzX5hEIrbAhRzmHRCxd9BbRh2sVGyncA'
GENIUS_TOKEN = 'p-TsfUhykYaoW4Owag-bMdTRZpwaIiNUI2blBQLAwmbarcFGlO9AxMx4C2Pg_Y__'


# Функция для поиска песни на Genius
def search_song(song_name: str) -> dict:
    base_url = "https://api.genius.com"
    headers = {"Authorization": f"Bearer {GENIUS_TOKEN}"}
    search_url = f"{base_url}/search"
    params = {"q": song_name}

    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception("Genius API недоступен")

    data = response.json()
    if not data['response']['hits']:
        return None

    song = data['response']['hits'][0]['result']
    song_id = song['id']
    song_info = {
        "title": song["title"],
        "artist": song["primary_artist"]["name"],
        "url": song["url"]
    }

    # Получаем подробности о песне через API
    song_details = get_song_details_via_api(song_id)
    song_info.update(song_details)

    return song_info


# Функция для получения деталей песни через API
def get_song_details_via_api(song_id: int) -> dict:
    base_url = f"https://api.genius.com/songs/{song_id}"
    headers = {"Authorization": f"Bearer {GENIUS_TOKEN}"}

    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        raise Exception("Genius API недоступен")

    data = response.json()
    song_data = data['response']['song']

    return {
        "release_date": song_data.get("release_date", "Не указано")
    }


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь название песни, чтобы узнать информацию о ней."
    )


# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    song_name = update.message.text
    try:
        # Поиск песни через Genius API
        song_info = search_song(song_name)
        if not song_info:
            await update.message.reply_text("Песня не найдена. Попробуйте другое название.")
            return

        # Формирование ответа с данными о песне
        reply = (
            f"🎵 Название: {song_info['title']}\n"
            f"🎤 Исполнитель: {song_info['artist']}\n"
            f"📅 Дата релиза: {song_info['release_date']}\n"
            f"🔗 Подробнее: {song_info['url']}"
        )
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")


# Основная функция
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()


if __name__ == "__main__":
    main()
