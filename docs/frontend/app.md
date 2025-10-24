# 🎨 Фронтенд: `app.js`

Файл `app.js` — это основная логика интерфейса для взаимодействия пользователя с API.  
Он отвечает за сбор данных формы, отправку запросов к серверу, отображение результатов маршрута и работу с картой (через Leaflet).

---

## ⚙️ Основные функции

### 1. Отправка данных формы
Пользователь вводит:
- интересы (через запятую),
- количество доступных часов,
- текущую локацию.

После нажатия «Построить маршрут»:
- данные собираются в объект `payload`;
- выполняется запрос `POST /api/itinerary`;
- ответ с маршрутом отображается на странице.

```js
async function fetchItinerary(payload) {
  const response = await fetch("/api/itinerary", { ... });
  return response.json();
}
```

---

### 2. Очистка и обработка интересов
```js
function sanitizeInterestInput(raw) {
  return raw.split(",").map((chunk) => chunk.trim()).filter(Boolean);
}
```
Разделяет строку интересов по запятым и убирает пустые значения.

---

### 3. Работа с картой
Используется **Leaflet.js**:
- при первом вызове создаётся карта (`ensureMap`);
- на ней отображаются метки остановок маршрута (`renderMap`);
- карта автоматически масштабируется под все точки (`fitBounds`).

```js
function renderMap(stops) {
  markersLayer.clearLayers();
  stops.forEach((stop, index) => { ... });
  mapInstance.fitBounds(bounds, { padding: [30, 30] });
}
```

---

### 4. Отображение маршрута
Функция `renderItinerary(data)` выводит:
- краткое описание (`summary`);
- список остановок (`stopsList`);
- дополнительные заметки (`notesList`);
- интерактивную карту.

```js
function renderItinerary(data) {
  summaryNode.textContent = `${data.summary}...`;
  data.stops.forEach((stop, index) => { ... });
  renderMap(data.stops);
}
```

---

### 5. Отправка обратной связи
После построения маршрута пользователь может оценить его и оставить комментарий.  
Эти данные отправляются на сервер в фоне:

```js
feedbackForm.addEventListener("submit", async (event) => {
  const payload = {
    rating,
    comment,
    interests,
    location,
    available_hours,
    stops,
  };
  await fetch("/api/feedback", { method: "POST", body: JSON.stringify(payload) });
});
```

---

## 🧠 Переменные и структура

| Переменная | Назначение |
|-------------|------------|
| `form` | Форма запроса маршрута |
| `summaryNode` | Блок краткого описания маршрута |
| `stopsList` | Контейнер со списком остановок |
| `notesList` | Дополнительные комментарии |
| `mapNode` | Элемент карты |
| `feedbackForm` | Форма отправки отзыва |
| `mapInstance`, `markersLayer` | Объекты Leaflet |
| `lastItineraryContext` | Хранит последний построенный маршрут для последующей отправки фидбэка |

---

## 🗺️ Логика работы интерфейса

```
Пользователь → заполняет форму → POST /api/itinerary → Отображение маршрута + карта
                                               ↓
                                        POST /api/feedback
                                               ↓
                                       Подтверждение отзыва
```

---

## 💡 Итог
`app.js` соединяет пользовательский интерфейс с API:
- собирает ввод пользователя,
- запрашивает маршрут у бэкенда,
- визуализирует результаты,
- позволяет отправить отзыв после поездки.
