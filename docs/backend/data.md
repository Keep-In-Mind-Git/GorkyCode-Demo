# Модуль `data`

Этот модуль отвечает за загрузку и предварительную обработку набора культурных объектов.  
Он состоит из двух основных файлов:

- [`build_dataset.py`](#build_datasetpy) — утилита для преобразования Excel-таблицы в JSON-формат.  
- [`places.json`](#placesjson) — готовый нормализованный датасет с объектами.  

---

## build_dataset.py

**Назначение:**  
Служебный скрипт, который преобразует Excel-файл (`cultural_objects_mnn.xlsx`) с культурными объектами в структурированный JSON-файл `places.json`, используемый в приложении.

**Основные функции:**

| Функция | Назначение |
|----------|-------------|
| `parse_point(value)` | Извлекает координаты (широта, долгота) из строки формата `POINT(lon lat)`. |
| `build_tags(*segments)` | Объединяет списки тегов в один уникальный отсортированный список. |
| `keyword_enrichment(text)` | Находит ключевые слова в названии и описании, добавляет дополнительные теги. |
| `main()` | Основной процесс: чтение Excel-файла, нормализация данных и запись в `places.json`. |

**Логика работы:**
1. Проверяется наличие Excel-файла `cultural_objects_mnn.xlsx`.  
2. Считываются данные с помощью `pandas.read_excel()`.  
3. Для каждой строки:
   - Извлекаются координаты (`coordinate`);
   - Определяется категория (`category_id`);
   - Генерируются теги на основе категории и ключевых слов (`CATEGORY_TAGS`, `KEYWORD_TAGS`);
   - Подсчитывается примерная длительность посещения (`CATEGORY_ESTIMATED_DURATION`);
   - Формируется объект словаря с полями:
     ```json
     {
       "id": 123,
       "title": "Название",
       "description": "Описание",
       "latitude": 59.93,
       "longitude": 30.33,
       "tags": ["museum", "art", "history"],
       "estimated_visit_minutes": 45
     }
     ```
4. Все объекты записываются в `places.json` (UTF-8, читаемый формат с отступами).  

**Пример запуска:**
```bash
python build_dataset.py
```

# dataset.py

## Назначение:
Загружает подготовленный датасет places.json и возвращает список объектов Place.

Основные элементы:

Элемент | Описание
1. DATA_PATH  Путь к файлу places.json.
2. load_places()	Кэшируемая функция (@lru_cache) для загрузки списка объектов. Проверяет наличие файла и парсит JSON в список Place.

Возвращаемые данные:
Список объектов Place с полями:

* id, title, description, address

* latitude, longitude

* category_id, tags

* estimated_visit_minutes, source_url

Пример использования:
```python
from app.services.dataset import load_places

places = load_places()
print(places[0].title)  # → "Музей современного искусства" ```