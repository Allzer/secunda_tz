import random
from typing import Optional
import uuid

def gen_uuid():
    return uuid.uuid4()

def gen_adres():
    result = ['Питербург, Малый Купаввенский пр, д.5', 'Саратов, 2-й Кабельный пр, д.37', 'Сызрань, Улица Разумовского, д.13']
    return random.choice(result)

def gen_phone_number():
    number_part = ''.join(random.choices('0123456789', k=10))
    return f"+7{number_part}"

def gen_latitude_longitude(fixed_index: Optional[int] = None) -> str:
    """
    Возвращает строку "lat,lon" (десятичные градусы).
    Использует хардкод-лист координат (примерные точки в России).
    Для стабильных тестов можно передать fixed_index.
    """
    positions = [
        "55.753933,37.620795",  # Точка 0
        "55.752023,37.617499",  # Точка 1
        "55.729625,37.603701",  # Точка 2
        "55.829622,37.637486",  # Точка 3
        "55.764865,37.607573",  # Точка 4
        "55.760102,37.618423",  # Точка 5
        "55.703295,37.530095",  # Точка 6
        "55.793939,37.701624",  # Точка 7
        "59.934280,30.335099",  # (пример — Санкт-Петербург) Точка 8
        "53.202778,50.140278",  # (пример — Самара) Точка 9
    ]

    if fixed_index is not None:
        idx = max(0, min(int(fixed_index), len(positions) - 1))
        return positions[idx]
    return random.choice(positions)

def gen_name():
    prefix = ['ООО', 'ОАО', 'ИП']
    name = ['Автозвук', 'Мясокомбинат', 'Магазин продуктов']

    result = '{} {}'.format(random.choice(prefix), random.choice(name))
    
    return result

def gen_activites():
    return {
            'Машины' : ['Колонки', 'Провода', 'Крепления'],
            'Еда': ['Убой скота', 'Получение молока', 'Разведение новых животных'],
            'Продукты' : ['Продажа продуктов', 'Продажа сигарет', 'Продажа алкоголя']
        }
