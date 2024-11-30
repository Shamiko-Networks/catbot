
import hashlib
import json
import time
import requests
from config import ai_config
from utils import save_base64_image


async def improve_prompt(prompt):
    if not prompt:
        return None  # Indicate failure

    try:
        response = requests.post(
            ai_config.improve_prompt_endpoint,
            headers={'Content-Type': 'application/json'},
            json={"prompt": prompt},
            timeout=15
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        improved_prompt = data.get("response")  # Use .get() to handle potential missing key
        return improved_prompt

    except requests.exceptions.RequestException as e:
        return None
    except json.JSONDecodeError as e:
        return None


async def generate_image(prompt):
    if not prompt:
        print('prompt is empty')
        return None,prompt
    
    prompt = await improve_prompt(prompt)
    if not prompt:
        print('failed to improve prompt')
        return None,prompt
    
    print(f' Draw | {prompt}')

    try:
        response = requests.post(
            ai_config.image_gen_endpoint,
            headers={'Content-Type': 'application/json'},
            json={"model": '3', "prompt": prompt},
            timeout=15
        )
        response.raise_for_status()

        data = response.json()
        img_base64 = data.get("image")  # Use .get() for safety

        if img_base64:  # Check if 'image' key exists and has a value
            img_url = f'misc/images/{hashlib.md5(prompt.encode()+str(time.time()).encode()).hexdigest()}.png'
            save_base64_image(img_base64, img_url)
            return img_url,prompt
        else:
            return None,prompt

    except requests.exceptions.RequestException as e:
        return None,prompt
    except json.JSONDecodeError as e:
        return None,prompt

