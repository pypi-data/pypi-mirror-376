import os
import json
import csv

def read_file(filename):
    """Читает содержимое файла"""
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()

def write_file(filename, content):
    """Записывает содержимое в файл"""
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content)

def append_to_file(filename, content):
    """Добавляет содержимое в файл"""
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(content)

def file_exists(filename):
    """Проверяет существование файла"""
    return os.path.exists(filename)

def get_file_extension(filename):
    """Возвращает расширение файла"""
    return os.path.splitext(filename)[1]

def get_file_size(filename):
    """Возвращает размер файла в байтах"""
    return os.path.getsize(filename)

def read_json(filename):
    """Читает JSON файл"""
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_json(filename, data):
    """Записывает данные в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def read_csv(filename):
    """Читает CSV файл"""
    with open(filename, 'r', encoding='utf-8') as file:
        return list(csv.reader(file))

def write_csv(filename, data):
    """Записывает данные в CSV файл"""
    with open(filename, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)