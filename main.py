import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import json

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define your API details
API_URL = "http://ws.audioscrobbler.com/2.0/"
API_KEY = "c3bffda04ecb9d62f7008b0fb28fa1eb"


# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Welcome to the Music Info Bot! \n\n"
        "Commands:\n"
        "/search <song name> - Search for a song.\n"
        "/top <genre> - Get top songs by genre.\n"
        "/preferences - Save or show your preferences."
    )


# Method 1: Search for a song by name
async def search_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for a song by its name."""
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a song name to search.")
        return

    song_name = " ".join(context.args)
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
            if data['results']['trackmatches']['track']:
                song_info = data['results']['trackmatches']['track'][0]
                reply = (
                    f"Song: {song_info['name']}\n"
                    f"Artist: {song_info['artist']}\n"
                    f"Album: {song_info.get('album', 'N/A')}\n"
                )
            else:
                reply = "No results found for your query."
        else:
            reply = "Error: No results found."
    else:
        reply = "Error: Unable to connect to the music API."

    await update.message.reply_text(reply)


# Method 2: Get top songs by genre
async def top_songs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Retrieve top songs for a specific genre."""
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a genre to get top songs.")
        return

    genre = " ".join(context.args)
    params = {
        'method': 'tag.gettoptracks',
        'tag': genre,
        'api_key': API_KEY,
        'format': 'json'
    }

    response = requests.get(API_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'toptracks' in data['tracks']:
            reply = f"Top songs in the genre {genre}:\n"
            for song in data['tracks']['track'][:5]:  # Display top 5 songs
                reply += f"- {song['name']} by {song['artist']['name']}\n"
        else:
            reply = "No top songs found for the specified genre."
    else:
        reply = "Error: Unable to retrieve top songs."

    await update.message.reply_text(reply)


# Method 3: Save and display user preferences
async def preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save or display user preferences."""
    user_id = update.message.from_user.id

    if len(context.args) == 0:
        # Display saved preferences
        preferences = context.user_data.get("preferences", {})
        if preferences:
            reply = "Your saved preferences:\n" + json.dumps(preferences, indent=2)
        else:
            reply = "No preferences saved yet. Use /preferences <key=value> to save preferences."
    else:
        # Save new preferences
        for arg in context.args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                context.user_data.setdefault("preferences", {})[key] = value
        reply = "Preferences saved!"

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
    application.add_handler(CommandHandler("search", search_song))
    application.add_handler(CommandHandler("top", top_songs))
    application.add_handler(CommandHandler("preferences", preferences))

    # Log all errors
    application.add_error_handler(error_handler)

    # Run the bot
    application.run_polling()


if __name__ == "__main__":
    main()
