import random
import string
from PIL import Image, ImageDraw, ImageFont
import os


def generate_captcha(length=6, width=200, height=80):
    """
    Генерирует CAPTCHA изображение с случайным текстом
    """
    # Генерация случайного текста
    chars = string.ascii_letters + string.digits
    text = ''.join(random.choice(chars) for _ in range(length))

    # Создание изображения
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype('arial.ttf', 36)
    except:
        font = ImageFont.load_default()

    # Добавление шумов и искажений
    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    # Рисование текста
    draw.text((10, 20), text, font=font, fill=(0, 0, 0))

    return image, text


def verify_captcha(input_text, generated_text):
    """
    Проверяет введённый текст CAPTCHA
    """
    return input_text.lower() == generated_text.lower()