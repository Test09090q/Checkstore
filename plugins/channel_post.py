#(©)Codexbotz

import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from bot import Bot
from config import *
from helper_func import encode

@Bot.on_message(filters.private & filters.user(ADMINS) & ~filters.command(['start','users','broadcast','batch','genlink','stats', 'addpaid', 'removepaid', 'listpaid', 'myplan']))

async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("Please Wait...!", quote=True)
    try:
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("Something went Wrong..!")
        return

    # Generate base64-encoded ID
    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)

    # Generate website and bot links
    website_link = f"{WEBSITE_URL}?rohit_18={base64_string}" if WEBSITE_URL_MODE else None
    bot_link = f"https://t.me/{client.username}?start={base64_string}"

    # Shorten the bot link if enabled
    #shortzy = Shortzy(api_key=SHORTLINK_API_KEY, base_site=SHORTLINK_API_URL)
    #short_bot_link = bot_link
    #if USE_SHORTLINK:
        #short_bot_link = await shortzy.convert(bot_link)

    # Create inline keyboard
    buttons = []
    if WEBSITE_URL_MODE:
        buttons.append([InlineKeyboardButton("🔗 Website Link", url=website_link)])
    buttons.append([InlineKeyboardButton("🔁 Bot Link (Original)", url=bot_link)])
    #if USE_SHORTLINK:
        #buttons.append([InlineKeyboardButton("⚡️ Shortened Bot Link", url=short_bot_link)])

    reply_markup = InlineKeyboardMarkup(buttons)

    # Edit reply with all links
    message_text = "<b>Here are your links:</b>"
    #if WEBSITE_URL_MODE:
        #message_text += f"<b>Website:</b> {website_link}\n"
    #message_text += f"<b>Bot (Original):</b> {bot_link}\n"
    #if USE_SHORTLINK:
        #message_text += f"<b>Bot (Shortened):</b> {short_bot_link}"

    await reply_text.edit(message_text, reply_markup=reply_markup, disable_web_page_preview=True)

    # Optionally update the post's reply markup
    if not DISABLE_CHANNEL_BUTTON:
        await post_message.edit_reply_markup(reply_markup)


#async def channel_post(client: Client, message: Message):
    #reply_text = await message.reply_text("Please Wait...!", quote = True)
   # try:
       # post_message = await message.copy(chat_id = client.db_channel.id, disable_notification=True)
    #except FloodWait as e:
        #await asyncio.sleep(e.x)
        #post_message = await message.copy(chat_id = client.db_channel.id, disable_notification=True)
    #except Exception as e:
        #print(e)
        #await reply_text.edit_text("Something went Wrong..!")
       # return
    #converted_id = post_message.id * abs(client.db_channel.id)
    #string = f"get-{converted_id}"
   # base64_string = await encode(string)
    #link = f"https://t.me/{client.username}?start={base64_string}"

    #reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📫 ʏᴏᴜʀ ᴜʀʟ", url=f'https://telegram.me/share/url?url={link}')]])

    #await reply_text.edit(f"<b>Here is your link</b>\n\n{link}", reply_markup=reply_markup, disable_web_page_preview = True)

    #if not DISABLE_CHANNEL_BUTTON:
        #await post_message.edit_reply_markup(reply_markup)

@Bot.on_message(filters.channel & filters.incoming & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):

    if DISABLE_CHANNEL_BUTTON:
        return

    converted_id = message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📫 ʏᴏᴜʀ ᴜʀʟ​", url=f'https://telegram.me/share/url?url={link}')]])
    try:
        await message.edit_reply_markup(reply_markup)
    except Exception as e:
        print(e)
        pass
