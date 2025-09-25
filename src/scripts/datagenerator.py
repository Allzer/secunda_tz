import random
import uuid

def gen_uuid():
    return uuid.uuid4()

def gen_adres():
    result = ['Питербург, Малый Купаввенский пр, д.5', 'Саратов, 2-й Кабельный пр, д.37', 'Сызрань, Улица Разумовского, д.13']
    return random.choice(result)

def gen_phone_number():
    number_part = ''.join(random.choices('0123456789', k=10))
    return f"+7{number_part}"

def gen_latitude_longitude():
    #55°44′24.00″ 37°36′36.00"
    result = '{}°{}′{}.{}" {}°{}′{}.{}"'.format(
        random.randint(10,99), 
        random.randint(10,99),
        random.randint(10,99), 
        random.randint(10,99), 
        random.randint(10,99), 
        random.randint(10,99), 
        random.randint(10,99), 
        random.randint(10,99)
    )
    return result

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
