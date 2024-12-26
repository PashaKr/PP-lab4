import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

API_URL = "http://ws.audioscrobbler.com/2.0/"
API_KEY = "c3bffda04ecb9d62f7008b0fb28fa1eb"

# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    keyboard = [
        [InlineKeyboardButton("Search", callback_data="search")],
        [InlineKeyboardButton("Charts", callback_data="charts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Welcome to the Music Info Bot! Choose an option:",
        reply_markup=reply_markup
    )

# Callback handler for button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    if query.data == "search":
        await query.edit_message_text(
            "Please enter the name of the song you want to search for."
        )
        context.user_data['awaiting_search'] = True
    elif query.data == "charts":
        await query.edit_message_text("Fetching top charts...")
        await fetch_top_charts(update, context)

# Fetch top charts from Last.fm
async def fetch_top_charts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Retrieve top 5 songs from Last.fm charts."""
    url = "https://www.last.fm/charts"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        tracks = soup.select('td.chartlist-name a.chartlist-name-link')
        artists = soup.select('td.chartlist-artist a')

        if tracks and artists:
            reply = "Top 5 Songs on Last.fm Charts:\n"
            for i in range(min(5, len(tracks))):
                song = tracks[i].text.strip()
                artist = artists[i].text.strip()
                reply += f"{i + 1}. {song} by {artist}\n"
        else:
            reply = "Could not retrieve chart data."
    else:
        reply = "Error: Unable to connect to Last.fm charts."

    await update.callback_query.edit_message_text(reply)

# Handle song search input
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user input for song search."""
    if context.user_data.get('awaiting_search'):
        context.user_data['awaiting_search'] = False
        song_name = update.message.text
        await search_song_by_name(update, context, song_name)

# Search for a song by name
async def search_song_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE, song_name: str) -> None:
    """Search for a song by its name."""
    params = {
        'method': 'track.search',
        'track': song_name,
        'api_key': API_KEY,
        'format': 'json'
    }

    response = requests.get(API_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'results' in data and 'trackmatches' in data['results']:
            tracks = data['results']['trackmatches']['track']
            if tracks:
                reply = f"Found {len(tracks)} result(s) for '{song_name}':\n"
                for idx, song_info in enumerate(tracks[:5]):  # Limit to top 5 results
                    album = song_info.get('album', 'N/A')
                    reply += (
                        f"{idx + 1}. Song: {song_info['name']}\n"
                        f"   Artist: {song_info['artist']}\n"
                        f"   Album: {album}\n\n"
                    )
            else:
                reply = f"No results found for '{song_name}'."
        else:
            reply = "Error: No results found."
    else:
        reply = "Error: Unable to connect to the music API."

    await update.message.reply_text(reply)

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update):
        await update.message.reply_text("An error occurred. Please try again later.")

# Main function to start the bot
def main() -> None:
    """Start the bot."""
    application = Application.builder().token("7589269344:AAEUzX5hEIrbAhRzmHRCxd9BbRh2sVGyncA").build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Log all errors
    application.add_error_handler(error_handler)

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
