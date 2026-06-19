<template>
  <Teleport to="body">
    <div class="overlay" @click.self="$emit('close')">
      <div class="modal">
        <div class="modal-header">
          <span class="modal-title">Search Location</span>
          <button class="close-btn" @click="$emit('close')">✕</button>
        </div>

        <div class="input-wrap">
          <span class="s-icon">🔍</span>
          <input
            ref="inputEl"
            v-model="query"
            type="text"
            placeholder="City, ZIP code, landmark, coordinates…"
            autocomplete="off"
            @input="onInput"
            @keydown.enter.prevent="submit"
            @keydown.escape="$emit('close')"
            @keydown.down.prevent="moveFocus(1)"
            @keydown.up.prevent="moveFocus(-1)"
          />
          <button v-if="query" class="clear-btn" @click="query = ''; suggestions = []">✕</button>
        </div>

        <!-- My location -->
        <button class="geo-btn" @click="useGeo" :disabled="geoLoading">
          <span>📍</span>
          {{ geoLoading ? 'Getting location…' : 'Use my current location' }}
        </button>

        <p v-if="geoError" class="geo-err">{{ geoError }}</p>

        <!-- Suggestions -->
        <ul v-if="suggestions.length" class="suggestions">
          <li
            v-for="(s, i) in suggestions"
            :key="i"
            :class="{ focused: focusIndex === i }"
            @mousedown.prevent="pick(s)"
          >
            <span class="sug-pin">📍</span>
            <div class="sug-text">
              <span class="sug-name">{{ s.name }}</span>
              <span class="sug-sub" v-if="s.admin1 || s.country">
                {{ [s.admin1, s.country].filter(Boolean).join(', ') }}
              </span>
            </div>
          </li>
        </ul>

        <!-- Recent / hints when no query -->
        <div v-if="!query && !suggestions.length" class="hints">
          <p class="hints-title">Try searching for</p>
          <div class="chips">
            <span @mousedown.prevent="pick({ name: 'Dubai', latitude: 25.07, longitude: 55.31 })">Dubai</span>
            <span @mousedown.prevent="pick({ name: 'London', latitude: 51.51, longitude: -0.13 })">London</span>
            <span @mousedown.prevent="pick({ name: 'Tokyo', latitude: 35.68, longitude: 139.69 })">Tokyo</span>
            <span @mousedown.prevent="pick({ name: 'New York', latitude: 40.71, longitude: -74.01 })">New York</span>
            <span @mousedown.prevent="$emit('search', '90210')">ZIP: 90210</span>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { searchLocations } from '../api.js'

const emit = defineEmits(['search', 'close'])

const query       = ref('')
const suggestions = ref([])
const focusIndex  = ref(-1)
const geoLoading  = ref(false)
const geoError    = ref('')
const inputEl     = ref(null)
let debounceTimer = null

onMounted(() => setTimeout(() => inputEl.value?.focus(), 80))

function onInput() {
  focusIndex.value = -1
  clearTimeout(debounceTimer)
  if (query.value.trim().length < 2) { suggestions.value = []; return }
  debounceTimer = setTimeout(async () => {
    try { suggestions.value = await searchLocations(query.value.trim()) }
    catch { suggestions.value = [] }
  }, 280)
}

function submit() {
  if (focusIndex.value >= 0 && suggestions.value[focusIndex.value]) {
    pick(suggestions.value[focusIndex.value]); return
  }
  if (query.value.trim()) emit('search', query.value.trim())
}

function pick(s) {
  // Use exact coordinates when available — avoids re-geocoding by name which can fail
  if (s.latitude != null && s.longitude != null) {
    emit('search', `${s.latitude},${s.longitude}`)
  } else {
    emit('search', [s.name, s.admin1, s.country].filter(Boolean).join(', '))
  }
}

function moveFocus(dir) {
  if (!suggestions.value.length) return
  focusIndex.value = Math.max(-1, Math.min(suggestions.value.length - 1, focusIndex.value + dir))
}

function useGeo() {
  if (!navigator.geolocation) { geoError.value = 'Geolocation not supported.'; return }
  geoLoading.value = true; geoError.value = ''
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      geoLoading.value = false
      emit('search', `${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}`)
    },
    (err) => {
      geoLoading.value = false
      geoError.value = err.code === 1
        ? 'Location access denied. Please allow it in your browser.'
        : 'Could not get your location. Try again.'
    },
    { timeout: 10000 }
  )
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(6px);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.modal {
  background: #1e1a14;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 24px 24px 0 0;
  width: 100%;
  max-width: 480px;
  padding: 1.5rem 1.5rem 2rem;
  animation: slide-up 0.28s cubic-bezier(.22,.68,0,1.2);
}

@keyframes slide-up {
  from { transform: translateY(100%); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.2rem;
}

.modal-title { font-size: 1rem; font-weight: 600; color: #fff; }

.close-btn {
  background: rgba(255,255,255,0.1);
  border: none;
  color: rgba(255,255,255,0.6);
  border-radius: 50%;
  width: 30px; height: 30px;
  cursor: pointer;
  font-size: 0.8rem;
  display: flex; align-items: center; justify-content: center;
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 0.8rem;
}

.s-icon {
  position: absolute;
  left: 1rem;
  font-size: 1rem;
  pointer-events: none;
}

input {
  width: 100%;
  padding: 0.9rem 2.8rem 0.9rem 2.8rem;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px;
  color: #fff;
  font-size: 1rem;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}
input::placeholder { color: rgba(255,255,255,0.35); }
input:focus { border-color: rgba(255,255,255,0.25); }

.clear-btn {
  position: absolute; right: 0.9rem;
  background: none; border: none;
  color: rgba(255,255,255,0.4); cursor: pointer; font-size: 0.85rem;
}

.geo-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.8rem 1rem;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 12px;
  color: rgba(255,255,255,0.75);
  font-size: 0.9rem;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 0.8rem;
}
.geo-btn:hover:not(:disabled) { background: rgba(255,255,255,0.1); }
.geo-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.geo-err { font-size: 0.82rem; color: #ff8080; margin-bottom: 0.6rem; }

.suggestions {
  list-style: none;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  overflow: hidden;
}

.suggestions li {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.85rem 1rem;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.suggestions li:last-child { border-bottom: none; }
.suggestions li:hover,
.suggestions li.focused { background: rgba(255,255,255,0.07); }

.sug-pin  { font-size: 0.9rem; flex-shrink: 0; }
.sug-text { display: flex; flex-direction: column; gap: 0.1rem; }
.sug-name { font-size: 0.92rem; color: #fff; font-weight: 500; }
.sug-sub  { font-size: 0.75rem; color: rgba(255,255,255,0.4); }

.hints { margin-top: 0.5rem; }
.hints-title { font-size: 0.75rem; color: rgba(255,255,255,0.35); margin-bottom: 0.7rem; text-transform: uppercase; letter-spacing: 0.8px; }

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.chips span {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 0.4rem 0.9rem;
  font-size: 0.82rem;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  transition: background 0.15s;
}
.chips span:hover { background: rgba(255,255,255,0.14); }
</style>
