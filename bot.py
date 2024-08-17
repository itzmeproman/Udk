import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from database import Database
from fuzzywuzzy import fuzz


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

def handle_pagination(update, context):
    """Handles user interaction with pagination buttons."""

    query = update.callback_query
    query.answer()  # Acknowledge button press

    data = query.data.split(':')
    action = data[0]
    page = int(data[1]) if len(data) > 1 else 1

    chat_id = query.message.chat_id
    message_id = query.message.message_id

    db = Database()
    anime_name = context.user_data.get('anime_name', '')  # Get the original search term

    anime_names = [anime['name'] for anime in db.anime_collection.find()]
    close_matches = get_close_matches(anime_name, anime_names)

    MAX_SUGGESTIONS_PER_PAGE = 5

    if action == 'next':
        page += 1
    elif action == 'prev':
        page -= 1
    else:
        # Handle button press for a specific suggestion
        anime_name = data[1]
        # Perform search with the chosen anime name
        search_anime(update, context, db)  # Call search_anime with the selected name
        return

    start_index = (page - 1) * MAX_SUGGESTIONS_PER_PAGE
    end_index = start_index + MAX_SUGGESTIONS_PER_PAGE
    current_page_suggestions = close_matches[start_index:end_index]

    # Create keyboard with suggestions and next/prev buttons
    keyboard = [[telegram.KeyboardButton(text=suggestion)] for suggestion in current_page_suggestions]
    if page > 1:
        keyboard.append([telegram.KeyboardButton(text="Prev")])
    if end_index < len(close_matches):
        keyboard.append([telegram.KeyboardButton(text="Next")])
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)

    # Update the message with new suggestions
    update.callback_query.edit_message_text(
        text=f"Your spelling might be wrong. Did you mean:\n{'\n'.join(current_page_suggestions)}",
        reply_markup=reply_markup
    )
    

def search_anime(update, context, db):
    anime_name = update.message.text.strip()

    anime_names = [anime['name'] for anime in db.anime_collection.find()]
    close_matches = get_close_matches(anime_name, anime_names)

    if close_matches:
        MAX_SUGGESTIONS_PER_PAGE = 5  # Adjust as needed
        current_page = context.user_data.get('page', 1)  # Use context to store page number

        if len(close_matches) > MAX_SUGGESTIONS_PER_PAGE:
            # Pagination logic
            suggestions_text = "\n".join(close_matches[:MAX_SUGGESTIONS_PER_PAGE])
            reply_text = f"Your spelling might be wrong. Did you mean:\n{suggestions_text}\n"
            reply_text += "Press 'Next' for more suggestions or select an option above."

            # Create a ReplyKeyboardMarkup with buttons for suggestions and "Next"
            keyboard = [[telegram.KeyboardButton(text) for text in close_matches[:MAX_SUGGESTIONS_PER_PAGE]]]
            keyboard.append([telegram.KeyboardButton(text="Next")])
            reply_markup = telegram.ReplyKeyboardMarkup(keyboard=keyboard, one_time_keyboard=True, resize_keyboard=True)

            if current_page == 1:
                update.message.reply_text(reply_text, reply_markup=reply_markup)
            else:
                # Update message for subsequent pages
                update.message.edit_text(reply_text, reply_markup=reply_markup)
            context.user_data['page'] = current_page + 1  # Update page number

        else:
            # Show all suggestions if less than maximum per page
            anime_name = close_matches[0]  # Use the first suggestion

    # Handle user selection (if any)
    if update.callback_query:  # Check for callback query from button press
        chosen_anime_name = update.callback_query.data  # Get the button text
        context.user_data['chosen_anime'] = chosen_anime_name  # Store chosen anime name
        update.callback_query.answer()  # Acknowledge button press

    # Search for the anime (use chosen_anime_name if available)
    chosen_anime_name = context.user_data.get('chosen_anime', anime_name)
    anime = db.get_anime(chosen_anime_name)
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

  
