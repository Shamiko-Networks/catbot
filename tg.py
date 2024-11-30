import base64
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler
from config import ai_config
from utils import compress_image_in_place
import os
                
async def getTgFiletoB64(photo, bot):
    print(photo)
    file_id = photo.file_id
    size = photo.file_size
    if size > 2 * 1024 * 1024:  # 2MB = 2 * 1024 * 1024 字节
        return None
    new_file = await bot.get_file(photo)
    file_p = f"{file_id}.jpg"
    await new_file.download_to_drive(file_p)
    if compress_image_in_place(file_p):
        file_p = f"compress_{file_p}"
    with open(file_p, "rb") as f:
        base64_encoded = base64.b64encode(f.read())
        # 将编码后的数据转换为字符串
        base64_string = base64_encoded.decode('utf-8')
        if len(base64_string) < 3:
            return None
    # 删除文件
    os.remove(file_p)
    return base64_string

def get_name(update: Update):
    a_user_name = update.effective_user.username
    if not a_user_name:
        return f"{update.effective_user.first_name} {update.effective_user.last_name}"
    return a_user_name.strip()


def is_message_expired(update, expire_minutes=10) -> bool:
    """
    检查消息是否已过期
    
    Args:
        update: Telegram更新对象
        expire_minutes: 过期时间(分钟)
        
    Returns:
        bool: True表示消息已过期，False表示消息在有效期内
    """
    try:
        if expire_minutes<1:
            expire_minutes=ai_config.expire_minutes
        # 获取消息时间戳
        message_date = update.effective_message.date
        
        # 获取当前时间
        current_time = datetime.now(message_date.tzinfo)
        
        # 计算时间差(分钟)
        time_diff = (current_time - message_date).total_seconds() / 60
        
        # 判断是否超过过期时间
        return time_diff > expire_minutes
        
    except Exception as e:
        print(f"检查消息时间出错: {str(e)}")
        return True  # 发生错误时当作过期处理