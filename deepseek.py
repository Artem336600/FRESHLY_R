import os
import requests
from dotenv import load_dotenv

load_dotenv()

class DeepSeekClient:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_recommendations(self, query):
        """
        Получает рекомендации продуктов на основе запроса
        
        Args:
            query (str): Поисковый запрос пользователя
            
        Returns:
            dict: Словарь с результатами поиска
        """
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
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Ошибка API: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Ошибка при запросе к API: {str(e)}"}

    def get_category_products(self, category):
        """
        Получает продукты для определенной категории
        
        Args:
            category (str): Название категории
            
        Returns:
            dict: Словарь с продуктами категории
        """
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
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Ошибка API: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Ошибка при запросе к API: {str(e)}"} 