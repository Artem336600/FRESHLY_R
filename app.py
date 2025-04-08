# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
from deepseek import DeepSeekClient
from supabase import create_client, Client

# Импортируем основную функцию из нашего модуля
from recommender import get_recommendations

load_dotenv() # Загружаем переменные из .env файла

app = Flask(__name__)
# Установите секретный ключ для Flask сессий (хотя здесь они не используются, это хорошая практика)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_default_secret_key_for_dev")

# Инициализация клиентов
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")  # Используем правильное имя переменной
)

deepseek_client = DeepSeekClient()

# --- Маршруты ---

@app.route('/', methods=['GET'])
def index():
    """Отображает главную страницу с формой ввода темы."""
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    """Обрабатывает POST-запрос с темой и отображает результаты."""
    theme = request.form.get('theme', '').strip()
    error = None
    products = []

    if not theme:
        error = "Пожалуйста, введите тему."
        # Возвращаем на главную страницу с ошибкой
        return render_template('index.html', error=error)
    else:
        # Вызываем нашу основную логику
        results_data = get_recommendations(theme)
        products = results_data.get('products', [])
        error = results_data.get('error') # Получаем возможную ошибку из recommender

        # Отображаем страницу с результатами
        return render_template('results.html', theme=theme, products=products, error=error)

@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/category/<category>')
def category(category):
    results = deepseek_client.get_category_products(category)
    if 'error' in results:
        return render_template('category.html', category=category, error=results['error'])
    return render_template('category.html', category=category, products=results.get('products', []))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Здесь будет обработка формы
        return jsonify({'status': 'success'})
    return render_template('contact.html')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    if not query:
        return render_template('search.html', query='')
    
    results = deepseek_client.get_recommendations(query)
    if 'error' in results:
        return render_template('search.html', query=query, error=results['error'])
    return render_template('search.html', query=query, products=results.get('products', []))

# --- Запуск приложения (для локальной разработки) ---
if __name__ == '__main__':
    # debug=True удобен для разработки, но НЕ ИСПОЛЬЗУЙТЕ в продакшене!
    # host='0.0.0.0' делает сервер доступным по сети (не только с localhost)
    app.run(debug=True, host='0.0.0.0', port=5001) # Используем порт 5001, чтобы не конфликтовать с другими
    print("Успешно подключено к Supabase.")
    print("Клиент DeepSeek инициализирован.")