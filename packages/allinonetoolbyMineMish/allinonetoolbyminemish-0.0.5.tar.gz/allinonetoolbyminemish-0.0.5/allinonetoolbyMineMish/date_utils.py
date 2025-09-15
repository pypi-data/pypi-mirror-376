import datetime
import calendar

def get_current_date():
    """Возвращает текущую дату"""
    return datetime.date.today()

def get_current_time():
    """Возвращает текущее время"""
    return datetime.datetime.now().time()

def get_current_datetime():
    """Возвращает текущие дату и время"""
    return datetime.datetime.now()

def format_date(date, format_str="%Y-%m-%d"):
    """Форматирует дату в строку"""
    return date.strftime(format_str)

def parse_date(date_str, format_str="%Y-%m-%d"):
    """Парсит строку в дату"""
    return datetime.datetime.strptime(date_str, format_str)

def add_days_to_date(date, days):
    """Добавляет дни к дате"""
    return date + datetime.timedelta(days=days)

def days_between_dates(date1, date2):
    """Вычисляет количество дней между двумя датами"""
    return abs((date2 - date1).days)

def is_leap_year(year):
    """Проверяет, является ли год високосным"""
    return calendar.isleap(year)

def get_last_day_of_month(year, month):
    """Возвращает последний день месяца"""
    return calendar.monthrange(year, month)[1]