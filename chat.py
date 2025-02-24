
import json
import prompt
import openai
from utils import get_time
from config import ai_config
import os
import requests

chat_history=[]
reply_history=[]

def log_history(msg, rpy):
    chat_history.append(msg)
    reply_history.append(rpy)
    if len(chat_history) >  ai_config.chat_threshold:
        chat_history_compress()
    save_history_to_file()

def save_history_to_file():
    with open("chat_history.json", "w") as f:
        json.dump(chat_history, f)
    with open("reply_history.json", "w") as f:
        json.dump(reply_history, f)


def load_history_from_file():
    global chat_history
    global reply_history
    # 检查是否存在这些文件，如果没有则创建
    if not os.path.exists("chat_history.json"):
        with open("chat_history.json", "w") as f:
            json.dump([], f)
    if not os.path.exists("reply_history.json"):
        with open("reply_history.json", "w") as f:
            json.dump([], f)

    try:
        with open("chat_history.json", "r") as f:
            chat_history = json.load(f)
    except Exception as e:
        print(e)
        chat_history = []
    try:
        with open("reply_history.json", "r") as f:
            reply_history = json.load(f)
    except Exception as e:
        print(e)
        reply_history = []

def init_openai():
    # 设置OpenAI配置
    openai.api_key = ai_config.openai_key
    openai.base_url = ai_config.openai_base_url

def code_chat(user_message):
    msg_prompt = [
        {
            "role": "system",
            "content": prompt.coder_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    rp = start_chat(msg_prompt, 0.3, ai_config.code_model)
    print(f'-------\nreq:{user_message}\nRp:{rp}\nmodel:{ai_config.code_model}\n--------\n')
    return rp


def math_chat(user_message):
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
    rp = start_chat(msg_prompt, 0.2, ai_config.math_model, 8192,180)
    # if rp == "":
    #     return ""
    # msg_prompt2 = [
    #     {
    #         "role": "system",
    #         "content": prompt.rea2
    #     },
    #     {
    #         "role": "user",
    #         "content": rp
    #     }
    # ]
    # rp = start_chat(msg_prompt2, 0.2, ai_config.compress_model,512)
    # print(f'-------\nreq:{user_message}\nRp:{rp}\nmodel:{ai_config.math_model}\n--------\n')
    return rp


def online_search_chat(user_message):
    msg_prompt = [
        {
            "role": "system",
            "content": prompt.broswer_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    rp = start_chat(msg_prompt, 0.3, ai_config.online_search_model)
    print(f'-------\nreq:{user_message}\nRp:{rp}\nmodel:{ai_config.online_search_model}\n--------\n')
    return rp


def check_chat(user_message):
    msg_prompt = [
        {
            "role": "system",
            "content": prompt.mind_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    rp = start_chat(msg_prompt, 0.2, ai_config.check_model)
    print(f'-------\nreq:{user_message}\nRp:{rp}\nmodel:{ai_config.check_model}\n--------\n')
    return rp


def img_data_to_chat(base64_image):
    # base64图片到文字
    msg_prompt = [
        {
            "role": "system",
            "content": prompt.img2chat_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What’s in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ]
    rp = start_chat(msg_prompt, 0.5, ai_config.sight_model)
    # rp = start_chat(msg_prompt, 0.7, "gpt-4o")
    print(f'-------\nreq: IMGFILE \nRp:{rp}\nmodel:{ai_config.sight_model}\n--------\n')
    return rp





# def img_to_chat():


def chat_history_compress():
    global chat_history
    global reply_history
    if len(chat_history) == 0:
        return "没有对话记录喵~"
    history_prompt = []
    for i in range(len(chat_history)):
        # 第一条为上一次压缩记忆，移除
        if i == 0:
            continue
        history_prompt.append({
            "role": "user",
            "content": chat_history[i]
        })
        history_prompt.append({
            "role": "assistant",
            "content": reply_history[i]
        })

    msgc_prompt = [{
        "role": "system",
        "content": prompt.compress_prompt
    }, {
        "role": "user",
        "content": json.dumps(history_prompt)
    }]

    rp = start_chat(msgc_prompt, 0.4, ai_config.compress_model)
    print(f'-------\nreq: chat_history\nRp:{rp}\nmodel:{ai_config.compress_model}\n--------\n')
    if rp and rp != "":
        chat_history = [f"这是刚才与你的对话概要:{rp}"]
        reply_history = [f"好的主人,我记住了"]




async def img2chat(img_data_b64):
    if img_data_b64 is not None:
        rp = img_data_to_chat(img_data_b64)
        if rp == "sorry" or rp == "I apologize, but I am not able to describe the contents of this image as it appears to contain inappropriate and explicit content that I am not able to engage with. I must refrain from providing any details about this particular image.":
            return "不要发奇怪的东西喵~",None
        else:
            rpy, ok =  build_chat(
                f'你看到了一张图片,内容是:{rp}, 这是你真实看见的内容，请猫猫复述内容并你用中文说出感想, 如果这张图片中有文字，请原封不动地告诉我有哪些文字，不要做出翻译或者修改',
                False,
                ai_config.default_model)
            if not ok:
                return "大脑宕机了喵",None
            return rpy,rp
    else:
        return "图片获取失败喵~",None


def build_chat(user_message, is_one=False,rmodel=ai_config.default_model):
    print(get_time())
    msg_prompt = [
        {
            "role": "system",
            "content": get_time() + prompt.cat_girl_prompt
        }
    ]
    if not is_one:  # 如果不是单独对话，加入历史记录
        for i in range(len(chat_history)):
            msg_prompt.append({
                "role": "user",
                "content": chat_history[i]
            })
            msg_prompt.append({
                "role": "assistant",
                "content": reply_history[i]
            })
    msg_prompt.append({
        "role": "user",
        "content": user_message
    })

    rp = start_chat(msg_prompt, 0.4, rmodel)
    if not rp or rp == "":
       print(f'use fallback\n')
       rp = start_chat(msg_prompt, 0.7, ai_config.fallback_model)
 
    if not rp or rp == "":
        return "大脑宕机了喵~", False

    print(f'-------\nreq:{user_message}\nRp:{rp}\nmodel:{rmodel}\n--------\n')
    return rp, True





def start_chat(msg_prompt, temp, model,max_tokens=1024,timeout=90):
    try:
        # Create a Future to run the chat completion
        chat_completion = openai.chat.completions.create(
            messages=msg_prompt,
            temperature=temp, 
            model=model,
            timeout=timeout, # Set 60 second timeout
            max_tokens=max_tokens
        )
        # Get response
        rp = chat_completion.choices[0].message.content
        return rp
    except Exception as e:
        print(f"Chat completion failed or timed out: {e}")
        return ""
    


def check_moderation(text):

  
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ai_config.moderate_key}"
    }
    data = {
        "input": text
    }

    # Make the POST request
    try:
        response = requests.post(ai_config.moderate_url, headers=headers, data=json.dumps(data), timeout=15)
    except requests.Timeout:
        print("Moderation request timed out after 30 seconds")
        return False
    except requests.RequestException as e:
        print(f"Moderation request failed: {e}")
        return False

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")

    # Parse the response JSON
    response_json = response.json()

    # Return whether the input was flagged
    flagged = response_json["results"][0]["flagged"]
    return flagged