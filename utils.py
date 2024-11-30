import base64
import io
import json
from datetime import datetime
import os
from PIL import Image



def get_time():
    now = datetime.now()

    # 自定义输出格式
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    hhh = now.strftime("%H")
    mmm = now.strftime("%M")
    return f"\n今天是{year}年{month}月{day}日,现在是{hhh}点{mmm}分"  # 输出格式：YYYY年MM月DD日 (例如：2023年10月26日)


def format_news_summary(text):
    # 分割为行
    lines = text.split('\n')
    
    # 存储转换后的行
    formatted_lines = []
    
    for line in lines:
        # 检查是否为新闻行
        if line.startswith('> 📰'):
            # 提取标题和链接
            # 假设格式为: "> 📰 **[标题](链接)**"
            try:
                # 移除前缀和多余字符
                content = line.replace('> 📰', '').strip()
                # 提取标题 (在 [ 和 ] 之间)
                title = content[content.find('[')+1:content.find(']')]
                # 提取链接 (在 ( 和 ) 之间)
                link = content[content.find('(')+1:content.find(')')]
                
                # 构建新格式
                formatted_line = f"📰 {title} \n> {link}"
                formatted_lines.append(formatted_line)
            except:
                # 如果解析失败，保持原样
                formatted_lines.append(line)
        else:
            # 非新闻行保持不变
            continue
    texts = escape_markdown('\n'.join(formatted_lines))
    if len(texts) >3000:
        texts=texts[:3000]
    # 合并所有行
    return texts



def escape_markdown(text: str) -> str:
    """
    转义 Telegram MarkdownV2 格式中的特殊字符
    """
    # 需要转义的特殊字符
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    # 遍历所有特殊字符并添加转义符号
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def contains_any_substring(target_string, substrings):
    """
    检查目标字符串中是否包含任意一个子字符串。

    参数:
    target_string (str): 需要检查的目标字符串。
    substrings (list or set): 包含多个子字符串的列表或集合。

    返回:
    bool: 如果包含任意一个子字符串，返回True；否则返回False。
    """

    return any(sub in target_string for sub in substrings)

def save_base64_image(base64_str: str, save_path: str) -> bool:
    """
    将base64图片数据保存为本地文件
    
    Args:
        base64_str: base64编码的图片字符串
        save_path: 保存图片的路径
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 如果字符串包含base64前缀,需要去掉
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
            
        # 解码base64数据
        img_data = base64.b64decode(base64_str)
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # 写入文件
        with open(save_path, 'wb') as f:
            f.write(img_data)
            
        return True
        
    except Exception as e:
        print(f"保存图片失败: {str(e)}")
        return False
    


def compress_image_in_place(image_path):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            while width > 1280 or height > 1280:
                width //= 2
                height //= 2
                img = img.resize((width, height), Image.LANCZOS)
            img.save(f'compress_{image_path}')
            return True
    except Exception as e:
        print(e)
        return False
    
def compress_image(image_data, max_size=(1024, 1024), quality=85):
    # 从二进制数据创建Image对象
    image = Image.open(io.BytesIO(image_data))

    # 调整图像大小，保持纵横比
    image.thumbnail(max_size, Image.LANCZOS)

    # 创建一个字节流对象
    output = io.BytesIO()

    # 根据图像格式选择保存方法
    if image.format == 'JPEG':
        image.save(output, format='JPEG', quality=quality, optimize=True)
    elif image.format == 'PNG':
        image.save(output, format='PNG', optimize=True)
    else:
        # 如果不是JPEG或PNG，转换为JPEG
        image = image.convert('RGB')
        image.save(output, format='JPEG', quality=quality, optimize=True)

    # 获取压缩后的二进制数据
    compressed_data = output.getvalue()

    return compressed_data


def contains_keyword(string, keyword):
    return keyword in string
