<template>
  <div id="app">
    <StatusBar :status="status" />
    <ToolBar
      :collecting="collecting"
      :investigating="investigating"
      :has-events="events.length > 0"
      :event-count="events.length"
      @collect="runCollect"
      @investigate="runInvestigate"
      @clear="runClear"
    />

    <main class="layout">
      <!-- Toast -->
      <transition name="toast">
        <div v-if="toast" :class="['toast', toast.type]">{{ toast.msg }}</div>
      </transition>

      <!-- Left: timeline -->
      <section class="timeline-col">
        <div class="col-header">
          <span class="col-title">Activity timeline</span>
          <span class="muted" v-if="lastCollected">Last collected {{ lastCollected }}</span>
        </div>

        <div v-if="events.length === 0" class="empty-state">
          <div class="icon">📋</div>
          <strong>No events yet</strong>
          <p>Click <strong>⚡ Collect</strong> to gather activity from your system.</p>
        </div>

        <div v-else class="event-list">
          <EventCard v-for="ev in events" :key="ev.id" :event="ev" />
        </div>
      </section>

      <!-- Right: investigation -->
      <section class="investigation-col">
        <div class="col-header">
          <span class="col-title">Investigation</span>
        </div>

        <div v-if="!investigation" class="empty-state">
          <div class="icon">🔍</div>
          <strong>No investigation yet</strong>
          <p>Collect some events then click <strong>🔍 Investigate</strong>.</p>
        </div>

        <InvestigationPanel v-else :result="investigation" />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StatusBar from './components/StatusBar.vue'
import ToolBar from './components/ToolBar.vue'
import EventCard from './components/EventCard.vue'
import InvestigationPanel from './components/InvestigationPanel.vue'
import { useApi } from './composables/useApi.js'

const api = useApi()

const status       = ref(null)
const events       = ref([])
const investigation = ref(null)
const collecting   = ref(false)
const investigating = ref(false)
const lastCollected = ref(null)
const toast        = ref(null)

function showToast(msg, type = 'info', ms = 3500) {
  toast.value = { msg, type }
  setTimeout(() => { toast.value = null }, ms)
}

async function loadStatus() {
  try { status.value = await api.getStatus() }
  catch { /* server not yet up */ }
}

async function loadEvents() {
  try { events.value = await api.getEvents() }
  catch (e) { showToast('Could not load events: ' + e.message, 'error') }
}

async function runCollect() {
  collecting.value = true
  try {
    const res = await api.collect()
    lastCollected.value = new Date().toLocaleTimeString()
    showToast(`Collected — ${res.events_saved} new event(s) saved.`)
    await loadEvents()
    await loadStatus()
  } catch (e) {
    showToast('Collection failed: ' + e.message, 'error')
  } finally {
    collecting.value = false
  }
}

async function runInvestigate() {
  investigating.value = true
  try {
    investigation.value = await api.investigate()
    showToast('Investigation complete.')
  } catch (e) {
    showToast('Investigation failed: ' + e.message, 'error')
  } finally {
    investigating.value = false
  }
}

async function runClear() {
  try {
    const res = await api.clearEvents()
    events.value = []
    investigation.value = null
    showToast(`Cleared ${res.deleted} event(s).`)
  } catch (e) {
    showToast('Clear failed: ' + e.message, 'error')
  }
}

onMounted(async () => {
  await loadStatus()
  await loadEvents()
})
</script>

<style>
/* Layout */
.layout {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 0;
  height: calc(100vh - 100px);
  overflow: hidden;
  position: relative;
}

.timeline-col,
.investigation-col {
  overflow-y: auto;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.investigation-col {
  border-left: 1px solid var(--border);
}

.col-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.col-title { font-weight: 600; font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.muted { color: var(--muted); font-size: 12px; }

.event-list { display: flex; flex-direction: column; gap: 8px; }

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 20px;
  font-size: 13px;
  z-index: 200;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}
.toast.error { border-color: var(--red); color: var(--red); }

.toast-enter-active, .toast-leave-active { transition: opacity 0.25s, transform 0.25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(10px); }
</style>
