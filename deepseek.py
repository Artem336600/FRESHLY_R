import os
import requests
from dotenv import load_dotenv

# Загружаем переменные только если файл существует
if os.path.exists('.env'):
    load_dotenv()

class DeepSeekClient:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
            
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Проверяем подключение при инициализации
        self._test_connection()
        
    def _test_connection(self):
        """Проверяет подключение к API"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers
            )
            if response.status_code != 200:
                raise ConnectionError(f"Failed to connect to DeepSeek API: {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to DeepSeek API: {str(e)}")

    def get_recommendations(self, query):
        """
        Получает рекомендации продуктов на основе запроса
        
        Args:
            query (str): Поисковый запрос пользователя
            
        Returns:
            dict: Словарь с результатами поиска
        """
        if not query:
            return {"error": "Query cannot be empty"}
            
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты - помощник по подбору продуктов. Предоставляй рекомендации в формате JSON с полями: name, price, store, rating, image_url, url"
                        },
                        {
                            "role": "user",
                            "content": f"Найди продукты по запросу: {query}"
                        }
                    ]
                },
                timeout=10  # Добавляем таймаут
            )
            
            response.raise_for_status()  # Вызовет исключение при ошибке HTTP
            return response.json()
                
        except requests.exceptions.Timeout:
            return {"error": "Timeout при запросе к API"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Ошибка при запросе к API: {str(e)}"}
        except Exception as e:
            return {"error": f"Неожиданная ошибка: {str(e)}"}

    def get_category_products(self, category):
        """
        Получает продукты для определенной категории
        
        Args:
            category (str): Название категории
            
        Returns:
            dict: Словарь с продуктами категории
        """
        if not category:
            return {"error": "Category cannot be empty"}
            
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты - помощник по подбору продуктов. Предоставляй рекомендации в формате JSON с полями: name, price, store, rating, image_url, url"
                        },
                        {
                            "role": "user",
                            "content": f"Найди продукты в категории: {category}"
                        }
                    ]
                },
                timeout=10  # Добавляем таймаут
            )
            
            response.raise_for_status()  # Вызовет исключение при ошибке HTTP
            return response.json()
                
        except requests.exceptions.Timeout:
            return {"error": "Timeout при запросе к API"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Ошибка при запросе к API: {str(e)}"}
        except Exception as e:
            return {"error": f"Неожиданная ошибка: {str(e)}"} 