# импортируем библиотеки
from flask import Flask, request
import logging

import json

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}
# создаём словарь, диапазона чисел
sessiondiap = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    # Отправляем request.json и response в функцию handle_dialog. Она сформирует оставшиеся поля JSON, которые отвечают
    # непосредственно за ведение диалога
    handle_dialog(request.json, response)

    logging.info('Response: %r', request.json)

    # Преобразовываем в JSON и возвращаем
    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.
        # Запишем подсказки, которые мы ему покажем в первый раз

        sessionStorage[user_id] = {
            'suggests': [
                "Число загадано.",
                "Не хочу.",
                "Отстань!"
            ],
            'first_name': None
        }
        # создаём словарь, диапазона чисел
        sessiondiap[user_id] = {
            'start':  1,
            'end':    100,
            'tis':    0,
            'step':   0,
            'itis':   50,
            'znak':   '',
            'regim':  '0'
            }
        res['response']['text'] = 'Привет! Я - Алиса.  Назови свое имя.'
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, то это говорит о том,
    # что пользователь ещё не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'

        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться!     ' + first_name.title()\
                          + ',   загадай число от 1 до 1000, а я попробую его отгадать.'
            res['response']['buttons'] = get_suggests(user_id)
            sessiondiap[user_id]['regim'] = 'загадай'
        return

    if sessiondiap[user_id]['regim'] == 'загадай':
        if 'загада' in req['request']['original_utterance'].lower():
            sessiondiap[user_id]['regim'] = 'игра'
            sessiondiap[user_id]['znak'] = '>'
            res['response']['text'] = 'Тогда начнем.    Задуманное число > %s ?' % (
                sessiondiap[user_id]['itis'])
        else:
            res['response']['end_session'] = True
        return

    # сюда попадаем когда начата игра
    st = get_otvet(user_id, req['request']['original_utterance'].lower())
    if st == 'да' or st == 'нет':
        change_diap(user_id, st)
#        res['response']['text'] = 'Все говорят "%s", а ты купи слона!' % (
#            st)
        res['response']['text'] = 'Твое число  > %s ?' % (
                sessiondiap[user_id]['itis'])
#        req['request']['original_utterance'])
    else:
        res['response']['text'] = 'Не поняла твой ответ  "%s".  Пожалуйста, ответь еще раз!' % (
            req['request']['original_utterance'])
    res['response']['buttons'] = get_suggests(user_id)


def get_otvet(user_id, st):

    st0 = st
    if st in  ['да' , 'конечно', 'немного', 'намного']:
        st0 = 'да'
    elif '>' in st or 'больше' in st:
        if sessiondiap[user_id]['znak'] == '>':
            st0 = 'да'
        else:
            st0 = 'нет'

    elif '<' in st or 'меньше' in st:
        if sessiondiap[user_id]['znak'] == '<':
            st0 = 'да'
        else:
            st0 = 'нет'

    return st0


def change_diap(user_id, st):

    if sessiondiap[user_id]['znak'] == '>' and st == 'да':
        sessiondiap[user_id]['start'] = sessiondiap[user_id]['itis'] + 1

    elif sessiondiap[user_id]['znak'] == '>' and st == 'нет':
        sessiondiap[user_id]['end'] = sessiondiap[user_id]['itis'] - 1

    elif sessiondiap[user_id]['znak'] == '<' and st == 'да':
        sessiondiap[user_id]['end'] = sessiondiap[user_id]['itis'] - 1

    elif sessiondiap[user_id]['znak'] == '<' and st == 'нет':
            sessiondiap[user_id]['start'] = sessiondiap[user_id]['itis'] + 1

    sessiondiap[user_id]['itis'] = int((sessiondiap[user_id]['end'] + sessiondiap[user_id]['start'] - 1) / 2)
    sessiondiap[user_id]['step'] = sessiondiap[user_id]['step'] + 1


# Функция возвращает две подсказки для ответа.
def get_suggests(user_id):
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests'][:2]
    ]

    # Убираем первую подсказку, чтобы подсказки менялись каждый раз.
#    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    # Если осталась только одна подсказка, предлагаем подсказку
    # со ссылкой на Яндекс.Маркет.
    if len(suggests) < 2:
        suggests.append({
            "title": "Ладно",
            "url": "https://market.yandex.ru/search?text=слон",
            "hide": True
        })

    return suggests

def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)





if __name__ == '__main__':
    app.run()