import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from database import Database
from fuzzywuzzy import fuzz

ANILIST_TOKEN = ""
TOKEN = ""


def add_anime(update, context):
    chat_id = update.effective_chat.id
    # Check if user is admin
    if chat_id != YOUR_ADMIN_ID:
        update.message.reply_text("You are not authorized to add animes.")
        return

    # Extract anime name and info link
    message_text = update.message.text.split("/")
    if len(message_text) < 3:
        update.message.reply_text("Invalid format. Use /Add Animename : infolink")
        return

    anime_name = message_text[1].strip()
    info_link = message_text[2].strip()

    # Add anime to database
    db = Database()
    db.add_anime(anime_name, info_link)
    update.message.reply_text(f"Anime '{anime_name}' added successfully!")

def get_close_matches(word, possibilities, n=10, cutoff=0.8):
    return [match for match, score in zip(possibilities, fuzz.ratio(word, possibilities)) if score >= cutoff]

def search_anime(update, context):
    anime_name = update.message.text.strip()

    # Create an Anilist client
    client = Client(access_token=ANILIST_TOKEN)

    try:
        # Search for anime on Anilist
        anime_data = client.search(anime_name, type='anime')
        anime_list = anime_data['data']['Page']['media']

        if anime_list:
            # Fuzzy match user input with Anilist results
            anime_titles = [anime['title']['english'] or anime['title']['romaji'] for anime in anime_list]
            close_matches = get_close_matches(anime_name, anime_titles)

            if len(close_matches) > 1:
                # Multiple matches, provide suggestions with pagination
                MAX_SUGGESTIONS_PER_PAGE = 5
                current_page = context.user_data.get('page', 1)
                start_index = (current_page - 1) * MAX_SUGGESTIONS_PER_PAGE
                end_index = min(start_index + MAX_SUGGESTIONS_PER_PAGE, len(close_matches))
                current_page_suggestions = close_matches[start_index:end_index]

                # Create keyboard with suggestions and navigation buttons
                keyboard = [[telegram.KeyboardButton(text=suggestion)] for suggestion in current_page_suggestions]
                if current_page > 1:
                    keyboard.append([telegram.KeyboardButton(text="Prev")])
                if end_index < len(close_matches):
                    keyboard.append([telegram.KeyboardButton(text="Next")])
                reply_markup = telegram.ReplyKeyboardMarkup(keyboard=keyboard, one_time_keyboard=True, resize_keyboard=True)

                # Send message with suggestions and pagination buttons
                suggestions_text = "\n".join(current_page_suggestions)
                reply_text = f"Your spelling might be wrong. Did you mean:\n{suggestions_text}"
                update.message.reply_text(reply_text, reply_markup=reply_markup)

            elif len(close_matches) == 1:
                # Single match, fetch info from database
                anime_name = close_matches[0]
                anime_info = db.get_anime(anime_name)  # Assuming db is accessible here
                if anime_info:
                    # Send anime information from database
                    update.message.reply_text(f"Title: {anime_info['title']}\nInfo: {anime_info['info_link']}")
                else:
                    # Anime found on Anilist but not in database
                    update.message.reply_text("Anime found on Anilist but not in database. Consider adding it.")
            else:
                # No matches found
                update.message.reply_text("No anime found.")
        else:
            # No results from Anilist
            update.message.reply_text("No anime found on Anilist.")

    except Exception as e:
        # Handle exceptions (e.g., API errors, no results)
        update.message.reply_text(f"An error occurred: {str(e)}")


def start(update, context):
    update.message.reply_text("I'm an anime info bot! Send me an anime name to get its info link.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_anime), filters=Filters.user(user_id=YOUR_ADMIN_ID))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command & ~('Full index' in text) & ~('Search button' in text) & ~('Request' in text), search_anime))
    # Add handlers for spelling correction and pagination

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

  
