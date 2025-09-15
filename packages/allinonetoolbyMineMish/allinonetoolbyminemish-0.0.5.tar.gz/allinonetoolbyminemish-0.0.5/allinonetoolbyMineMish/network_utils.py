import requests
import socket
import urllib.parse

def get_public_ip():
    """Возвращает публичный IP адрес"""
    response = requests.get('https://api.ipify.org')
    return response.text

def is_valid_url(url):
    """Проверяет, является ли строка валидным URL"""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def download_file(url, filename):
    """Скачивает файл по URL"""
    response = requests.get(url)
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename

def get_hostname():
    """Возвращает hostname текущего компьютера"""
    return socket.gethostname()

def check_internet_connection():
    """Проверяет подключение к интернету"""
    try:
        requests.get('https://www.google.com', timeout=5)
        return True
    except:
        return False

def get_headers(url):
    """Возвращает заголовки HTTP ответа"""
    response = requests.head(url)
    return response.headers

def is_port_open(host, port):
    """Проверяет, открыт ли порт"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0