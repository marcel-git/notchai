<template>
  <main class="guidance-page">
    <header class="page-header">
      <RouterLink class="back-link" to="/">Back to chat</RouterLink>
      <h1>Global guidance</h1>
      <p>
        These behavior rules apply to every character and conversation. They are added to each
        model call and use context tokens.
      </p>
    </header>

    <section class="guidance-card" aria-labelledby="guidance-title">
      <h2 id="guidance-title">Add a rule</h2>
      <form class="add-form" @submit.prevent="addGlobalGuidance">
        <label class="field" for="new-guidance">
          <span>Guidance <output>{{ guidanceDraft.trim().length }}/300</output></span>
          <textarea
            id="new-guidance"
            v-model="guidanceDraft"
            maxlength="300"
            rows="3"
            placeholder="For example: Never speak or act for my persona."
            required
          ></textarea>
        </label>
        <button class="primary-button" type="submit" :disabled="saving || !guidanceDraft.trim()">
          Add guidance
        </button>
      </form>

      <p v-if="error" class="notice error" role="alert">{{ error }}</p>
      <p v-if="notice" class="notice success" role="status">{{ notice }}</p>
      <p v-if="loading" class="status" role="status">Loading saved guidance...</p>
      <p v-else-if="entries.length === 0" class="status">No global guidance saved yet.</p>
      <div v-else class="table-wrap">
        <table class="guidance-table">
          <thead>
            <tr>
              <th scope="col" class="id-column">#</th>
              <th scope="col">Guidance</th>
              <th scope="col" class="actions-column">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in entries" :key="entry.id">
              <th scope="row" class="entry-id">{{ entry.id }}</th>
              <td class="guidance-cell">
                <template v-if="editingId === entry.id">
                  <textarea
                    v-model="editDraft"
                    :aria-label="`Edit guidance ${entry.id}`"
                    maxlength="300"
                    rows="3"
                  ></textarea>
                  <output class="character-count">{{ editDraft.length }}/300</output>
                </template>
                <span v-else>{{ entry.text }}</span>
              </td>
              <td class="row-actions">
                <template v-if="editingId === entry.id">
                  <button
                    class="primary-button compact-button"
                    type="button"
                    :disabled="saving || !editDraft.trim() || editDraft.trim() === entry.text"
                    @click="saveGuidance(entry)"
                  >
                    Save
                  </button>
                  <button
                    class="secondary-button compact-button"
                    type="button"
                    :disabled="saving"
                    @click="cancelEdit"
                  >
                    Cancel
                  </button>
                </template>
                <template v-else>
                  <button
                    class="secondary-button compact-button"
                    type="button"
                    :disabled="saving"
                    @click="beginEdit(entry)"
                  >
                    Edit
                  </button>
                  <button
                    class="delete-button compact-button"
                    type="button"
                    :disabled="saving"
                    @click="removeGuidance(entry)"
                  >
                    Delete
                  </button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import { RouterLink } from 'vue-router'
  import {
    addGuidance,
    deleteGuidance,
    listGuidance,
    updateGuidance,
  } from '../services/customizationApi'
  import type { GuidanceEntry } from '../types/customization'

  const entries = ref<GuidanceEntry[]>([])
  const guidanceDraft = ref('')
  const editDraft = ref('')
  const editingId = ref<number | null>(null)
  const loading = ref(true)
  const saving = ref(false)
  const error = ref('')
  const notice = ref('')

  onMounted(() => {
    void loadGuidance()
  })

  async function loadGuidance() {
    loading.value = true
    error.value = ''
    try {
      entries.value = await listGuidance()
    } catch (cause: unknown) {
      error.value = cause instanceof Error ? cause.message : 'Could not load global guidance.'
    } finally {
      loading.value = false
    }
  }

  async function addGlobalGuidance() {
    const text = guidanceDraft.value.trim()
    if (!text || saving.value) return
    saving.value = true
    error.value = ''
    notice.value = ''
    try {
      const entry = await addGuidance(text)
      entries.value.push(entry)
      guidanceDraft.value = ''
      notice.value = 'Guidance added.'
    } catch (cause: unknown) {
      error.value = cause instanceof Error ? cause.message : 'Could not add guidance.'
    } finally {
      saving.value = false
    }
  }

  function beginEdit(entry: GuidanceEntry) {
    editingId.value = entry.id
    editDraft.value = entry.text
    error.value = ''
    notice.value = ''
  }

  function cancelEdit() {
    editingId.value = null
    editDraft.value = ''
  }

  async function saveGuidance(entry: GuidanceEntry) {
    const text = editDraft.value.trim()
    if (!text || text === entry.text || saving.value) return
    saving.value = true
    error.value = ''
    notice.value = ''
    try {
      const updated = await updateGuidance(entry.id, text)
      entry.text = updated.text
      cancelEdit()
      notice.value = 'Guidance updated.'
    } catch (cause: unknown) {
      error.value = cause instanceof Error ? cause.message : 'Could not update guidance.'
    } finally {
      saving.value = false
    }
  }

  async function removeGuidance(entry: GuidanceEntry) {
    if (saving.value || !window.confirm(`Delete guidance ${entry.id}?`)) return
    saving.value = true
    error.value = ''
    notice.value = ''
    try {
      await deleteGuidance(entry.id)
      entries.value = entries.value.filter((item) => item.id !== entry.id)
      notice.value = 'Guidance deleted.'
    } catch (cause: unknown) {
      error.value = cause instanceof Error ? cause.message : 'Could not delete guidance.'
    } finally {
      saving.value = false
    }
  }
</script>

<style scoped>
  .guidance-page {
    width: min(900px, 100%);
    height: 100%;
    margin: 0 auto;
    padding: 38px 32px;
    overflow-y: auto;
  }

  .page-header {
    margin-bottom: 28px;
  }

  .back-link {
    color: var(--color-gold);
    font-size: 12px;
    text-decoration: none;
  }

  h1 {
    margin: 16px 0 6px;
    color: #e5e5d9;
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 32px;
    font-weight: 500;
  }

  .page-header p,
  .status {
    color: var(--color-muted);
    font-size: 12px;
    line-height: 1.6;
  }

  .guidance-card {
    display: grid;
    gap: 18px;
    padding: 24px;
    border: 1px solid var(--color-line);
    border-radius: 12px;
    background: rgba(23, 33, 27, 0.82);
  }

  h2 {
    margin: 0;
    color: #e5e5d9;
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 22px;
    font-weight: 500;
  }

  .add-form {
    display: grid;
    justify-items: start;
    gap: 12px;
  }

  .field {
    display: grid;
    width: 100%;
    gap: 8px;
    color: #cdd2c9;
    font-size: 12px;
  }

  .field > span {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
  }

  output,
  .character-count {
    color: var(--color-gold);
    font-size: 10px;
    font-variant-numeric: tabular-nums;
  }

  textarea {
    width: 100%;
    min-height: 76px;
    resize: vertical;
    padding: 10px;
    border: 1px solid rgba(211, 218, 201, 0.14);
    border-radius: 7px;
    background: #111813;
    color: var(--color-text);
    font: inherit;
    line-height: 1.5;
  }

  .table-wrap {
    overflow-x: auto;
  }

  .guidance-table {
    width: 100%;
    border-collapse: collapse;
    color: #cdd2c9;
    font-size: 12px;
    line-height: 1.55;
    text-align: left;
  }

  .guidance-table th,
  .guidance-table td {
    padding: 12px 10px;
    border-top: 1px solid var(--color-line);
    vertical-align: top;
  }

  .guidance-table thead th {
    color: var(--color-muted);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .id-column,
  .entry-id {
    width: 48px;
    color: var(--color-muted);
    font-variant-numeric: tabular-nums;
  }

  .actions-column {
    width: 170px;
  }

  .guidance-cell {
    min-width: 240px;
    overflow-wrap: anywhere;
    white-space: pre-wrap;
  }

  .guidance-cell textarea {
    min-width: 240px;
  }

  .character-count {
    display: block;
    margin-top: 4px;
    text-align: right;
  }

  .row-actions {
    width: 170px;
    white-space: nowrap;
  }

  .row-actions button {
    margin: 0 5px 5px 0;
  }

  .primary-button,
  .secondary-button,
  .delete-button {
    min-height: 39px;
    padding: 0 14px;
    border: 1px solid transparent;
    border-radius: 7px;
    font-size: 12px;
  }

  .primary-button {
    border-color: rgba(196, 169, 110, 0.45);
    background: rgba(60, 91, 65, 0.45);
    color: var(--color-text);
  }

  .secondary-button {
    border-color: rgba(211, 218, 201, 0.18);
    background: rgba(211, 218, 201, 0.06);
    color: #cdd2c9;
  }

  .delete-button {
    border-color: rgba(229, 164, 155, 0.28);
    background: rgba(105, 50, 46, 0.16);
    color: #e5a49b;
  }

  .compact-button {
    min-height: 32px;
    padding: 0 9px;
    font-size: 10px;
  }

  button:disabled {
    cursor: wait;
    opacity: 0.6;
  }

  .notice {
    margin: 0;
    padding: 11px 13px;
    border-radius: 7px;
    font-size: 12px;
    line-height: 1.5;
  }

  .error {
    border: 1px solid rgba(229, 164, 155, 0.24);
    background: rgba(105, 50, 46, 0.2);
    color: #e5a49b;
  }

  .success {
    border: 1px solid rgba(126, 170, 131, 0.24);
    background: rgba(49, 86, 63, 0.22);
    color: #a6c7a8;
  }

  .status {
    margin: 0;
  }

  @media (max-width: 580px) {
    .guidance-page {
      padding: 24px 16px;
    }

    .guidance-card {
      padding: 18px;
    }
  }
</style>
