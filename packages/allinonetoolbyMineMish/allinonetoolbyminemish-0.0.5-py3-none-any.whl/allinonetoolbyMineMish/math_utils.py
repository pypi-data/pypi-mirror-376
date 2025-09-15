import math
import random

def is_prime(n):
    """Проверяет, является ли число простым"""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def fibonacci(n):
    """Генерирует последовательность Фибоначчи"""
    a, b = 0, 1
    result = []
    for _ in range(n):
        result.append(a)
        a, b = b, a + b
    return result

def factorial(n):
    """Вычисляет факториал числа"""
    if n == 0:
        return 1
    return n * factorial(n - 1)

def degrees_to_radians(degrees):
    """Преобразует градусы в радианы"""
    return degrees * (math.pi / 180)

def radians_to_degrees(radians):
    """Преобразует радианы в градусы"""
    return radians * (180 / math.pi)

def calculate_distance(x1, y1, x2, y2):
    """Вычисляет расстояние между двумя точками"""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def random_in_range(min_val, max_val):
    """Генерирует случайное число в диапазоне"""
    return random.uniform(min_val, max_val)

def percentage(part, whole):
    """Вычисляет процент"""
    return (part / whole) * 100

def average(numbers):
    """Вычисляет среднее значение"""
    return sum(numbers) / len(numbers)

def median(numbers):
    """Вычисляет медиану"""
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_numbers[mid - 1] + sorted_numbers[mid]) / 2
    else:
        return sorted_numbers[mid]