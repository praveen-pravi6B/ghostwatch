<template>
  <div class="panel card">
    <div class="panel-header">
      <h2>Investigation</h2>
      <span v-if="!result.ai_available" class="badge badge-unavailable">AI offline</span>
    </div>

    <!-- AI offline notice -->
    <div class="offline-notice" v-if="!result.ai_available">
      <strong>Ollama is not available.</strong>
      {{ result.ai_error || 'Start Ollama to enable AI explanations.' }}
      Rule-based findings are still shown below.
    </div>

    <!-- Clean bill of health -->
    <div class="clean-notice" v-if="!result.rule_summary?.length && result.ai_available && !result.ai_error">
      No deterministic rule findings in the collected events.
    </div>

    <!-- Rule summary -->
    <section v-if="result.rule_summary?.length">
      <h3 class="section-label">Rule findings</h3>
      <ul class="rule-list">
        <li v-for="(r, i) in result.rule_summary" :key="i" class="rule-item">{{ r }}</li>
      </ul>
    </section>

    <!-- AI explanation -->
    <section v-if="result.ai_explanation">
      <h3 class="section-label">
        AI explanation
        <span class="label-note">(based on supplied evidence only)</span>
      </h3>
      <p class="explanation">{{ result.ai_explanation }}</p>
    </section>

    <!-- Uncertainty -->
    <section v-if="result.ai_uncertainty">
      <h3 class="section-label uncertainty-label">Uncertainty</h3>
      <p class="explanation muted">{{ result.ai_uncertainty }}</p>
    </section>

    <!-- Next steps -->
    <section v-if="result.ai_next_steps?.length">
      <h3 class="section-label">Suggested manual checks</h3>
      <ul class="steps-list">
        <li v-for="(s, i) in result.ai_next_steps" :key="i">{{ s }}</li>
      </ul>
    </section>

    <!-- Evidence references -->
    <section v-if="result.ai_evidence_refs?.length">
      <h3 class="section-label">Evidence referenced by AI</h3>
      <div class="refs">
        <code v-for="(r, i) in result.ai_evidence_refs" :key="i" class="ref">{{ r }}</code>
      </div>
    </section>
  </div>
</template>

<script setup>
defineProps({ result: Object })
</script>

<style scoped>
.panel { display: flex; flex-direction: column; gap: 18px; }
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-header h2 { font-size: 15px; font-weight: 600; }

.clean-notice {
  background: #0d2119;
  border: 1px solid #2ea043;
  border-radius: var(--radius);
  padding: 10px 14px;
  font-size: 13px;
  color: var(--green);
}

.offline-notice {
  background: #2d1517;
  border: 1px solid var(--red);
  border-radius: var(--radius);
  padding: 10px 14px;
  font-size: 13px;
  color: #ffa198;
}

.section-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.label-note { text-transform: none; font-weight: 400; letter-spacing: 0; color: var(--muted); font-size: 11px; }
.uncertainty-label { color: var(--yellow); }

.rule-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.rule-item {
  background: #1c1208;
  border: 1px solid #3d2b00;
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 12px;
  font-family: var(--mono);
  color: var(--orange);
}

.explanation { font-size: 13px; line-height: 1.7; white-space: pre-wrap; }
.muted { color: var(--muted); }

.steps-list {
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

.refs { display: flex; flex-wrap: wrap; gap: 6px; }
.ref {
  background: #1c2d3e;
  border: 1px solid #1f4570;
  border-radius: 4px;
  padding: 2px 8px;
  color: var(--accent);
  font-size: 11px;
}
</style>
