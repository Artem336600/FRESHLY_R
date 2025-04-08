# Freshly - Рекомендательная система продуктов

Веб-приложение для рекомендации продуктов на основе пользовательских запросов.

## Технологии

- Python 3.10+
- Flask
- Supabase
- DeepSeek API
- Gunicorn (для production)

## Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Artem336600/FRESHLY_R.git
cd FRESHLY_R
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл .env и добавьте необходимые переменные окружения:
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_key
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=development
```

5. Запустите приложение:
```bash
python app.py
```

## Деплой на Railway

1. Создайте новый проект на Railway

2. Подключите ваш GitHub репозиторий

3. Добавьте следующие переменные окружения в Railway:
- SUPABASE_URL
- SUPABASE_SERVICE_KEY
- DEEPSEEK_API_KEY
- DEEPSEEK_BASE_URL
- FLASK_SECRET_KEY
- FLASK_ENV=production

4. Railway автоматически определит Procfile и запустит приложение

## Структура проекта

```
FRESHLY_R/
├── static/          # Статические файлы (CSS, JS)
├── templates/       # HTML шаблоны
├── app.py          # Основной файл приложения
├── deepseek.py     # Клиент для DeepSeek API
├── recommender.py  # Логика рекомендаций
├── requirements.txt # Зависимости
└── Procfile        # Конфигурация для production
```

## Лицензия

MIT 