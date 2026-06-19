<template>
  <div class="map-view">
    <h2 class="view-title">Weather Map</h2>
    <p class="view-sub">Tap anywhere on the map to get the weather for that location.</p>

    <!-- Leaflet map container -->
    <div ref="mapEl" class="map-container"></div>

    <!-- Inline result popup (shows while user is on map tab) -->
    <Transition name="slide-up">
      <div v-if="result" class="map-result">
        <div class="mr-left">
          <span class="mr-emoji">{{ emoji }}</span>
          <div class="mr-info">
            <div class="mr-loc">{{ result.location_name }}</div>
            <div class="mr-desc">{{ result.weather_data.daily[0]?.weather_description }}</div>
          </div>
        </div>
        <div class="mr-right">
          <div class="mr-temp">{{ temp }}°C</div>
          <button class="mr-goto" @click="$emit('load', `${resultCoords.lat},${resultCoords.lng}`)">
            Open →
          </button>
        </div>
      </div>
    </Transition>

    <div v-if="mapLoading" class="map-overlay-msg">
      <div class="spinner"></div> Fetching weather…
    </div>
    <div v-if="mapError" class="map-overlay-msg err">⚠️ {{ mapError }}</div>

    <p class="map-hint">📍 Click map · Weather loads instantly</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { fetchWeather } from '../api.js'
import { weatherEmoji, round } from '../utils.js'

const props = defineProps({
  centerLat: { type: Number, default: 20 },
  centerLng: { type: Number, default: 0 },
})

const emit = defineEmits(['load'])

const mapEl        = ref(null)
const result       = ref(null)
const resultCoords = ref(null)
const mapLoading   = ref(false)
const mapError     = ref(null)

let map    = null
let marker = null

const emoji = computed(() => weatherEmoji(result.value?.weather_data?.daily?.[0]?.weather_description))
const temp  = computed(() => round(result.value?.weather_data?.daily?.[0]?.temp_mean))

// Custom pin icon (avoids Vite/Leaflet default-marker asset issue)
const pinIcon = L.divIcon({
  className: '',
  html: `<div style="font-size:2rem;line-height:1;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.6))">📍</div>`,
  iconSize: [32, 40],
  iconAnchor: [16, 40],
})

async function handleMapClick(e) {
  const { lat, lng } = e.latlng
  mapLoading.value = true
  mapError.value   = null

  // Move / place marker
  if (marker) {
    marker.setLatLng(e.latlng)
  } else {
    marker = L.marker(e.latlng, { icon: pinIcon }).addTo(map)
  }

  try {
    result.value       = await fetchWeather(`${lat.toFixed(5)}, ${lng.toFixed(5)}`)
    resultCoords.value = { lat, lng }
  } catch (err) {
    mapError.value = err.message
    result.value   = null
  } finally {
    mapLoading.value = false
  }
}

onMounted(() => {
  map = L.map(mapEl.value, {
    center: [props.centerLat || 20, props.centerLng || 0],
    zoom: props.centerLat ? 10 : 2,
    zoomControl: true,
  })

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap · © CARTO',
    subdomains: 'abcd',
    maxZoom: 19,
  }).addTo(map)

  map.on('click', handleMapClick)
})

onUnmounted(() => {
  if (map) { map.remove(); map = null }
})

// Re-center when the parent tells us the current location changed
watch(() => [props.centerLat, props.centerLng], ([lat, lng]) => {
  if (map && lat && lng) map.setView([lat, lng], 10)
})
</script>

<style scoped>
.map-view { padding-top: 0.5rem; }

.view-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(255,255,255,0.85);
  margin-bottom: 0.2rem;
}

.view-sub {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.35);
  margin-bottom: 1rem;
}

.map-container {
  width: 100%;
  height: 340px;
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.1);
}

/* force Leaflet tile backgrounds on dark maps */
:deep(.leaflet-container) { background: #1a1a1a; }
:deep(.leaflet-control-zoom a) {
  background: rgba(30,26,20,0.92) !important;
  color: rgba(255,255,255,0.7) !important;
  border-color: rgba(255,255,255,0.1) !important;
}

/* Result card below map */
.map-result {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px;
  padding: 0.9rem 1rem;
  margin-top: 0.8rem;
}

.mr-left {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}

.mr-emoji { font-size: 2rem; line-height: 1; }

.mr-info { display: flex; flex-direction: column; gap: 0.15rem; }
.mr-loc  { font-size: 0.88rem; font-weight: 600; color: #fff; }
.mr-desc { font-size: 0.75rem; color: rgba(255,255,255,0.45); }

.mr-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.4rem;
}

.mr-temp {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
}

.mr-goto {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 10px;
  color: rgba(255,255,255,0.8);
  font-size: 0.78rem;
  font-family: inherit;
  padding: 0.3rem 0.7rem;
  cursor: pointer;
  transition: background 0.18s;
}
.mr-goto:hover { background: rgba(255,255,255,0.2); }

/* Loading / error overlay message */
.map-overlay-msg {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 1rem;
  margin-top: 0.6rem;
  border-radius: 12px;
  font-size: 0.85rem;
  color: rgba(255,255,255,0.6);
  background: rgba(255,255,255,0.05);
}
.map-overlay-msg.err { color: #ff8080; background: rgba(200,50,50,0.12); }

.spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,0.15);
  border-top-color: rgba(255,255,255,0.7);
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.map-hint {
  text-align: center;
  font-size: 0.72rem;
  color: rgba(255,255,255,0.2);
  margin-top: 0.8rem;
}

/* Result slide-up transition */
.slide-up-enter-active { transition: all 0.3s ease; }
.slide-up-enter-from   { opacity: 0; transform: translateY(12px); }
</style>
