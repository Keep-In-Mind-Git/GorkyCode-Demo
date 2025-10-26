const form = document.getElementById("itinerary-form");
const summaryNode = document.getElementById("summary");
const stopsList = document.getElementById("stops");
const resultsPanel = document.getElementById("results-panel");
const stopTemplate = document.getElementById("stop-template");
const notesList = document.getElementById("notes");
const mapNode = document.getElementById("map");
const feedbackForm = document.getElementById("feedback-form");
const feedbackRating = document.getElementById("feedback-rating");
const feedbackComment = document.getElementById("feedback-comment");
const feedbackStatus = document.getElementById("feedback-status");

let mapInstance;
let markersLayer;
let lastItineraryContext = null;
let leafletApi;

async function fetchItinerary(payload) {
  const response = await fetch("/api/itinerary", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Ошибка при генерации маршрута");
  }

  return response.json();
}

function sanitizeInterestInput(raw) {
  return raw
    .split(",")
    .map((chunk) => chunk.trim())
    .filter(Boolean);
}

function ensureMap() {
  if (!leafletApi) {
    leafletApi = window.L;
  }

  if (!leafletApi) {
    console.warn("Leaflet API не загружен, карта недоступна.");
    return;
  }

  if (mapInstance || !mapNode) {
    return;
  }
  mapInstance = leafletApi.map("map", {
    scrollWheelZoom: false,
    zoomControl: true,
  });
  leafletApi
    .tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
    })
    .addTo(mapInstance);
  markersLayer = leafletApi.layerGroup().addTo(mapInstance);
}

function renderMap(data) {
  if (!mapNode) {
    return;
  }

  if (!leafletApi) {
    leafletApi = window.L;
  }

  if (!leafletApi) {
    mapNode.hidden = true;
    return;
  }

  if (!data || !Array.isArray(data.stops) || data.stops.length === 0) {
    mapNode.classList.remove("visible");
    mapNode.hidden = true;
    if (markersLayer) {
      markersLayer.clearLayers();
    }
    return;
  }

  ensureMap();
  markersLayer.clearLayers();

  const bounds = [];
  const routePoints = [];

  // Add user location marker
  if (data.user_latitude && data.user_longitude) {
    const userCoords = [data.user_latitude, data.user_longitude];
    bounds.push(userCoords);
    routePoints.push(userCoords);
    const userIcon = leafletApi.divIcon({
      className: "map-marker user-marker",
      html: `<span>★</span>`,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
    });
    const userMarker = leafletApi.marker(userCoords, { icon: userIcon });
    userMarker.bindPopup(`<strong>Вы здесь</strong>`);
    markersLayer.addLayer(userMarker);
  }

  data.stops.forEach((stop, index) => {
    const coords = [stop.latitude, stop.longitude];
    bounds.push(coords);
    routePoints.push(coords);
    const icon = leafletApi.divIcon({
      className: "map-marker",
      html: `<span>${index + 1}</span>`,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
    });
    const marker = leafletApi.marker(coords, { icon });
    marker.bindPopup(`<strong>${stop.name}</strong><br>${stop.address}`);
    markersLayer.addLayer(marker);
  });

  // Add polyline for the route
  if (routePoints.length > 1) {
    const polyline = leafletApi.polyline(routePoints, { color: '#6366f1', weight: 5 });
    markersLayer.addLayer(polyline);
  }

  mapNode.hidden = false;
  mapNode.classList.add("visible");
  mapInstance.fitBounds(bounds, { padding: [50, 50] });
  setTimeout(() => mapInstance.invalidateSize(), 150);
}

function renderItinerary(data) {
  const hours = data.total_duration_minutes / 60;
  const durationText = hours >= 1 ? `${hours.toFixed(1)} ч.` : `${data.total_duration_minutes} мин.`;
  summaryNode.textContent = `${data.summary}. Общая длительность: ${durationText}`;

  stopsList.replaceChildren();
  data.stops.forEach((stop, index) => {
    const fragment = stopTemplate.content.cloneNode(true);
    fragment.querySelector(".stop-name").textContent = `${index + 1}. ${stop.name}`;
    fragment.querySelector(
      ".stop-timing"
    ).textContent = `${stop.arrival_time} · ${stop.stay_duration_minutes} мин.`;
    fragment.querySelector(".stop-address").textContent = stop.address;
    fragment.querySelector(".stop-reason").textContent = stop.reason;
    stopsList.appendChild(fragment);
  });

  if (Array.isArray(data.notes) && data.notes.length > 0) {
    notesList.replaceChildren();
    data.notes.forEach((note) => {
      const li = document.createElement("li");
      li.textContent = note;
      notesList.appendChild(li);
    });
    notesList.hidden = false;
  } else {
    notesList.hidden = true;
    notesList.replaceChildren();
  }

  renderMap(data);

  if (feedbackForm) {
    feedbackForm.hidden = false;
    feedbackStatus.hidden = true;
    feedbackStatus.textContent = "";
    feedbackRating.value = "";
    feedbackComment.value = "";
  }

  resultsPanel.hidden = false;
  resultsPanel.scrollIntoView({ behavior: "smooth" });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    interests: sanitizeInterestInput(document.getElementById("interests").value),
    available_hours: Number.parseFloat(document.getElementById("hours").value),
    location: document.getElementById("location").value.trim(),
  };

  if (!payload.interests.length) {
    alert("Добавьте хотя бы один интерес");
    return;
  }

  if (Number.isNaN(payload.available_hours) || payload.available_hours <= 0) {
    alert("Введите корректное количество часов");
    return;
  }

  try {
    form.classList.add("loading");
    const itinerary = await fetchItinerary(payload);
    renderItinerary(itinerary);
    lastItineraryContext = { request: payload, response: itinerary };
  } catch (error) {
    alert(error.message);
  } finally {
    form.classList.remove("loading");
  }
});

if (feedbackForm) {
  feedbackForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!lastItineraryContext) {
      alert("Сначала постройте маршрут");
      return;
    }

    const rating = Number.parseInt(feedbackRating.value, 10);
    if (!Number.isInteger(rating) || rating < 1 || rating > 5) {
      alert("Выберите оценку маршрута");
      return;
    }

    feedbackForm.classList.add("loading");
    feedbackStatus.hidden = true;
    feedbackStatus.textContent = "";

    const payload = {
      rating,
      comment: feedbackComment.value.trim() || null,
      interests: lastItineraryContext.request.interests,
      location: lastItineraryContext.request.location,
      available_hours: lastItineraryContext.request.available_hours,
      stops: lastItineraryContext.response.stops.map((stop) => ({
        name: stop.name,
        arrival_time: stop.arrival_time,
      })),
    };

    try {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Не удалось отправить отзыв");
      }

      feedbackStatus.textContent = "Спасибо! Отзыв отправлен.";
      feedbackStatus.hidden = false;
    } catch (error) {
      feedbackStatus.textContent = error.message;
      feedbackStatus.hidden = false;
    } finally {
      feedbackForm.classList.remove("loading");
    }
  });
}
