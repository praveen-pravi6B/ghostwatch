<template>
  <div class="event-card" :class="{ flagged: event.rule_findings?.length }">
    <!-- Header row -->
    <div class="card-header">
      <span :class="['badge', `badge-${event.severity}`]">{{ event.severity }}</span>
      <span class="event-type">{{ event.event_type }}</span>
      <span class="source badge badge-info">{{ event.source }}</span>
      <span class="ts">{{ formatTs(event.timestamp) }}</span>
    </div>

    <!-- Summary -->
    <div class="summary">{{ event.summary }}</div>

    <!-- Process info -->
    <div class="process-row" v-if="event.process?.pid">
      <span class="mono">PID {{ event.process.pid }}</span>
      <template v-if="event.process.name">
        · <span class="mono">{{ event.process.name }}</span>
      </template>
      <template v-if="event.process.exe">
        · <span class="mono muted">{{ event.process.exe }}</span>
      </template>
      <template v-if="event.process.username">
        · <span class="muted">{{ event.process.username }}</span>
      </template>
    </div>

    <!-- Rule findings -->
    <div class="findings" v-if="event.rule_findings?.length">
      <div class="finding" v-for="f in event.rule_findings" :key="f.rule_id">
        <span class="rule-id">{{ f.rule_id }}</span>
        <span class="rule-desc">{{ f.description }}</span>
      </div>
    </div>

    <!-- Collection note -->
    <div class="note muted" v-if="event.collection_note">
      ⚠ {{ event.collection_note }}
    </div>
  </div>
</template>

<script setup>
defineProps({ event: Object })

function formatTs(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    + ' ' + d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.event-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: border-color 0.15s;
}
.event-card.flagged {
  border-left: 3px solid var(--orange);
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.event-type { font-weight: 500; flex: 1; }
.ts { color: var(--muted); font-size: 12px; margin-left: auto; white-space: nowrap; }
.summary { font-size: 13px; }
.process-row { font-size: 12px; color: var(--muted); display: flex; gap: 4px; flex-wrap: wrap; }
.mono { font-family: var(--mono); }
.muted { color: var(--muted); }
.findings { display: flex; flex-direction: column; gap: 4px; }
.finding {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  background: #1c1208;
  border: 1px solid #3d2b00;
  border-radius: 4px;
  padding: 5px 8px;
  font-size: 12px;
}
.rule-id {
  font-family: var(--mono);
  color: var(--orange);
  white-space: nowrap;
  font-weight: 600;
}
.rule-desc { color: var(--text); }
.note { font-size: 11px; margin-top: 2px; }
</style>
