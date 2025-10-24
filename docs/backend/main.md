# Описание логики — `main.py` и `models.py`

## 🧩 main.py — Точка входа FastAPI-приложения

Файл `main.py` отвечает за **инициализацию и запуск API** для проекта AI Tourist Assistant.

### Основные задачи:
- Настраивает и запускает FastAPI-приложение.  
- Подключает CORS-middleware для работы с фронтендом (например, `localhost:5173`).  
- Определяет эндпоинты API для маршрутизации и отзывов.  
- Отдаёт статические файлы и главную страницу фронтенда.  

### Структура и логика:

1. **Инициализация:**
   - Определяется базовая директория и путь к фронтенду (`FRONTEND_DIR`).
   - Проверяется наличие папки фронтенда, иначе выбрасывается исключение.
   - Загружаются переменные окружения с помощью `dotenv`.

2. **Создание приложения:**
   ```python
   app = FastAPI(title="AI Tourist Assistant", version="0.2.0")

Настраивается CORS, чтобы фронтенд мог обращаться к API.

3. **Эндпоинты:**

   | Метод                 | Путь                                                                                                                                       | Описание |
   | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
   | `GET /health`         | Проверка состояния API. Возвращает `{"status": "ok"}`.                                                                                     |          |
   | `GET /`               | Отдаёт файл `index.html` из папки фронтенда.                                                                                               |          |
   | `POST /api/itinerary` | Принимает запрос с интересами, временем и локацией, вызывает `ItineraryPlanner`, возвращает сгенерированный маршрут (`ItineraryResponse`). |          |
   | `POST /api/feedback`  | Принимает отзыв пользователя (`FeedbackRequest`), записывает его асинхронно в фоне.                                                        |          |

4. **Работа с маршрутом:**

   * При запросе `/api/itinerary` создаётся экземпляр `ItineraryPlanner`.
   * Вызывается метод `plan()`, который формирует индивидуальный маршрут.
   * Результат возвращается клиенту в формате `ItineraryResponse`.

---

## 📘 models.py — Модели данных и доменные объекты

Файл `models.py` содержит **все Pydantic-модели и структуры данных**, используемые API.

### Основные модели:

#### **ItineraryRequest**

Входная модель при генерации маршрута.

```python
class ItineraryRequest(BaseModel):
    interests: List[str]
    available_hours: float
    location: str
```

* `interests` — список интересов пользователя.
* `available_hours` — сколько часов у него есть.
* `location` — текущая локация (город, адрес).
* Содержит валидатор, который проверяет, что интересы не пустые.

---

#### **ItineraryStop**

Описывает одну остановку маршрута.

```python
class ItineraryStop(BaseModel):
    name: str
    address: str
    reason: str
    arrival_time: str
    stay_duration_minutes: int
    latitude: float
    longitude: float
```

---

#### **ItineraryResponse**

Результат генерации маршрута.

```python
class ItineraryResponse(BaseModel):
    summary: str
    total_duration_minutes: int
    stops: List[ItineraryStop]
    notes: Optional[List[str]]
```

---

#### **Place**

Доменная модель культурного объекта.

```python
@dataclass(slots=True)
class Place:
    id: int
    title: str
    description: str
    address: str
    latitude: float
    longitude: float
    category_id: int | None
    tags: List[str]
    estimated_visit_minutes: int
    source_url: Optional[str]
```

* Хранит данные об одном объекте (например, музее, театре).
* Метод `to_stop()` преобразует объект в `ItineraryStop` для добавления в маршрут.

---

#### **FeedbackRequest**

Используется для приёма отзывов о маршруте.

```python
class FeedbackRequest(BaseModel):
    rating: int
    comment: Optional[str]
    interests: List[str]
    location: str
    available_hours: float
    stops: List[FeedbackStop]
```

---

## 💡 Итог

* `main.py` — создаёт и конфигурирует API, определяет эндпоинты.
* `models.py` — описывает все структуры данных, через которые API взаимодействует с пользователем и внутренней логикой.

