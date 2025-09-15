import re
import random
import string

def reverse_string(text):
    """Переворачивает строку"""
    return text[::-1]

def is_palindrome(text):
    """Проверяет, является ли строка палиндромом"""
    text = text.lower().replace(" ", "")
    return text == text[::-1]

def count_vowels(text):
    """Считает количество гласных в строке"""
    vowels = "aeiouаеёиоуыэюя"
    return sum(1 for char in text.lower() if char in vowels)

def generate_password(length=12):
    """Генерирует случайный пароль"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def slugify(text):
    """Преобразует текст в slug"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text

def capitalize_words(text):
    """Делает каждое слово с заглавной буквы"""
    return ' '.join(word.capitalize() for word in text.split())

def truncate_text(text, max_length, suffix="..."):
    """Обрезает текст до максимальной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def count_words(text):
    """Считает количество слов в тексте"""
    return len(text.split())

def remove_duplicates(text):
    """Удаляет повторяющиеся слова"""
    words = text.split()
    return ' '.join(sorted(set(words), key=words.index))

def text_to_leet(text):
    """Преобразует текст в leet speak"""
    leet_dict = {
        'a': '4', 'b': '8', 'e': '3', 'g': '6',
        'l': '1', 'o': '0', 's': '5', 't': '7'
    }
    return ''.join(leet_dict.get(char.lower(), char) for char in text)