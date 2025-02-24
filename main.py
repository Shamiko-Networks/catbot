import re
import time
import traceback
import io
from draw import generate_image
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler
import openai
import os
import asyncio

from datetime import datetime
import prompt
import config
from utils import *
from chat import *
from tg import *
from config import ai_config

async def cat_math_chat(user_message, user_name, context=None, update=None, chat_id=None):
    # gemini-exp-1114
    if check_moderation(user_message):
        print("Moderation check failed")  
        return f"不要发这种奇怪的东西喵~", False
    
    thinking_msg = await context.bot.send_message(chat_id, "🤓 猫猫正在思考中...")  # 发送思考消息
    
    msg_prompt = [
        {
            "role": "system",
            "content": prompt.reasoning_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    
    # openai 流对话
    rp_stream_math = openai.chat.completions.create(
        model=ai_config.math_model,
        messages=msg_prompt,
        temperature=0.6,
        stream=True

    )
    
    # 处理流式响应
    rp_math = ""
    cot_temp = ""
    
    async def update_message(text):
        try:       
            text = cot_chat(remove_think_tags(text))
            if text !='':
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=thinking_msg.message_id,
                    text=text
                )
        except Exception as e:
            print(f"发送失败: {e}")
    
    for chunk in rp_stream_math:
        #print(chunk)
        try:
            if chunk.choices[0].delta.content is not None:
                #print(chunk.choices[0].delta)
                if getattr(chunk.choices[0].delta, 'reasoning_content', '') != '':
                    if chunk.choices[0].delta.reasoning_content!= "":
                        cot_temp += chunk.choices[0].delta.reasoning_content
                else:
                    rp_math += chunk.choices[0].delta.content
                    cot_temp += chunk.choices[0].delta.content
                
                if len(cot_temp) > 2048:
                    await update_message(cot_temp)
                    cot_temp = ""  # Reset temporary content
        except Exception as e:
            print(f"发送失败3: {e}")
    
    # 最后发送完整结果
    print(f'-------\nreq:{user_message}\nRp:{rp_math}\nmodel:{ai_config.math_model}\n--------\n')
    rp_math = remove_think_tags(rp_math)
    
    # 发送最终结果
    await update_message(rp_math)
    
    if rp_math == "":
        return "想不出来喵~", False
    
    user_message = f'"{user_name}"让你计算和思考了"{user_message}",大致计算过程和结果是:"{rp_math}", 你已经说出了大致计算过程和结果，现在请猫猫尽可能用自己的语气告诉他结果，说出你的思考感想'
    
    
    return build_chat(user_message, True, ai_config.long_chat_model)


async def cat_code_chat(user_message, user_name,context=None, update=None, chat_id=None):
    if check_moderation(user_message):
        print("Moderation check failed")  
        return f"不要发这种奇怪的东西喵~",False
    rp_code = code_chat(user_message)
    user_message = f'"{user_name}"让你编程了"{user_message}",你的编程结果是:"{rp_code}",你已经说出了编程结果,现在请猫猫尽可能用自己的语气总结编程结果，并说出你的感想'
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
    search_ctx_msg = await context.bot.send_message(chat_id, "🔍 猫猫正在上网搜索中...") # 发送搜索消息
    rp_online = online_search_chat(user_message)
    print(f'-------\nreq:{user_message}\nRp:{rp_online}\nmodel:onlineModel\n--------\n')
    user_message = f'"{user_name}"让你上网搜索了"{user_message}",搜索结果是:"{rp_online}",请猫猫尽可能用自己的语气详细地复述一遍搜索结果并说出你的感想'
    try:
        # 发送消息，指定 parse_mode 为 MarkdownV2
        await context.bot.edit_message_text(
            chat_id=chat_id,  # 替换为目标聊天ID
            message_id=search_ctx_msg.message_id,
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
    draw_ctx_msg=await context.bot.send_message(chat_id, "🎨 猫猫正在思考绘画内容中...") # 发送绘画消息
    img,aft_prompt = await generate_image(user_message)
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=draw_ctx_msg.message_id,
        text=f"🎨 猫猫正在拿起画笔..."
    )

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
               # text=f"{aft_prompt}",
                reply_to_message_id=update.effective_message.id,
                photo=imgbyte
            )
        except Exception as e:
            print(e)
            return f"绘画失败了",False
    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=draw_ctx_msg.message_id
    )
    return build_chat(f'{user_name}让你绘画了内容为"{aft_prompt}"的画,你完成了主人的任务,请你复述主人的绘画内容,并对内容作出评价', True, ai_config.long_chat_model)

# 处理函数映射表
CHAT_HANDLERS = {
    "MATH": cat_math_chat,
    "CODE": cat_code_chat,
    "ONLINE": cat_online_search_chat,
    "DRAW": cat_draw_image_chat
}

async def delete_context_message(context, chat_id, message_id):
    """删除上下文消息"""
    try:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
    except Exception as e:
        print(f"发送失败: {e}")

async def handle_chat_response(handler_func, user_message, user_name, context, update, chat_id, message_id):
    """统一处理聊天响应"""
    try:
        print(f"{handler_func.__name__.replace('cat_', '').replace('_chat', '').title()} Mode")
        result = await handler_func(user_message, user_name, context=context, update=update, chat_id=chat_id)
        
        if result is None:
            return "抱歉,处理消息时出现错误", False
            
        # 确保返回值可以解包为两个值
        if not isinstance(result, tuple) or len(result) != 2:
            return f"处理函数返回了意外的结果: {result}", False
            
        response, ok = result
        await delete_context_message(context, chat_id, message_id)
        return response, ok
        
    except Exception as e:
        print(f"处理聊天响应时发生错误: {str(e)}")
        return f"处理消息时发生错误: {str(e)}", False

async def cat_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message:
        replied_text = update.message.reply_to_message.text

        # 这里直接调用已有的cat_chat函数让角色扮演机器人来“总结和评价”被回复的内容
        review_text, need_save = await cat_chat(
            f"根据这一段内容，发表一下你的感想：\n{replied_text}",
            is_one=False,
            user_name="Someone",
            context=context,
            update=update,
            chat_id=update.effective_chat.id
        )
        review_text = remove_think_tags(review_text)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.id,
            text=review_text
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.id,
            text="请在回复某条消息时使用 /review 命令。"
        )


async def cat_chat(user_message, is_one=False, need_strict=True, user_name=None,context=None,update=None,chat_id=None):
    
    if user_name is None:
        # user_name = "路人"
        return f"我还不知道你的名字喵，我不和陌生人对话喵~ \n(需要设置用户名)", False

    if not user_message or user_message == '':
        return f'{user_name},有什么事喵?', False
    
    if len(user_message) > 4096:
        return "无法理解喵", False
    global_chat_ctx_message = await context.bot.send_message(chat_id, "🍙 猫猫已收到消息...") # 发送思考消息
     
    if need_strict:
        chat_intention = check_chat(user_message)
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=global_chat_ctx_message.message_id,
            text="🍙 猫猫正在打字..."
        )
    else:
        chat_intention = "NONE"


    if chat_intention == "BAN":
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=global_chat_ctx_message.message_id,
            text="🍙 猫猫似乎不太高兴..."
        )
        rp, ok = build_chat(f"{user_name}对你说: {user_message}，但你很不喜欢他这么说话。",False,ai_config.no_restrict_model)
        return rp, False

    if chat_intention == "NONE":
        if len(user_message) < 5:
            user_message = f"{user_name}向你打招呼: {user_message}。请你随机假想一个你正在做的事情,并对打招呼做出直接的回应,不要重复他人向你打招呼的内容"
        else:
            user_message = f"{user_name}对你说: {user_message}"
    
     # 处理在线搜索的特殊情况
    if contains_any_substring(user_message, substrings1):
        chat_intention = "ONLINE"
        
    if contains_any_substring(user_message, substrings2):
        chat_intention = "MATH"
        
    # 获取对应的处理函数
    handler = CHAT_HANDLERS.get(chat_intention)
    
    if handler:
        return await handle_chat_response(
            handler, user_message, user_name, context, update, chat_id,global_chat_ctx_message.message_id
        )
    
    # 处理默认聊天模式
    if chat_intention == "NONE":
        print("Chat Mode")
        response, ok = build_chat(user_message, is_one, ai_config.default_model)
        await delete_context_message(context, chat_id, global_chat_ctx_message.message_id)
        return response, ok
    
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

substrings1 = ["上网",  "联网"]

substrings2 = ["数学计算",  "好好想一下" , "推理一下"]




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

import re

def remove_think_tags(text):
    """
    移除文本中所有被<think></think>标签包围的内容，包括标签本身。

    参数:
        text (str): 输入的原始文本。

    返回:
        str: 移除指定内容后的文本。
    """
    # 定义正则表达式模式，匹配<think>标签及其内部内容
    pattern = r'<think>.*?</think>'
    
    # 使用re.DOTALL标志，使.匹配包括换行符在内的所有字符
    cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL)
    
    cleaned_text = cleaned_text.replace("<think>", "")
    cleaned_text = cleaned_text.replace("</think>", "")
    return cleaned_text.strip()  # 去除首尾多余的空白字符




async def cat_auto_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_message_expired(update):
        print("Message expired skipping")
        return
    
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if not update.message.chat:
        return
    
    chat_type = update.message.chat.type
    # if chat_type == 'private':
    #     await context.bot.send_message(
    #         chat_id=chat_id, 
    #         reply_to_message_id=update.effective_message.id, 
    #         text="该功能仅在群组内可用"
    #     )
    #     return


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
            rpy = remove_think_tags(rpy)
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
        await img64torpy(img_data_b64,update,context)

async def img64torpy(img_data_b64,update: Update, context: ContextTypes.DEFAULT_TYPE):
        rpy,imgtext = await img2chat(img_data_b64)
        if rpy and imgtext:
            rpy = remove_think_tags(rpy)
            log_history(imgtext, rpy)
        await update.message.reply_text(text=rpy)
        return

    

async def cat_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.sticker:
        img_data_b64 = await getTgFiletoB64(update.message.sticker, context.bot)
        await img64torpy(img_data_b64,update,context)


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
    review_handler = CommandHandler('review', cat_review)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    sticker_handler = MessageHandler(filters.Sticker.STATIC, cat_sticker)
    img_handler = MessageHandler(filters.PHOTO, cat_photo)
    filter_callchat = filters.Regex('^[^/@]')
    catchat_handler = MessageHandler(filter_callchat, cat_auto_chat)

    application = ApplicationBuilder().token(ai_config.token).build()
    # 注册 handler
    application.add_handler(start_handler)
    application.add_handler(cat_handler)
    application.add_handler(review_handler)
    application.add_handler(unknown_handler)
    application.add_handler(sticker_handler)
    application.add_handler(img_handler)
    application.add_handler(catchat_handler)


    # run!
    application.run_polling()
