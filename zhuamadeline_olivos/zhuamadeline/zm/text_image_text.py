import asyncio
import math
import re
import uuid

from nonebot.adapters.onebot.v11 import MessageSegment
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageSequence

from .config import font_path, full_path, save_dir
from .function import open_data
from .pathshim import Path

# 字体设置
font_size = 24  # 基础字体大小
try:
    font = ImageFont.truetype(str(font_path), font_size)  # 加载字体
except Exception:  # 字体缺失时置空：图文渲染自动退化为纯文本发送
    # 请在 plugin/data/zhuamadeline/data/fonts/ 下补充 ZhanKu.ttf 以恢复图片消息
    font = None

# 画布参数
MAX_WIDTH = 800                          # 画布最大宽度（像素）
MAX_IMAGE_HEIGHT = 600                   # 图片最大高度（像素）
PADDING = 30                             # 四周留白（像素）
LINE_SPACING = 5                         # 行间距（像素）
CACHE_LIMIT = 40                         # 缓存文件保留数量
DEFAULT_BG_COLOR = (247, 219, 255, 255)  # 默认淡紫色

# 在文件顶部添加颜色亮度计算函数
def get_color_brightness(color):
    """计算颜色的亮度（0-255）"""
    r, g, b = color[0], color[1], color[2]
    return (0.299 * r + 0.587 * g + 0.114 * b)

def is_dark_color(color, threshold=128):
    """判断颜色是否为深色"""
    return get_color_brightness(color) < threshold

def get_user_bg_color(user_id: str):
    """从用户数据中获取背景颜色"""
    try:
        # 确保文件存在
        if not full_path.exists():
            return DEFAULT_BG_COLOR

        data = open_data(full_path)

        # 获取用户颜色，如果不存在则返回默认
        color_str = data.get(str(user_id), {}).get("bg_color")
        if not color_str:
            return DEFAULT_BG_COLOR

        # 转换颜色格式（存储格式为 "#RRGGBB" 或 "RRGGBB"）
        color_str = color_str.lstrip('#')
        if len(color_str) == 6:
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            return (r, g, b, 255)  # 添加透明度255
        else:
            return DEFAULT_BG_COLOR
    except Exception:
        return DEFAULT_BG_COLOR

def create_gradient_background(width, height, user_id=None):
    """创建带用户自定义颜色的渐变背景"""
    # 获取用户颜色
    if user_id:
        start_color = get_user_bg_color(user_id)
    else:
        start_color = DEFAULT_BG_COLOR

    # 根据起始颜色决定深色模式
    dark_mode = is_dark_color(start_color)

    bg = Image.new('RGBA', (width, height), (0, 0, 0, 255) if dark_mode else (255, 255, 255, 255))
    draw = ImageDraw.Draw(bg)

    center_x, center_y = width // 2, height // 2
    max_radius = math.sqrt(center_x**2 + center_y**2)

    # 渐变颜色配置（深色模式终点为纯黑，浅色模式为白色）
    end_color = (0, 0, 0, 255) if dark_mode else (255, 255, 255, 255)

    # 使用三次贝塞尔缓动函数控制渐变速度
    def cubic_bezier(t, p0, p1, p2, p3):
        """三次贝塞尔缓动函数"""
        u = 1 - t
        return u**3*p0 + 3*u**2*t*p1 + 3*u*t**2*p2 + t**3*p3

    steps = 256  # 增加采样点使过渡更平滑
    for i in range(steps, 0, -1):
        # 使用贝塞尔曲线控制渐变进度（参数可调整）
        t = i / steps
        progress = cubic_bezier(t, 0, 0.2, 0.8, 1.0)  # 自定义缓动曲线

        radius = int(max_radius * progress)

        # 颜色插值（使用HSL色彩空间会更平滑）
        r = int(start_color[0] + (end_color[0] - start_color[0]) * progress)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * progress)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * progress)

        # 绘制渐变圆环
        if radius > 0:  # 避免绘制半径为0的圆
            draw.ellipse(
                [(center_x - radius, center_y - radius),
                 (center_x + radius, center_y + radius)],
                fill=(r, g, b, 255),
                outline=None
            )

    # 应用精细的高斯模糊（半径减小但多次应用效果更好）
    for _ in range(3):
        bg = bg.filter(ImageFilter.GaussianBlur(radius=1))

    return bg

# 愚人节特供！
# def wrap_text(text, max_chars=20):
#     """
#     将文本按段落拆分，并按单词/数字块自动换行
#     - 连续的字母（如 "hello"）视为 1 个单元
#     - 连续的数字（如 "123"）视为 1 个单元
#     - 其他字符（标点、空格、换行）仍按 1 个字符处理
#     """
#     lines = []
#     paragraphs = text.split("\n")

#     for paragraph in paragraphs:
#         if not paragraph.strip():
#             lines.append("\n")  # 保留空行
#             continue

#         # 使用正则表达式分割单词和数字块
#         tokens = re.findall(r'([a-zA-Z]+|\d+|\s|[^\w\s])', paragraph)

#         current_line = []
#         current_length = 0

#         for token in tokens:
#             token_length = len(token)

#             # 如果当前行 + 新 token 不超过 max_chars，则加入当前行
#             if current_length + token_length <= max_chars:
#                 current_line.append(token)
#                 current_length += token_length
#             else:
#                 # 否则，换行
#                 if current_line:
#                     lines.append("".join(current_line))
#                 current_line = [token]
#                 current_length = token_length

#         # 添加最后一行
#         if current_line:
#             lines.append("".join(current_line))

#     return lines

def wrap_text(text, max_chars=20):
    """
    智能换行函数（支持中英文混合、特殊符号处理）
    
    参数：
    - text: 输入文本
    - max_chars: 每行最大字符单位数
    
    返回：
    - 按语义分块的文本行列表
    
    处理规则：
    1. 数学表达式（如1+2）视为1单元
    2. 英文单词（含下划线）视为1单元
    3. 单个中文字符视为1单元
    4. 未匹配到的字符也显示，每个算1单位
    """
    lines = []
    paragraphs = text.split("\n")

    # 改进后的正则表达式模式
    token_pattern = re.compile(
        r"($$\d+[\+\-\*/=]+\d+$$|"   # 数学表达式
        r"[a-zA-Z_]+(?:'[a-zA-Z_]+)*|"  # 英文单词（含下划线）
        r"\d+|"          # 连续数字
        r"[^\w\s\u4e00-\u9fff]|"  # 单个符号
        r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]|"  # 中文字符
        r"\s)"           # 空白字符
    )

    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("\n")  # 保留空行
            continue

        # 获取所有匹配项及其位置
        matches = []
        last_end = 0
        for match in token_pattern.finditer(paragraph):
            # 添加未匹配到的字符
            if match.start() > last_end:
                unmatched = paragraph[last_end:match.start()]
                matches.extend(list(unmatched))  # 将未匹配的字符拆分为单个字符
            matches.append(match.group())
            last_end = match.end()
        
        # 添加最后未匹配的部分
        if last_end < len(paragraph):
            unmatched = paragraph[last_end:]
            matches.extend(list(unmatched))

        current_line = []
        current_length = 0

        for token in matches:
            # 每个token视为1个字符单位
            token_length = 1

            if current_length + token_length <= max_chars:
                current_line.append(token)
                current_length += token_length
            else:
                if current_line:
                    lines.append("".join(current_line))
                current_line = [token]
                current_length = token_length

        if current_line:
            lines.append("".join(current_line))

    return lines

def draw_text(draw, lines, y, canvas_width, center=True, user_id=None):
    """
    在画布上绘制多行文本（自动处理溢出）
    
    参数：
    - draw: ImageDraw对象
    - lines: 文本行列表
    - y: 起始Y坐标
    - canvas_width: 画布可用宽度
    - center: 是否居中
    
    返回：
    - 绘制结束后的Y坐标
    """
    # 获取当前背景色判断深色模式
    if user_id:
        bg_color = get_user_bg_color(user_id)
    else:
        bg_color = DEFAULT_BG_COLOR
    dark_mode = is_dark_color(bg_color)

    for line in lines:
        if line == "\n":  # 处理空行
            y += font_size + LINE_SPACING
            continue

        # 获取文本实际尺寸
        bbox = draw.textbbox((0, 0), line, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # 非居中时的溢出处理
        if not center and w > canvas_width - 2 * PADDING:
            max_len = int(len(line) * (canvas_width - 2 * PADDING) / w)
            line = line[:max(max_len, 1)]
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]

        # 计算X坐标
        x = (canvas_width - w) // 2 if center else PADDING

        # 描边设置
        outline_width = 1
        text_color = (255, 255, 255, 255) if dark_mode else (0, 0, 0, 255)
        outline_color = (0, 0, 0, 255) if dark_mode else (255, 255, 255, 255)

        # 绘制描边
        for dx in [-outline_width, 0, outline_width]:
            for dy in [-outline_width, 0, outline_width]:
                if dx != 0 or dy != 0:
                    draw.text((x+dx, y+dy), line, font=font, fill=outline_color)

        # 绘制主文字
        draw.text((x, y), line, font=font, fill=text_color)
        y += h + LINE_SPACING

    return y


def calculate_content_size(draw, lines, image_size=None):
    """
    计算内容总尺寸（文本+图片）
    
    参数：
    - draw: 用于测量的ImageDraw对象
    - lines: 文本行列表
    - image_size: 图片尺寸（宽,高），可选
    
    返回：
    - (总宽度, 总高度)
    """
    max_width = 0
    total_height = 0

    # 测量文本尺寸
    for line in lines:
        if line == "\n":
            total_height += font_size + LINE_SPACING
            continue

        bbox = draw.textbbox((0, 0), line, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        max_width = max(max_width, w)
        total_height += h + LINE_SPACING

    # 加入图片尺寸
    if image_size:
        img_w, img_h = image_size
        max_width = max(max_width, img_w)
        total_height += img_h + 2 * font_size  # 图片前后间距

    return max_width, total_height

def generate_frame(text1, text2, base_image=None, center=True, max_chars=20, canvas_size=None, user_id=None):
    """生成带固定尺寸的单帧"""
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)

    lines1 = wrap_text(text1, max_chars) if text1 else []
    lines2 = wrap_text(text2, max_chars) if text2 else []

    img_size = None
    if base_image:
        max_img_width = min(MAX_WIDTH - 2 * PADDING, font_size * 20)
        orig_w, orig_h = base_image.size
        scale = min(MAX_IMAGE_HEIGHT / orig_h, max_img_width / orig_w, 1.0)
        img_size = (int(orig_w * scale), int(orig_h * scale))

    content_width, content_height = calculate_content_size(draw, lines1 + lines2, img_size)

    # 使用传入的固定尺寸或动态计算
    if canvas_size:
        canvas_width, canvas_height = canvas_size
    else:
        canvas_width = content_width + 2 * PADDING
        canvas_height = content_height + 2 * PADDING

    bg = create_gradient_background(canvas_width, canvas_height, user_id)
    canvas = Image.new('RGBA', (canvas_width, canvas_height))
    canvas.paste(bg, (0, 0), bg)

    content_layer = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(content_layer)
    y = PADDING

    y = draw_text(draw, lines1, y, canvas_width, center, user_id=user_id)

    if base_image and img_size:
        y += font_size
        resized_img = base_image.resize(img_size, Image.LANCZOS).convert('RGBA')
        img_layer = Image.new('RGBA', img_size, (0, 0, 0, 0))
        img_layer.paste(resized_img, (0, 0), resized_img)
        img_x = (canvas_width - img_size[0]) // 2 if center else PADDING
        content_layer.paste(img_layer, (img_x, y), img_layer)
        y += img_size[1] + font_size

    y = draw_text(draw, lines2, y, canvas_width, center, user_id=user_id)

    canvas = Image.alpha_composite(canvas, content_layer)
    return canvas

def clean_cache():
    """清理过期缓存文件"""
    files = sorted(save_dir.glob("send_image*"), key=lambda f: f.stat().st_mtime)
    for f in files[:-CACHE_LIMIT]:
        try:
            f.unlink()
        except:
            pass

async def generate_image_with_text(text1, image_path, text2, max_chars=20, center=True, user_id=None):
    """
    主生成函数（支持静态图/GIF）
    
    参数：
    - text1: 顶部文本
    - image_path: 图片路径（可选）
    - text2: 底部文本
    - max_chars: 换行字符数限制
    - center: 是否居中
    
    返回：
    - 生成的文件Path对象
    """
    # 参数检查
    if not text1 and not image_path and not text2:
        return None

    # 字体缺失时不渲染图片，调用方将自动回退为纯文本消息
    if font is None:
        return None

    image_path = str(image_path) if image_path else None
    is_gif = image_path and Path(image_path).exists() and image_path.lower().endswith(".gif")

    # 清理缓存（同步操作，但很快）
    clean_cache()  
    file_id = uuid.uuid4().hex[:8]

    try:
        if is_gif:
            # 将GIF处理放到线程池
            return await asyncio.to_thread(
                _process_gif_sync,
                text1, image_path, text2, max_chars, center, user_id, file_id
            )
        else:
            # 静态图片异步化
            return await asyncio.to_thread(
                _process_static_image_sync,
                text1, image_path, text2, max_chars, center, user_id, file_id
            )
    except Exception as e:
        print(f"图像生成失败: {str(e)}")
        return None

# def _process_gif_sync(text1, image_path, text2, max_chars, center, user_id, file_id):
#     """同步处理GIF的函数"""
#     gif = Image.open(image_path)
#     gif_frames = [frame.copy() for frame in ImageSequence.Iterator(gif)]


#     max_size = (0, 0)
#     for frame in gif_frames:
#         temp = generate_frame(text1, text2, frame.convert("RGBA"), center, max_chars, None, user_id)
#         max_size = (max(max_size[0], temp.width), max(max_size[1], temp.height))
        
#     processed_frames = []
#     durations = []

#     for frame in gif_frames:
#         result = generate_frame(text1, text2, frame.convert("RGBA"), 
#                               center, max_chars, max_size, user_id)
#         processed_frames.append(result.convert("RGB"))
#         durations.append(frame.info.get("duration", 100))
        
#     output_path = save_dir / f"send_image{file_id}.gif"
#     processed_frames[0].save(
#         output_path,
#         save_all=True,
#         append_images=processed_frames[1:],
#         duration=durations,
#         loop=0,
#         optimize=False
#     )
#     return output_path

def _process_gif_sync(text1, image_path, text2, max_chars, center, user_id, file_id):
    """同步处理GIF的函数（只取第一帧）"""
    gif = Image.open(image_path)
    
    # 只取第一帧
    first_frame = next(ImageSequence.Iterator(gif)).copy()
    
    # 处理静态图片
    result = generate_frame(text1, text2, first_frame.convert("RGBA"), 
                          center, max_chars, None, user_id)
    
    # 保存为PNG格式
    output_path = save_dir / f"send_image{file_id}.png"
    result.save(output_path)
    return output_path


def _process_static_image_sync(text1, image_path, text2, max_chars, center, user_id, file_id):
    """同步处理静态图片的函数"""
    image = Image.open(image_path).convert("RGBA") if image_path else None
    result = generate_frame(text1, text2, image, center, max_chars, None, user_id)
    output_path = save_dir / f"send_image{file_id}.png"
    result.save(output_path)
    return output_path


# 以下为消息发送相关函数

# 文本消息转图片的触发阈值（OlivOS 移植版调整）：
# 默认永不合成图片，仅由允许列表中的调用点显式传 render_image=True。
# 显式允许后，两个阈值满足其一才转图，可按需调整。
TEXT_TO_IMAGE_MIN_LINES = 13   # 超过该行数转图片
TEXT_TO_IMAGE_MIN_CHARS = 300  # 或超过该字符数转图片


def should_render_image(text, render_image=False) -> bool:
    """仅在调用方明确允许时判断文本是否需要合成图片"""
    if not render_image:
        return False
    try:
        s = str(text)
        return (s.count('\n') + 1 > TEXT_TO_IMAGE_MIN_LINES
                or len(s) > TEXT_TO_IMAGE_MIN_CHARS)
    except Exception:
        return False


async def send_image_or_text(
    user_id=None,
    handler=None,
    text="",
    at_sender=False,
    forward_text=None,
    max_chars=30,
    render_image=False,
):
    """发送图文消息的便捷函数（短文本直发，长文本合成图片）"""
    img = None
    if should_render_image(text, render_image=render_image):
        img = await generate_image_with_text(
            text1=text,
            image_path=None,
            text2=None,
            max_chars=max_chars,
            center=False,
            user_id=user_id
        )
    if img:
        message = MessageSegment.image(img) + (forward_text or "")
    else:
        message = (forward_text or "") + text
    await handler.finish(message, at_sender=at_sender)

async def not_finish_send_image_or_text(
    user_id=None,
    handler=None,
    text="",
    at_sender=False,
    forward_text=None,
    max_chars=30,
    render_image=False,
):
    """发送图文消息的便捷函数(非finish)（短文本直发，长文本合成图片）"""
    img = None
    if should_render_image(text, render_image=render_image):
        img = await generate_image_with_text(
            text1=text,
            image_path=None,
            text2=None,
            max_chars=max_chars,
            center=False,
            user_id=user_id
        )
    if img:
        message = MessageSegment.image(img) + (forward_text or "")
    else:
        message = (forward_text or "") + text
    await handler.send(message, at_sender=at_sender)

async def send_image_or_text_forward(
    user_id,
    handler,
    text,
    forward_text,
    bot,
    bot_id,
    group_id,
    max_chars=30,
    at_sender=False,
    render_image=False,
):
    """通过转发消息发送图文（短文本直发，长文本合成图片）"""
    if not should_render_image(text, render_image=render_image):
        # 短文本直接发送，不再合成图片
        await handler.finish(text, at_sender=at_sender)
        return
    img = await generate_image_with_text(
        text1=text,
        image_path=None,
        text2=None,
        max_chars=max_chars,
        center=False,
        user_id=user_id
    )
    if img:
        await handler.finish(MessageSegment.image(img) + forward_text, at_sender=at_sender)
    else:
        await handler.finish(text, at_sender=at_sender)

async def auto_send_message(text, bot, group_id, forward_text=None, max_chars=30, render_image=False):
    """自动发送消息到群组（短文本直发，长文本合成图片）"""
    img = None
    if should_render_image(text, render_image=render_image):
        img = await generate_image_with_text(
            text1=text,
            image_path=None,
            text2=None,
            max_chars=max_chars,
            center=False,
            user_id=None
        )
    if img:
        message = MessageSegment.image(img) + (forward_text or "")
    else:
        message = (forward_text or "") + text
    await bot.send_group_msg(group_id=group_id, message=message)
