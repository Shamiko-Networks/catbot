import hashlib
import json
import random
import re
import time
import traceback
import io
import requests
from draw import generate_image
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler
import openai
import base64
import os

from datetime import datetime
# import google.generativeai as genai
import prompt
import config
from utils import *
from chat import *
from tg import *
from config import ai_config

async def cat_math_chat(user_message, user_name,context=None, update=None, chat_id=None):
    # gemini-exp-1114
    if check_moderation(user_message):
        print("Moderation check failed")  
        return f"不要发这种奇怪的东西喵~",False
    rp_math = math_chat(user_message)
    user_message = f'"{user_name}"让你计算了"{user_message}",你的计算过程和结果是:"{rp_math}",请猫猫尽可能用自己的语气详细地复述一遍计算结果并说出你的感想'
    try:
        await context.bot.send_message(
            chat_id=chat_id,  # 替换为目标聊天ID
            text=rp_math
        )
    except Exception as e:
        print(f"发送失败: {e}")
    return build_chat(user_message, True, ai_config.long_chat_model)

async def cat_code_chat(user_message, user_name,context=None, update=None, chat_id=None):
    if check_moderation(user_message):
        print("Moderation check failed")  
        return f"不要发这种奇怪的东西喵~",False
    rp_code = code_chat(user_message)
    user_message = f'"{user_name}"让你编程了"{user_message}",你的编程结果是:"{rp_code}",请猫猫尽可能用自己的语气详细地复述一遍编程结果并说出你的感想'
    try:
        await context.bot.send_message(
            chat_id=chat_id,  # 替换为目标聊天ID
            text=rp_code
        )
    except Exception as e:
        print(f"发送失败: {e}")
    return build_chat(user_message, True, ai_config.long_chat_model)


async def cat_online_search_chat(user_message, user_name,context=None, update=None, chat_id=None):
    print("Online Mode")
    if check_moderation(user_message):
        print("Moderation check failed")  
        return f"不要发这种奇怪的东西喵~",False
    rp_online = online_search_chat(user_message)
    print(f'-------\nreq:{user_message}\nRp:{rp_online}\nmodel:onlineModel\n--------\n')
    user_message = f'"{user_name}"让你上网搜索了"{user_message}",搜索结果是:"{rp_online}",请猫猫尽可能用自己的语气详细地复述一遍搜索结果并说出你的感想'
    try:
        # 发送消息，指定 parse_mode 为 MarkdownV2
        await context.bot.send_message(
            chat_id=chat_id,  # 替换为目标聊天ID
            text=format_news_summary(rp_online),
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        print(f"发送失败: {e}")
    return build_chat(user_message, True ,ai_config.long_chat_model)

async def cat_draw_image_chat(user_message, user_name,context=None, update=None, chat_id=None):
    if check_moderation(user_message):
        print("Moderation check failed")    
        return f"不要发这种奇怪的东西喵~",False
    img,aft_prompt = await generate_image(user_message)
    if not img:
        return f"绘画失败了",False
    if context and update and chat_id:
        # 从本地打开图片文件
        try:
            with open(img, 'rb') as f:
                imgbyte = f.read()
            
            # Send the generated image to the Telegram chat
            await context.bot.send_photo(
                chat_id=chat_id, 
                reply_to_message_id=update.effective_message.id,
                photo=imgbyte
            )
        except Exception as e:
            print(e)
            return f"绘画失败了",False
    build_chat(f'{user_name}让你绘画了内容为"{aft_prompt}"的画,你完成了主人的任务,请你复述主人的绘画内容,并对内容作出评价', True, ai_config.long_chat_model)
   
async def cat_chat(user_message, is_one=False, need_strict=True, user_name=None,context=None,update=None,chat_id=None):
    
    if user_name is None:
        # user_name = "路人"
        return f"我还不知道你的名字喵，我不和陌生人对话喵~ \n(需要设置用户名)", False

    if not user_message or user_message == '':
        return f'{user_name},有什么事喵?', False
    
    if len(user_message) > 4096:
        return "无法理解喵", False
    
    if need_strict:
        chat_intention = check_chat(user_message)
    else:
        chat_intention = "NONE"

    if chat_intention == "BAN":
        rp, ok = build_chat(f"{user_name}对你说: {user_message}，但你很不喜欢他这么说话。",False,ai_config.no_restrict_model)
        return rp, False


    if chat_intention == "NONE" and len(user_message) < 6:
        user_message = f"{user_name}向你打招呼: {user_message}。请你假想一个你正在做的事情,并对打招呼做出直接的回应,不要重复他人向你打招呼的内容"

    if chat_intention == "MATH":
        print("Math Mode")
        return await cat_math_chat(user_message, user_name,context=context,update=update,chat_id=chat_id)
    
    if chat_intention == "CODE":
        print("Code Mode")
        return await cat_code_chat(user_message, user_name,context=context,update=update,chat_id=chat_id)

    if chat_intention == "ONLINE" or contains_any_substring(user_message, substrings1):
        print("Online Mode")
        return await cat_online_search_chat(user_message, user_name,context=context,update=update,chat_id=chat_id)
    
    if chat_intention == "DRAW":
        print("Draw Mode")
        return  await cat_draw_image_chat(user_message, user_name,context=context,update=update,chat_id=chat_id)
    
    if chat_intention == "NONE":
        print("Chat Mode")
        return build_chat(f"{user_name}对你说: {user_message}", is_one,ai_config.default_model)
    
    
    print(f'chat_intention: {chat_intention}')
    return "大脑宕机了喵~", False


async def catgirl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_message_expired(update):
        print("Message expired skipping")
        return
    # 检查命令后的内容，一次性聊天
    if not update.message.text:
        return
    parts = update.message.text.split()
    if len(parts) > 1:
        # 去掉第一个元素（命令部分），保留后面的内容
        messages = parts[1:]
        if len(messages) > 8:
            rpy, need_save =  build_chat(f"{get_name(update)}: {update.message.text}",False,ai_config.no_restrict_model)
            try:
                # 尝试回复消息
                await update.message.reply_text(rpy)
            except Exception as e:
                print(f"Unexpected error: {e}")
                traceback.print_exc()   
    try:
        await update.message.reply_text("有什么事情喵~，要和我开始说话，请回复这句话喵~")
    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text("大脑宕机了喵~")


user_chat_limit_dict = {}
user_last_chat_dict = {}

substrings1 = ["上网", "计算", "联网"]





def handle_limit(user_id):
    global user_chat_limit_dict
    global user_last_chat_dict
    time_now = time.time()
    # 180秒重置计数器
    if user_last_chat_dict.get(user_id, 0) + 180 < time_now:
        user_chat_limit_dict[user_id] = 0
    if user_chat_limit_dict.get(user_id, 0) > 2:
        return True
    return False


def log_limit(user_id):
    global user_chat_limit_dict
    global user_last_chat_dict
    user_chat_limit_dict[user_id] = user_chat_limit_dict.get(user_id, 0) + 1
    user_last_chat_dict[user_id] = time.time()

async def cat_auto_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_message_expired(update):
        print("Message expired skipping")
        return
    
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    chat_type = update.message.chat.type
    if chat_type == 'private':
        await context.bot.send_message(
            chat_id=chat_id, 
            reply_to_message_id=update.effective_message.id, 
            text="该功能仅在群组内可用"
        )
        return


    user_name = get_name(update)
    rpy = "喵~"
    
    if handle_limit(user_id):
        rpy = f"{user_name}，你太聒噪了喵~"
    
    print(f'{user_name}({user_id}):{user_chat_limit_dict.get(user_id, 0)}|{user_last_chat_dict.get(user_id, 0)}')
    if update.message.text:
        log_limit(user_id)
        rpy, need_save = await cat_chat(update.message.text, is_one=False, user_name=user_name,context=context,update=update,chat_id=chat_id)
        if need_save:
            log_history(update.message.text, rpy)
        try:
            # Try to reply to message if it exists, otherwise send new message
            if update.effective_message:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    reply_to_message_id=update.effective_message.id, 
                    text=rpy
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=rpy
                )
        except Exception as e:
            print(f"Unexpected error: {e}")
            traceback.print_exc()


async def cat_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_message_expired(update):
        print("Message expired skipping")
        return
    if update.message.photo:
        photo = update.message.photo[-1]
        img_data_b64 = await getTgFiletoB64(photo, context.bot)
        rpy = await img2chat(img_data_b64)
        if not rpy:
            rpy = "大脑宕机了喵~"
        await update.message.reply_text(text=rpy)
        return


async def cat_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.sticker:
        img_data_b64 = await getTgFiletoB64(update.message.sticker, context.bot)
        rpy = await img2chat(img_data_b64)
        if not rpy:
            rpy = "大脑宕机了喵~"
        await update.message.reply_text(text=rpy)
        return


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="我不懂这个喵~")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''响应start命令'''
    text = '对话时以她的名字\"猫猫\"开头即可对话，或者`/cat 你的内容`,在群组中需要变成`/cat@tako_cat_bot 你的内容`\n如:\n`猫猫,你喜欢小鱼干吗？`\nor \n/cat `你喜欢小鱼干吗？`'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='MarkdownV2')


if __name__ == '__main__':
    #检查当前目录下是否有images文件夹,没有则创建
    if not os.path.exists('images'):
        os.makedirs('images')

    init_openai()
    ai_config.print_config()
    load_history_from_file()

    
    start_handler = CommandHandler('start', start)
    cat_handler = CommandHandler('cat', catgirl)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    sticker_handler = MessageHandler(filters.Sticker.STATIC, cat_sticker)
    img_handler = MessageHandler(filters.PHOTO, cat_photo)
    filter_callchat = filters.Regex('^[^!@#$%^&*()_+\-=\[\]{\};:\'",.<>/?0-9].*$')
    catchat_handler = MessageHandler(filter_callchat, cat_auto_chat)

    application = ApplicationBuilder().token(ai_config.token).build()
    # 注册 handler
    application.add_handler(start_handler)
    application.add_handler(cat_handler)
    application.add_handler(unknown_handler)
    application.add_handler(sticker_handler)
    application.add_handler(img_handler)
    application.add_handler(catchat_handler)

    # run!
    application.run_polling()
