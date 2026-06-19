<template>
  <div class="app-shell">
    <div class="bg-layer" :style="bgStyle"></div>

    <div class="scroll-area">
      <div class="page">

        <!-- Top bar -->
        <div class="top-bar">
          <template v-if="activeNav === 'home'">
            <div class="logo">
              <span class="logo-icon">⛅</span>
              <span class="logo-text">Climo</span>
            </div>
          </template>
          <span v-else class="view-heading">{{ topTitle }}</span>
        </div>

        <!-- Global error banner -->
        <ErrorBanner v-if="error" :message="error" @dismiss="error = null" />

        <!-- ── HOME view ── -->
        <template v-if="activeNav === 'home'">
          <div v-if="loading" class="loading">
            <div class="spinner"></div>
            <span>Reading the skies…</span>
          </div>

          <Transition name="fade">
            <div v-if="weather && !loading">
              <WeatherHero :day="todayData" :location="weather.location_name" />
              <StatsRow    :day="todayData" />
              <ForecastStrip :days="forecastDays" />

              <div v-if="aqiInfo" class="aqi-row">
                <div class="aqi-badge" :class="aqiClass">
                  <span class="aqi-icon">🌿</span>
                  <div class="aqi-text-block">
                    <span class="aqi-label">{{ aqiInfo.label }}</span>
                    <span class="aqi-detail">{{ aqiInfo.detail }}</span>
                  </div>
                  <div class="aqi-pill">{{ airQuality.aqi }}/5</div>
                </div>
              </div>

              <!-- UV Index banner -->
              <div v-if="uvInfo" class="uv-banner">
                <div class="uv-top">
                  <span class="uv-icon">{{ uvInfo.icon }}</span>
                  <div class="uv-text">
                    <span class="uv-label">{{ uvInfo.label }}</span>
                    <span class="uv-sub">UV Index today</span>
                  </div>
                  <span class="uv-num">{{ Math.round(todayData.uv_index_max) }}</span>
                </div>
                <div class="uv-track">
                  <div class="uv-bar-fill" :style="{ width: Math.min(todayData.uv_index_max / 11 * 100, 100) + '%', background: uvInfo.color }"></div>
                </div>
              </div>

              <!-- Wikipedia city card -->
              <Transition name="fade">
                <div v-if="wikiSummary" class="wiki-card">
                  <div class="wiki-header">
                    <span class="wiki-icon">📖</span>
                    <span class="wiki-city">{{ wikiSummary.title }}</span>
                  </div>
                  <p class="wiki-text">{{ wikiSummary.extract }}</p>
                  <div class="wiki-source">via Wikipedia</div>
                </div>
              </Transition>

            </div>
          </Transition>

          <div v-if="!weather && !loading && !error" class="empty">
            <div class="empty-icon">🌍</div>
            <p class="empty-title">Finding where you are…</p>
            <p class="empty-sub">
              or <button class="text-btn" @click="openSearch">search a city</button>
            </p>
          </div>
        </template>

        <!-- ── SAVED view ── -->
        <SavedView
          v-else-if="activeNav === 'saved'"
          @load="loadFromSaved"
        />

        <!-- ── MAP view ── -->
        <MapView
          v-else-if="activeNav === 'map'"
          :centerLat="currentLat"
          :centerLng="currentLng"
          @load="loadFromMap"
        />

      </div>
    </div>

    <!-- Bottom navigation -->
    <BottomNav :active="activeNav" @change="onNavChange" />

    <!-- Search modal (overlays any view) -->
    <SearchModal v-if="showSearch" @search="handleSearch" @close="showSearch = false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import WeatherHero   from './components/WeatherHero.vue'
import StatsRow      from './components/StatsRow.vue'
import ForecastStrip from './components/ForecastStrip.vue'
import SavedView     from './components/SavedView.vue'
import MapView       from './components/MapView.vue'
import SearchModal   from './components/SearchModal.vue'
import BottomNav     from './components/BottomNav.vue'
import ErrorBanner   from './components/ErrorBanner.vue'
import { fetchWeather, fetchWikiSummary } from './api.js'
import { topGlow, AQI_HUMAN, uvLabel } from './utils.js'

const weather    = ref(null)
const loading    = ref(false)
const error      = ref(null)
const showSearch = ref(false)
const activeNav  = ref('home')
const currentLat = ref(20)
const currentLng = ref(0)
const wikiSummary = ref(null)

const _todayStr = new Date().toISOString().slice(0, 10)

const todayData = computed(() => {
  const daily = weather.value?.weather_data?.daily ?? []
  return daily.find(d => d.date === _todayStr) ?? daily[0] ?? null
})

const forecastDays = computed(() => {
  const daily = weather.value?.weather_data?.daily ?? []
  const idx = daily.findIndex(d => d.date > _todayStr)
  if (idx === -1) return []
  return daily.slice(idx, idx + 5)
})
const airQuality   = computed(() => weather.value?.weather_data?.air_quality ?? null)

const bgStyle = computed(() => {
  const glow = topGlow(todayData.value?.weather_description)
  return { background: `radial-gradient(ellipse 80% 45% at 50% -5%, ${glow} 0%, transparent 65%), #16120e` }
})

const aqiClass = computed(() => {
  const aqi = airQuality.value?.aqi
  return ['', 'aqi-1', 'aqi-2', 'aqi-3', 'aqi-4', 'aqi-5'][aqi] || ''
})

const aqiInfo  = computed(() => AQI_HUMAN[airQuality.value?.aqi] || null)
const uvInfo   = computed(() => uvLabel(todayData.value?.uv_index_max))

const topTitle = computed(() => {
  if (activeNav.value === 'saved') return 'Saved'
  if (activeNav.value === 'map')   return 'Map'
  return 'Climo'
})

// ── Search / load ────────────────────────────────────────────
async function handleSearch(location) {
  if (!location?.trim()) return
  showSearch.value = false
  activeNav.value  = 'home'
  loading.value    = true
  error.value      = null
  weather.value    = null

  try {
    weather.value = await fetchWeather(location.trim())
    currentLat.value = weather.value.latitude
    currentLng.value = weather.value.longitude
    // Fire Wikipedia fetch in background — don't block weather display
    wikiSummary.value = null
    fetchWikiSummary(weather.value.location_name).then(s => { wikiSummary.value = s })
  } catch (err) {
    error.value = err.message || 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}

// Tap a saved card → go home + reload fresh weather
function loadFromSaved(locationName) {
  activeNav.value = 'home'
  handleSearch(locationName)
}

// Tap "Open →" on the map result card → go home with that location
function loadFromMap(locationName) {
  activeNav.value = 'home'
  handleSearch(locationName)
}

// ── Navigation ───────────────────────────────────────────────
function openSearch() {
  showSearch.value = true
}

function onNavChange(id) {
  if (id === 'search') { openSearch(); return }
  activeNav.value  = id
  showSearch.value = false
}

// ── Auto-detect location on mount ────────────────────────────
onMounted(() => {
  if (!navigator.geolocation) { showSearch.value = true; return }
  loading.value = true
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      currentLat.value = coords.latitude
      currentLng.value = coords.longitude
      handleSearch(`${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}`)
    },
    () => {
      loading.value    = false
      showSearch.value = true
    },
    { timeout: 8000 }
  )
})
</script>

<style scoped>
.app-shell {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.bg-layer {
  position: absolute;
  inset: 0;
  transition: background 1.4s ease;
  z-index: 0;
}

.scroll-area {
  position: relative;
  z-index: 1;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: 90px;
  scrollbar-width: none;
}
.scroll-area::-webkit-scrollbar { display: none; }

.page {
  max-width: 480px;
  margin: 0 auto;
  padding: 0.75rem 1.25rem 1.5rem;
  color: #fff;
  min-height: 100%;
}

@media (max-width: 360px) {
  .page { padding-left: 0.9rem; padding-right: 0.9rem; }
}

/* ── Top bar ── */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.8rem;
}

/* Logo — shown on home */
.logo {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.logo-icon {
  font-size: 1.5rem;
  line-height: 1;
  filter: drop-shadow(0 0 6px rgba(255,180,60,0.55));
}

.logo-text {
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  background: linear-gradient(135deg, #ffd89b 0%, #ffe8c2 45%, #ffffff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Page title — shown on saved / map */
.view-heading {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(255,255,255,0.75);
  letter-spacing: 0.2px;
}

.icon-btn {
  width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  transition: background 0.2s;
}
.icon-btn:hover { background: rgba(255,255,255,0.14); }

/* ── Loading ── */
.loading {
  display: flex; flex-direction: column; align-items: center;
  gap: 1rem; padding: 5rem 0;
  color: rgba(255,255,255,0.45); font-size: 0.88rem;
}

.spinner {
  width: 34px; height: 34px;
  border: 2.5px solid rgba(255,255,255,0.12);
  border-top-color: rgba(255,255,255,0.7);
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Empty state ── */
.empty {
  display: flex; flex-direction: column; align-items: center;
  padding: 5rem 0; gap: 0.5rem;
}
.empty-icon  { font-size: 3.5rem; margin-bottom: 0.5rem; }
.empty-title { font-size: 1rem; font-weight: 500; color: rgba(255,255,255,0.65); }
.empty-sub   { font-size: 0.85rem; color: rgba(255,255,255,0.35); }

.text-btn {
  background: none; border: none;
  color: rgba(255,255,255,0.65);
  text-decoration: underline;
  cursor: pointer;
  font-size: inherit; font-family: inherit;
}

/* ── AQI badge ── */
.aqi-row { margin: 0 0 0.6rem; }

.aqi-badge {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.8rem 1rem;
  border-radius: 16px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
}

.aqi-icon { font-size: 1.2rem; flex-shrink: 0; }

.aqi-text-block {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  flex: 1;
}

.aqi-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: #fff;
}

.aqi-detail {
  font-size: 0.73rem;
  color: rgba(255,255,255,0.45);
}

.aqi-pill {
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(255,255,255,0.45);
  background: rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: 0.2rem 0.55rem;
  flex-shrink: 0;
}

.aqi-1 { border-color: rgba(76,175,80,.35);  background: rgba(76,175,80,.07); }
.aqi-2 { border-color: rgba(139,195,74,.35); background: rgba(139,195,74,.07); }
.aqi-3 { border-color: rgba(255,193,7,.35);  background: rgba(255,193,7,.07); }
.aqi-4 { border-color: rgba(255,87,34,.35);  background: rgba(255,87,34,.07); }
.aqi-5 { border-color: rgba(229,57,53,.35);  background: rgba(229,57,53,.09); }

/* ── UV card ── */
.uv-banner {
  background: rgba(255, 180, 30, 0.06);
  border: 1px solid rgba(255, 180, 30, 0.18);
  border-radius: 16px;
  padding: 0.85rem 1rem 0.75rem;
  margin: 0.55rem 0;
}

.uv-top {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.65rem;
}

.uv-icon { font-size: 1.4rem; flex-shrink: 0; }

.uv-text {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
  flex: 1;
}

.uv-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: #fff;
}

.uv-sub {
  font-size: 0.7rem;
  color: rgba(255,255,255,0.35);
}

.uv-num {
  font-size: 1.9rem;
  font-weight: 800;
  line-height: 1;
  color: rgba(255,200,80,0.9);
  flex-shrink: 0;
}

.uv-track {
  height: 5px;
  background: rgba(255,255,255,0.08);
  border-radius: 99px;
  overflow: hidden;
}

.uv-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.7s ease;
}

/* ── Wikipedia card ── */
.wiki-card {
  border-left: 3px solid rgba(120, 160, 255, 0.4);
  border-radius: 0 14px 14px 0;
  background: rgba(100, 130, 255, 0.05);
  padding: 0.85rem 1rem 0.75rem 1rem;
  margin: 0.55rem 0;
}

.wiki-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.45rem;
}

.wiki-icon { font-size: 0.85rem; opacity: 0.5; }

.wiki-city {
  font-size: 0.72rem;
  font-weight: 700;
  color: rgba(160, 185, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 1.2px;
}

.wiki-text {
  font-size: 0.82rem;
  color: rgba(255,255,255,0.5);
  line-height: 1.65;
  font-weight: 400;
  font-style: italic;
  margin-bottom: 0.5rem;
}

.wiki-source {
  font-size: 0.62rem;
  color: rgba(255,255,255,0.2);
  text-align: right;
  letter-spacing: 0.5px;
}

.data-source {
  font-size: 0.65rem;
  color: rgba(255,255,255,0.18);
  text-align: center;
  padding: 0.4rem 0 0.6rem;
}

/* ── Transition ── */
.fade-enter-active { transition: opacity 0.45s ease, transform 0.45s ease; }
.fade-enter-from   { opacity: 0; transform: translateY(12px); }
</style>
