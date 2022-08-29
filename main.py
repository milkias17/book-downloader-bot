import os

import telebot
from dotenv import load_dotenv
from libgen_api import LibgenSearch
from telebot import types

import db

load_dotenv()

API_KEY = os.getenv("TG_API_KEY")
bot = telebot.TeleBot(API_KEY)
libgen = LibgenSearch()


def get_books(book_title):
    """
    Takes a book title and returns a dictionary containing info about the book
    """
    title_filters = {"Extension": "pdf"}
    results = libgen.search_title_filtered(book_title, title_filters, exact_match=True)

    # Workaround  for telegram not allowing url document sends of more than 20MB
    for book in results.copy():
        size = book["Size"].split()
        size_num = int(size[0])
        size_ext = size[1]
        if size_ext not in ["Mb", "Kb"]:
            results.remove(book)
        elif size_ext == "Mb" and size_num > 20:
            results.remove(book)

    return results


def get_keyboard_markup(results, chat_id):
    """
    Gives a InlineKeyboardMarkup object containing buttons for book downloads
    :param results: Dictonary containing info about wanted book
    :param chat_id: chat id of chat requesting book
    :return: InlineKeyboardMarkup object
    """
    keys = list()
    for index, book in enumerate(results):
        choice_text = f'{index + 1}.{book["Title"]}'
        data = f"{chat_id}|{index}"
        btn = types.InlineKeyboardButton(text=choice_text, callback_data=data)
        keys.append(btn)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*keys)
    return keyboard


def get_book_link(book):
    """
    Return a download link for book
    :param book: dictonary containing info about book
    :return str
    """
    book_link = libgen.resolve_download_links(book)
    return book_link["Cloudflare"]


@bot.callback_query_handler(func=lambda callback: True)
def callbacks(callback):
    """
    Sends the book to user after button click
    """
    chat_id = int(callback.data.split("|")[0])
    index = int(callback.data.split("|")[1])
    book_link = get_book_link(db.get_results(chat_id)[index])
    bot.send_document(callback.message.chat.id, book_link)


@bot.message_handler(commands=["download"])
def download(message):
    if len(message.text.split()) < 2:
        bot.send_message(message.chat.id, "Please enter the book name after /download")

    book_title = " ".join(message.text.split()[1:])
    try:
        books = get_books(book_title)
        if not books:
            bot.send_message(
                message.chat.id, "Could not find the book you just sent :("
            )
        else:
            if db.exists(message.chat.id):
                db.update_results(message.chat.id, str(books))
            else:
                db.insert_results(message.chat.id, str(books))
            keyboard = get_keyboard_markup(books, message.chat.id)
            bot.send_message(
                message.chat.id, "Choose your book:", reply_markup=keyboard
            )
    except IndexError:
        bot.send_message(
            message.chat.id,
            "I am really sorry but I'm having technical issues, please try again",
        )
    except Exception as e:
        print(e)


@bot.message_handler(content_types=["text"], regexp="^[^/]")
def download2(message):
    book_title = message.text
    try:
        books = get_books(book_title)
        if not books:
            bot.send_message(
                message.chat.id, "Could not find the book you just sent :("
            )
        else:
            if db.exists(message.chat.id):
                db.update_results(message.chat.id, str(books))
            else:
                db.insert_results(message.chat.id, str(books))

            keyboard = get_keyboard_markup(books, message.chat.id)
            bot.send_message(
                message.chat.id, "Choose your book:", reply_markup=keyboard
            )
    except IndexError:
        bot.send_message(
            message.chat.id,
            "I am really sorry but I'm having technical issues please try again",
        )
    except Exception as e:
        print(e)


@bot.message_handler(commands=["start"])
def welcome_user(message):
    welcome_msg = f"""Hello {message.chat.first_name}, I can help you download any book you want. Just send me the book name!\n
Commands:
/help if you need help on how to use this bot
/download [Book Name] to get the book you want"""
    bot.send_message(message.chat.id, welcome_msg)


@bot.message_handler(commands=["help"])
def help_message(message):
    msg = f"""Hello again {message.chat.first_name}, with my help you can download any book you want!
Just send me the title of the book and I'll send it to you.
/help if you need help on how to use this bot
/download [Book Name] to get the book you want
"""
    bot.send_message(message.chat.id, msg)


bot.polling()
