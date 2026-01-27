import os
from dotenv import load_dotenv
from openai import OpenAI

# Загружаем переменные из .env
load_dotenv()

# Получаем значение
api_key = "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"
client = OpenAI(api_key=api_key)
print("API-ключ:", api_key)

# Проверим, не пустой ли он
if api_key and api_key.startswith("sk-"):
    print("✅ Ключ загружен успешно!")
else:
    print("❌ Ключ не найден или записан неверно")

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "Ты - строгий и грубый учитель."},
        {"role": "user", "content": "Привет! Как дела?"}
    ]
)
print("Ответ ИИ:", response.choices[0].message.content)
