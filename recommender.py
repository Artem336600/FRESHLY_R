# recommender.py
import sys
import os
import re
import requests
from dotenv import load_dotenv
import json
from typing import Dict, List, Optional, Tuple, Union
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Загрузка переменных окружения ---
if os.path.exists('.env'):
    load_dotenv()

# --- Конфигурация (Загружается из .env) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
SUPABASE_TABLE_NAME = "Products"
SUPABASE_CATEGORY_COLUMN = "class"

# --- Списки Категорий и Словарь Соответствий ---
HUMAN_READABLE_CATEGORIES = [
    "есть горячее(в том числе милкшейки, кофе, соусы, горячая еда, салаты и горячая еда)", "из ресторанов",
    "пекарня и кондитерская", "кофейня", "здоровый рацион", "самый сезон(овощи и прочее)",
    "овощи, грибы, зелень", "фрукты и ягоды", "молоко, масло и яйца", "сыры", "кефир, сметана, творог",
    "йогурты и десерты", "молочное для детей", "хлеб", "выпечка", "хлебцы", "вода", "соки и морсы",
    "газировка и тоники", "холодный чай и кофе", "энергетики, пиво и вино", "снеки", "шоколад и конфеты",
    "торты печенье вафли", "сухофрукты и орехи", "пастила и мармелад", "варенье мёд и пасты", "леденцы и жвачка",
    "мясо и птица", "колбаса и сосиски", "рыба и морепродукты", "закуски и паштеты", "мороженое",
    "пельмени и вареники", "овощи и ягоды", "десерты", "полуфабрикаты", "рыба и морепродукты", # Повтор для заморозки
    "лёд и кое-что ещё", "без мяса и молока", "вкусно и полезно", "вода и напитки", "спорт", "без глютена",
    "макароны крупы и мука", "сухие завтраки и каши", "масло соусы и специи", "кофе и какао", "чай", "консервы",
    "питание", "вода и напитки", # Повтор для детей
    "гигиена и уход", "для кошек", "для собак"
]

CATEGORY_SLUGS = [
    "hot_streetfood", "from_restaurants", "pastry_and_desserts", "goryachii_kofe", "healthydiet", "seasonal",
    "ovoshchi_griby_i_zelen", "Frukty_i_yagody", "milk_products", "cheese", "kefir_smetana_tvorog",
    "jogurty_deserty", "molochnoe_dlya_detej", "hleb", "vipechka", "hlebcy", "water", "soki_i_morsy",
    "napitki", "holodnyj_chaj", "energy_beer", "snacks", "shokolad_i_konfety", "cakes_cookies_waffles",
    "dried_fruits_and_nuts", "pastille_marshmallow", "bb0535d89aa9444c7fa05b006d2683f6", "bc32ca480164435f9d21e01e603e2c30",
    "beef_pork", "wurst_all", "ryba_i_moreprodukty", "zakuski_i_pashtety", "morozhenoe",
    "pelmeni_i_vareniki", "frozen_vegetables_and_berries", "deserty", "polufabrikaty", "553b84d49692448bb06588f9d694cbde", # Повтор для заморозки
    "b9c6c90166f1487888de39b933119747", "vegetarian", "30d1565e2ba14327afe286bee2797ce4", "f512b46d6fd9438b87ccb1c4ead49c22",
    "sports", "5b14c4a8f8d94f3bb9bc073e20f88da0", "makarony_krupy_muka", "hlopya_i_myusli", "oils_sauces_spices",
    "coffee_and_cocoa", "tea", "conservy", "kids_nutrition", "0a79f4817e2640d88fe176a5f7f17256", # Повтор для детей
    "kids_hygiene", "for_cats", "for_dogs"
]

CATEGORY_MAP = dict(zip(HUMAN_READABLE_CATEGORIES, CATEGORY_SLUGS))
SLUG_TO_HUMAN_MAP = {v: k for k, v in CATEGORY_MAP.items()}
ALL_CATEGORIES_FOR_PROMPT = "\n".join(HUMAN_READABLE_CATEGORIES)

def make_deepseek_request(messages, temperature=0.3):
    """Общая функция для запросов к DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": temperature
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise Exception("Timeout при запросе к DeepSeek API")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка при запросе к DeepSeek API: {str(e)}")

def get_relevant_categories(theme):
    """Получение релевантных категорий для темы"""
    if not theme:
        return None
        
    prompt = f"""
Ты помощник, который определяет релевантные категории продуктов для заданной темы.
Твоя задача: Проанализировать тему "{theme}" и выбрать из списка ниже наиболее подходящие категории продуктов.

Вот список ВСЕХ доступных категорий (используй ТОЛЬКО эти названия и ТОЧНО в таком виде, как они написаны):
--- НАЧАЛО СПИСКА КАТЕГОРИЙ ---
{ALL_CATEGORIES_FOR_PROMPT}
--- КОНЕЦ СПИСКА КАТЕГОРИЙ ---

Инструкции:
1. Внимательно прочитай тему: "{theme}".
2. Выбери из предоставленного списка от 3 до 7 самых релевантных категорий для этой темы.
3. Выводи ТОЛЬКО названия выбранных категорий из списка выше. Каждая категория должна быть на новой строке.
4. НЕ добавляй ничего лишнего: ни заголовков, ни пояснений, ни нумерации. Просто список категорий.
5. НЕ придумывай новые категории. Используй только те, что даны в списке.

Теперь определи и выведи список релевантных категорий для темы "{theme}":
"""
    try:
        messages = [
            {"role": "system", "content": "Ты ассистент, выбирающий категории продуктов из заданного списка по теме пользователя."},
            {"role": "user", "content": prompt}
        ]
        response = make_deepseek_request(messages, temperature=0.2)
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Ошибка при получении категорий: {str(e)}", file=sys.stderr)
        return None

def get_recommendations(theme: str, supabase) -> Tuple[List[dict], Optional[str]]:
    """
    Get product recommendations based on a theme using DeepSeek API.
    
    Args:
        theme (str): The theme to get recommendations for
        supabase: Supabase client instance
        
    Returns:
        Tuple[List[dict], Optional[str]]: List of recommendations and optional error message
    """
    try:
        # Input validation
        if not theme or not isinstance(theme, str):
            return [], "Invalid theme provided"
            
        # Get API key from environment
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return [], "API key not found in environment variables"
            
        # Construct the prompt
        prompt = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful shopping assistant that recommends products based on themes."
                },
                {
                    "role": "user",
                    "content": f"Recommend 5 products for the theme: {theme}. For each product, provide a name, description, and explanation of why it's recommended. Format as JSON with fields: name, description, explanation."
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Make API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=prompt,
            timeout=30  # Add timeout
        )
        
        if response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            return [], f"Failed to get recommendations: {response.status_code}"
            
        # Parse response
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # Extract recommendations from content
        try:
            recommendations = json.loads(content)
            if not isinstance(recommendations, list):
                recommendations = [recommendations]
                
            # Add placeholder image URLs
            for rec in recommendations:
                rec["image_url"] = "https://via.placeholder.com/150"
                
            return recommendations, None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse recommendations: {e}")
            return [], "Failed to parse recommendations"
            
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return [], f"Request failed: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return [], f"An unexpected error occurred: {str(e)}"

def select_products_for_theme_with_explanation(theme, category_name, products_from_db):
    """Выбор продуктов с объяснениями"""
    if not products_from_db:
        return []

    max_products_in_prompt = 40
    product_list_str = ""
    product_map_for_lookup = {}

    for i, prod in enumerate(products_from_db):
        if i >= max_products_in_prompt:
            break
        prod_name = prod.get('product', f'Неизвестный продукт {i+1}')
        display_name = f"Продукт {i+1}: {prod_name}"
        product_list_str += f"{display_name}\n"
        product_map_for_lookup[f"Продукт {i+1}"] = prod

    prompt = f"""
Ты эксперт по подбору продуктов. Тебе дана тема и список продуктов из определенной категории.
Твоя задача: Выбрать из этого списка продукты, которые НАИБОЛЕЕ соответствуют теме, и КРАТКО объяснить, почему каждый выбранный продукт подходит.

Тема: "{theme}"
Категория продуктов: "{category_name}"

Список доступных продуктов из этой категории:
{product_list_str.strip()}

Выбери подходящие продукты (от 1 до 5) и объясни выбор в формате:
Продукт N -- Объяснение почему подходит
"""

    try:
        messages = [
            {"role": "system", "content": "Ты эксперт по подбору продуктов по теме из предложенного списка с объяснением выбора."},
            {"role": "user", "content": prompt}
        ]
        response = make_deepseek_request(messages, temperature=0.3)
        response_text = response['choices'][0]['message']['content'].strip()

        selected_products = []
        for line in response_text.split('\n'):
            if ' -- ' not in line:
                continue
                
            product_id, explanation = line.split(' -- ', 1)
            product_id = product_id.strip()
            if product_id in product_map_for_lookup:
                product_data = product_map_for_lookup[product_id]
                selected_products.append({
                    'name': product_data.get('product', 'Неизвестный продукт'),
                    'cost': product_data.get('cost', 'Цена не указана'),
                    'old_price': product_data.get('old_price'),
                    'img': product_data.get('img'),
                    'weight': product_data.get('weight'),
                    'explanation': explanation.strip()
                })

        return selected_products
    except Exception as e:
        print(f"Ошибка при выборе продуктов: {str(e)}", file=sys.stderr)
        return []

# Можно добавить тестовый запуск, если файл запускается напрямую
if __name__ == '__main__':
    test_theme = "летний пикник"
    results = get_recommendations(test_theme)
    if results['error']:
        print(f"\nОшибка: {results['error']}")
    if results['products']:
        print("\nНайденные продукты:")
        for prod in results['products']:
            print(f"- {prod.get('name')} - {prod.get('explanation')}")