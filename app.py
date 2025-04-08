# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from dotenv import load_dotenv
from deepseek import DeepSeekClient
from supabase import create_client, Client

# Импортируем основную функцию из нашего модуля
from recommender import get_recommendations

# Загружаем переменные из .env файла только в development
if os.path.exists('.env'):
    load_dotenv()

app = Flask(__name__)
# Установите секретный ключ для Flask сессий
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_default_secret_key_for_dev")

# Инициализация клиентов
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

deepseek_client = DeepSeekClient()

print("Успешно подключено к Supabase.")
print("Клиент DeepSeek инициализирован.")

# --- Маршруты ---

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

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

# --- Запуск приложения ---
if __name__ == '__main__':
    # В development используем debug=True
    is_development = os.getenv('FLASK_ENV') == 'development'
    if is_development:
        app.run(debug=True, host='0.0.0.0', port=5001)
    else:
        # В production используем gunicorn (настройки в Procfile)
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))