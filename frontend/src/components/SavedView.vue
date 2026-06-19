<template>
  <div class="saved-view">
    <h2 class="view-title">Saved Locations</h2>

    <!-- Loading -->
    <div v-if="loading" class="center-msg">
      <div class="spinner"></div>
      <span>Loading…</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="center-msg err">{{ error }}</div>

    <!-- Empty -->
    <div v-else-if="!records.length" class="center-msg">
      <span class="empty-icon">📭</span>
      <p>No saved locations yet.</p>
      <p class="sub">Search for a city to get started.</p>
    </div>

    <!-- List -->
    <TransitionGroup v-else name="list" tag="div" class="record-list">
      <div
        v-for="rec in records"
        :key="rec.id"
        class="record-card"
        @click="$emit('load', `${rec.latitude},${rec.longitude}`)"
      >
        <div class="card-icon">{{ emoji(rec) }}</div>

        <div class="card-body">
          <div class="card-location">{{ city(rec.location_name) }}</div>
          <div class="card-meta">
            <span>{{ rec.location_name }}</span>
          </div>
          <div class="card-range">
            {{ rec.date_from }} → {{ rec.date_to }}
            <span v-if="rec.label" class="card-label">{{ rec.label }}</span>
          </div>
        </div>

        <div class="card-right">
          <div class="card-temp">{{ temp(rec) }}°</div>
          <button
            class="del-btn"
            @click.stop="remove(rec.id)"
            :disabled="deleting === rec.id"
            title="Delete"
          >
            {{ deleting === rec.id ? '…' : '🗑️' }}
          </button>
        </div>
      </div>
    </TransitionGroup>

    <!-- Refresh -->
    <button class="refresh-btn" @click="load" :disabled="loading">
      ↻ Refresh
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRecords, deleteRecord } from '../api.js'
import { weatherEmoji, splitLocation, round } from '../utils.js'

defineEmits(['load'])

const records = ref([])
const loading = ref(false)
const error   = ref(null)
const deleting = ref(null)

function emoji(rec) {
  const desc = rec.weather_data?.daily?.[0]?.weather_description
  return weatherEmoji(desc)
}

function temp(rec) {
  const mean = rec.weather_data?.daily?.[0]?.temp_mean
  return mean !== null && mean !== undefined ? round(mean) : '—'
}

function city(locationName) {
  return splitLocation(locationName).city
}

async function load() {
  loading.value = true
  error.value = null
  try {
    records.value = await getRecords(50)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function remove(id) {
  deleting.value = id
  try {
    await deleteRecord(id)
    records.value = records.value.filter(r => r.id !== id)
  } catch (e) {
    error.value = e.message
  } finally {
    deleting.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.saved-view { padding-top: 0.5rem; }

.view-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(255,255,255,0.85);
  margin-bottom: 1.2rem;
}

.center-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.7rem;
  padding: 4rem 0;
  color: rgba(255,255,255,0.45);
  font-size: 0.9rem;
  text-align: center;
}
.center-msg.err { color: #ff8080; }
.empty-icon { font-size: 2.5rem; }
.sub { font-size: 0.8rem; color: rgba(255,255,255,0.3); }

.spinner {
  width: 30px; height: 30px;
  border: 2px solid rgba(255,255,255,0.12);
  border-top-color: rgba(255,255,255,0.6);
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.record-list { display: flex; flex-direction: column; gap: 0.7rem; }

.record-card {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 16px;
  padding: 0.9rem 1rem;
  cursor: pointer;
  transition: background 0.18s, transform 0.18s;
}
.record-card:hover {
  background: rgba(255,255,255,0.12);
  transform: translateY(-1px);
}

.card-icon { font-size: 2rem; flex-shrink: 0; }

.card-body { flex: 1; min-width: 0; }

.card-location {
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  font-size: 0.72rem;
  color: rgba(255,255,255,0.35);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 0.1rem;
}

.card-range {
  font-size: 0.72rem;
  color: rgba(255,255,255,0.3);
  margin-top: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.card-label {
  background: rgba(255,255,255,0.1);
  border-radius: 6px;
  padding: 0.1rem 0.4rem;
  font-size: 0.65rem;
  color: rgba(255,255,255,0.5);
}

.card-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.4rem;
  flex-shrink: 0;
}

.card-temp {
  font-size: 1.3rem;
  font-weight: 700;
  color: #fff;
}

.del-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.2rem 0.3rem;
  border-radius: 6px;
  opacity: 0.4;
  transition: opacity 0.15s, background 0.15s;
}
.del-btn:hover:not(:disabled) { opacity: 1; background: rgba(255,60,60,0.2); }
.del-btn:disabled { opacity: 0.2; cursor: not-allowed; }

.refresh-btn {
  display: block;
  margin: 1.2rem auto 0;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  color: rgba(255,255,255,0.5);
  font-size: 0.82rem;
  padding: 0.5rem 1.4rem;
  cursor: pointer;
  transition: background 0.2s;
}
.refresh-btn:hover:not(:disabled) { background: rgba(255,255,255,0.12); }

/* list transition */
.list-leave-active { transition: all 0.3s ease; }
.list-leave-to     { opacity: 0; transform: translateX(20px); }
</style>
