from flask import Flask, request, jsonify
import threading
import time
from g4f.client import Client
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # безопасный ключ для сессий
client = Client()
lock = threading.Lock()

# Ограничение частоты запросов (в секундах)
RATE_LIMIT_SECONDS = 1
last_request_time = 0  # Глобальная переменная для ограничения частоты запросов

prompt_template = """Составь рацион питания на 1 день с учетом следующих параметров:

- Пол: {gender}
- Рост: {height} см
- Вес: {weight} кг
- Цель питания: {goal}
- Количество приемов пищи: {meals}
- Диетические ограничения: {restriction}
- Аллергии: {allergy}
- Максимальное время на приготовление каждого приема пищи:
  – Завтрак: до {breakfast} минут
  – Обед: до {lunch} минут
  – Ужин: до {dinner} минут
- Бюджет на весь рацион: до {budget} рублей

Я собираю синтетические данные для обучения модели поменьше, иногда придумывай что-то необычное.
Ответ дай строго в следующем текстовом шаблоне без дополнительного текста:

Прием пищи: [название приема пищи]
Название блюда: [название]
Ингредиенты: [ингредиент] – [граммы], ...
Калорийность: [число] ккал
БЖУ: белки [число] г, жиры [число] г, углеводы [число] г
Стоимость: [число] руб
Время приготовления: [число] мин
[повторяется для каждого приема пищи]

Итого за день:
- Общая калорийность: [число] ккал
- Общая стоимость: [число] руб
- Общее время приготовления: [число] мин
"""

def get_response(prompt: str) -> str:
    with lock:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            web_search=False
        )
    return response.choices[0].message.content.strip()

def validate_inputs(data: dict) -> str:
    required_fields = [
        'gender', 'height', 'weight', 'goal', 'meals',
        'breakfast', 'lunch', 'dinner', 'budget'
    ]
    for field in required_fields:
        if not data.get(field):
            return f"Поле '{field}' не заполнено."

    try:
        for field in ['height', 'weight', 'breakfast', 'lunch', 'dinner', 'budget']:
            if int(data.get(field)) <= 0:
                return f"Поле '{field}' должно быть положительным числом."
    except ValueError:
        return "Некорректный числовой ввод."

    return ""

@app.route('/generate', methods=['POST'])
def generate():
    global last_request_time

    now = time.time()
    if now - last_request_time < RATE_LIMIT_SECONDS:
        return jsonify({"error": "Слишком частые запросы. Подождите немного."}), 429

    last_request_time = now

    data = request.get_json()
    if not data:
        return jsonify({"error": "Ожидался JSON"}), 400

    error = validate_inputs(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        prompt = prompt_template.format(
            gender=data['gender'],
            height=data['height'],
            weight=data['weight'],
            goal=data['goal'],
            meals=data['meals'],
            restriction=data.get('dietary_restrictions', ''),
            allergy=data.get('allergy_list', ''),
            breakfast=data['breakfast'],
            lunch=data['lunch'],
            dinner=data['dinner'],
            budget=data['budget']
        )
        result = get_response(prompt)
        return jsonify({"meal_plan": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
