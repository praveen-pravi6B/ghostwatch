<template>
  <div class="toolbar">
    <div class="left">
      <button class="primary" :disabled="collecting" @click="$emit('collect')">
        {{ collecting ? 'Collecting…' : '⚡ Collect' }}
      </button>
      <button :disabled="investigating || !hasEvents" @click="$emit('investigate')">
        {{ investigating ? 'Investigating…' : '🔍 Investigate' }}
      </button>
      <button class="danger" :disabled="!hasEvents" @click="$emit('clear')">
        🗑 Clear
      </button>
    </div>
    <div class="right">
      <span class="count" v-if="eventCount > 0">{{ eventCount }} event{{ eventCount !== 1 ? 's' : '' }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  collecting:    Boolean,
  investigating: Boolean,
  hasEvents:     Boolean,
  eventCount:    Number,
})
defineEmits(['collect', 'investigate', 'clear'])
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid var(--border);
  gap: 8px;
}
.left { display: flex; gap: 8px; }
.count { color: var(--muted); font-size: 13px; }
</style>
