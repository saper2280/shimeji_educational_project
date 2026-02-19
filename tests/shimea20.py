import os
from dotenv import load_dotenv
from openai import OpenAI

# Загружаем переменные из .env
load_dotenv()

# Получаем значение из переменных окружения или .env
api_key = os.getenv("OPENAI_API_KEY", "your_api_key_here")
client = OpenAI(api_key=api_key)

# Быстрая проверка формата (placeholder если не установлен)
if api_key and api_key.startswith("sk-"):
    print("✅ Ключ задан (похоже корректно)")
else:
    print("❌ Ключ не задан — установите OPENAI_API_KEY в src/OPENAI_API_KEY.env или в окружении")

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "Ты - строгий и грубый учитель."},
        {"role": "user", "content": "Привет! Как дела?"}
    ]
)
print("Ответ ИИ:", response.choices[0].message.content)
