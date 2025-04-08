# recommender.py
import sys
import os
import re
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv # Для загрузки .env

# --- Загрузка переменных окружения ---
load_dotenv() # Загружает переменные из .env файла

# --- Конфигурация (Загружается из .env) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
SUPABASE_TABLE_NAME = "Products"
SUPABASE_CATEGORY_COLUMN = "class" # Убедитесь, что имя столбца верное

# --- Проверка наличия ключей ---
if not all([SUPABASE_URL, SUPABASE_KEY, DEEPSEEK_API_KEY]):
    # В веб-приложении лучше не выходить, а логировать или возвращать ошибку
    print("ОШИБКА: Не все переменные окружения установлены (SUPABASE_URL, SUPABASE_SERVICE_KEY, DEEPSEEK_API_KEY). Проверьте .env файл.", file=sys.stderr)
    # Можно выбросить исключение, чтобы Flask его поймал
    # raise ValueError("Отсутствуют необходимые переменные окружения")

# --- Инициализация клиентов (лучше делать один раз при старте приложения или лениво) ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Успешно подключено к Supabase.")
except Exception as e:
    print(f"Ошибка подключения к Supabase: {e}", file=sys.stderr)
    supabase = None # Обработка ошибки

try:
    deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    print("Клиент DeepSeek инициализирован.")
except Exception as e:
    print(f"Ошибка инициализации клиента DeepSeek: {e}", file=sys.stderr)
    deepseek_client = None # Обработка ошибки

# --- Списки Категорий и Словарь Соответствий ---
# (Остаются как в вашем оригинальном скрипте)
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

if len(HUMAN_READABLE_CATEGORIES) != len(CATEGORY_SLUGS):
    print("ОШИБКА: Длины списков категорий не совпадают!", file=sys.stderr)
    # raise ValueError("Длины списков категорий не совпадают")

CATEGORY_MAP = dict(zip(HUMAN_READABLE_CATEGORIES, CATEGORY_SLUGS))
SLUG_TO_HUMAN_MAP = {v: k for k, v in CATEGORY_MAP.items()}
ALL_CATEGORIES_FOR_PROMPT = "\n".join(HUMAN_READABLE_CATEGORIES)

# --- Функция 1: Получение категорий (без изменений, но добавим проверку клиента) ---
def get_relevant_categories(theme):
    if not deepseek_client:
        print("Ошибка: Клиент DeepSeek не инициализирован.", file=sys.stderr)
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
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты ассистент, выбирающий категории продуктов из заданного списка по теме пользователя."},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка при запросе категорий у DeepSeek: {e}", file=sys.stderr)
        return None # Возвращаем None при ошибке

# --- Функция 2: Получение продуктов с объяснением (без изменений, но добавим проверку клиента) ---
def select_products_for_theme_with_explanation(theme, category_name, products_from_db):
    if not deepseek_client:
        print("Ошибка: Клиент DeepSeek не инициализирован.", file=sys.stderr)
        return []
    if not products_from_db:
        return []

    max_products_in_prompt = 40
    product_list_str = ""
    product_map_for_lookup = {}

    for i, prod in enumerate(products_from_db):
        prod_name = prod.get('product', f'Неизвестный продукт {i+1}')
        display_name = f"Продукт {i+1}: {prod_name}"
        product_list_str += f"{display_name}\n"
        product_map_for_lookup[f"Продукт {i+1}"] = prod_name

        if i >= max_products_in_prompt - 1:
             product_list_str += "... (и другие)\n"
             break

    prompt = f"""
Ты эксперт по подбору продуктов. Тебе дана тема и список продуктов из определенной категории.
Твоя задача: Выбрать из этого списка продукты, которые НАИБОЛЕЕ соответствуют теме, и КРАТКО объяснить, почему каждый выбранный продукт подходит.

Тема: "{theme}"
Категория продуктов: "{category_name}"

Список доступных продуктов из этой категории (используй идентификатор "Продукт N" для выбора):
--- НАЧАЛО СПИСКА ПРОДУКТОВ ---
{product_list_str.strip()}
--- КОНЕЦ СПИСКА ПРОДУКТОВ ---

Инструкции:
1. Внимательно проанализируй тему "{theme}".
2. Просмотри предоставленный список продуктов.
3. Выбери от 1 до 5 продуктов из списка, которые лучше всего подходят под тему "{theme}".
4. Для КАЖДОГО выбранного продукта напиши КРАТКОЕ (1-2 предложения) объяснение, почему он релевантен теме.
5. Выведи результат в формате:
   Идентификатор Продукта -- Объяснение
   Например:
   Продукт 5 -- Отлично подходит для пикника, так как его легко взять с собой и он не требует приготовления.
   Продукт 12 -- Согревающий напиток, идеален для зимнего вечера.
6. Используй ТОЛЬКО идентификаторы ("Продукт 1", "Продукт 2" и т.д.) из списка выше.
7. Используй разделитель " -- " (пробел, два дефиса, пробел) между идентификатором и объяснением.
8. Каждая пара "Идентификатор -- Объяснение" должна быть на новой строке.
9. НЕ добавляй заголовки, нумерацию строк или любой другой текст вне указанного формата.
10. Если ни один продукт из списка не подходит под тему, не выводи ничего (пустой ответ).

Теперь выбери подходящие продукты для темы "{theme}" и объясни свой выбор в указанном формате:
"""
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты эксперт по подбору продуктов по теме из предложенного списка с объяснением выбора."},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.3
        )
        response_text = response.choices[0].message.content.strip()

        selected_products_with_explanation = []
        lines = response_text.split('\n')

        for line in lines:
            line = line.strip()
            if " -- " in line:
                parts = line.split(" -- ", 1)
                product_id = parts[0].strip()
                explanation = parts[1].strip() if len(parts) > 1 else "Нет объяснения."
                original_product_name = product_map_for_lookup.get(product_id)
                if original_product_name:
                    selected_products_with_explanation.append({
                        'name': original_product_name,
                        'explanation': explanation
                    })
                else:
                     print(f"Предупреждение: ИИ вернул неизвестный идентификатор продукта '{product_id}'. Пропускаем.", file=sys.stderr)

        return selected_products_with_explanation

    except Exception as e:
        print(f"Ошибка при запросе выбора продуктов и объяснений у DeepSeek: {e}", file=sys.stderr)
        return [] # Возвращаем пустой список при ошибке

# --- Основная функция для вызова из Flask ---
def get_recommendations(theme):
    """
    Основная функция, выполняющая весь процесс получения рекомендаций.
    Возвращает словарь: {'products': list_of_products, 'error': error_message_or_None}
    """
    # Проверка инициализации клиентов
    if not supabase or not deepseek_client:
         return {'products': [], 'error': "Ошибка: Клиенты Supabase или DeepSeek не инициализированы."}
    if not theme:
         return {'products': [], 'error': "Ошибка: Тема не может быть пустой."}

    print(f"\nПолучение рекомендаций для темы: '{theme}'")

    # 1. Получаем релевантные категории
    print("Шаг 1: Определение релевантных категорий...")
    relevant_categories_text = get_relevant_categories(theme)

    if not relevant_categories_text:
        error_msg = "Не удалось получить категории от ИИ."
        print(error_msg, file=sys.stderr)
        return {'products': [], 'error': error_msg}
    print(f"ИИ предложил категории:\n{relevant_categories_text}")

    # 2. Преобразуем категории в слаги
    slug_list = []
    lines = relevant_categories_text.strip().split('\n')
    for line in lines:
        category_name = line.strip()
        if not category_name: continue
        slug = CATEGORY_MAP.get(category_name)
        if slug:
            slug_list.append(slug)
        else:
            print(f"Предупреждение: Категория '{category_name}' от ИИ не найдена в словаре. Пропускаем.", file=sys.stderr)

    if not slug_list:
        error_msg = "Не найдено подходящих слагов для категорий. Невозможно выполнить запрос к БД."
        print(error_msg, file=sys.stderr)
        return {'products': [], 'error': error_msg}
    print(f"Слаги для запроса к БД: {slug_list}")

    # 3. Итерация, запрос к БД, выбор продуктов
    print("Шаг 2: Поиск, выбор продуктов и получение объяснений...")
    final_selected_products_dict = {} # Используем словарь для уникальности
    processing_error_occurred = False # Флаг для отслеживания ошибок на этом шаге

    for slug in slug_list:
        human_category_name = SLUG_TO_HUMAN_MAP.get(slug, slug)
        print(f"--- Обработка категории: '{human_category_name}' (слаг: {slug}) ---")
        try:
            response = supabase.table(SUPABASE_TABLE_NAME)\
                               .select("product, cost, img")\
                               .eq(SUPABASE_CATEGORY_COLUMN, slug)\
                               .execute()

            if response.data:
                products_in_category = response.data
                print(f"Найдено {len(products_in_category)} продуктов в БД.")

                selected_products_with_explanations = select_products_for_theme_with_explanation(
                    theme, human_category_name, products_in_category
                )

                if selected_products_with_explanations:
                    print(f"ИИ выбрал и объяснил:")
                    product_data_map = {p.get('product'): p for p in products_in_category if p.get('product')}

                    for selection in selected_products_with_explanations:
                        product_name = selection['name']
                        explanation = selection['explanation']
                        print(f"  - {product_name}: {explanation}")

                        product_data = product_data_map.get(product_name)
                        if not product_data:
                            print(f"Предупреждение: Не найдены данные для '{product_name}'.", file=sys.stderr)
                            continue

                        if product_name not in final_selected_products_dict:
                             final_selected_products_dict[product_name] = {
                                'name': product_name, # Добавим имя для удобства
                                'cost': product_data.get('cost'),
                                'img': product_data.get('img'),
                                'categories': [human_category_name],
                                'explanation': explanation
                             }
                        else:
                            if human_category_name not in final_selected_products_dict[product_name]['categories']:
                                final_selected_products_dict[product_name]['categories'].append(human_category_name)
                else:
                    print(f"ИИ не выбрал продукты из этой категории.")

            else:
                print(f"В БД не найдено продуктов для слага '{slug}'.")

        except Exception as e:
            processing_error_occurred = True
            print(f"Ошибка при обработке категории '{slug}': {e}", file=sys.stderr)
            # Не прерываем цикл, пытаемся обработать другие категории

    # 4. Формируем результат
    final_product_list = list(final_selected_products_dict.values())

    # Определяем финальное сообщение об ошибке, если нужно
    final_error = None
    if not final_product_list and not processing_error_occurred and relevant_categories_text and slug_list:
        final_error = "Не найдено подходящих продуктов по заданным критериям, хотя категории были определены."
    elif processing_error_occurred and not final_product_list:
         final_error = "Во время обработки произошли ошибки, и не удалось найти подходящие продукты."
    elif processing_error_occurred: # Продукты есть, но были ошибки
         final_error = "Во время обработки некоторых категорий произошли ошибки. Результат может быть неполным." # Можно добавить это как предупреждение

    print("\n=============================================")
    if final_product_list:
        print(f"Итоговый список продуктов ({len(final_product_list)}) для темы '{theme}' сформирован.")
    else:
        print(f"Итоговый список продуктов для темы '{theme}' пуст.")
    print("=============================================")

    return {'products': final_product_list, 'error': final_error}

# Можно добавить тестовый запуск, если файл запускается напрямую
if __name__ == '__main__':
    test_theme = "летний пикник"
    results = get_recommendations(test_theme)
    if results['error']:
        print(f"\nОшибка: {results['error']}")
    if results['products']:
        print("\nНайденные продукты:")
        for prod in results['products']:
            print(f"- {prod.get('name')} ({', '.join(prod.get('categories',[]))}) - {prod.get('explanation')}")