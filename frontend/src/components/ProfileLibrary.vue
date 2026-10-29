<template>
  <main class="library-page">
    <header class="page-header">
      <RouterLink class="back-link" to="/">Back to chat</RouterLink>
      <h1>{{ title }}</h1>
      <p>{{ description }}</p>
    </header>

    <p v-if="error" class="notice error" role="alert">{{ error }}</p>
    <div class="library-layout">
      <aside class="profile-list">
        <button class="primary-button" type="button" @click="newProfile">Create {{ singular }}</button>
        <p v-if="loading && profiles.length === 0" class="muted">Loading {{ title.toLowerCase() }}...</p>
        <p v-else-if="!loading && profiles.length === 0" class="muted">
          No {{ title.toLowerCase() }} yet. Create one to get started.
        </p>
        <button
          v-for="profile in profiles"
          :key="profile.id"
          class="profile-item"
          :class="{ selected: selectedId === profile.id }"
          type="button"
          @click="selectProfile(profile)"
        >
          <strong>{{ profile.name }}</strong>
          <span>{{ profile[summaryField] || 'No description added' }}</span>
        </button>
      </aside>

      <form class="profile-editor" @submit.prevent="save">
        <div class="editor-heading">
          <div>
            <p class="eyebrow">{{ selectedId ? 'EDIT PROFILE' : 'NEW PROFILE' }}</p>
            <h2>{{ selectedId ? 'Update details' : `Create a ${singular}` }}</h2>
          </div>
          <button
            v-if="selectedId"
            class="text-button danger"
            type="button"
            :disabled="saving"
            @click="remove"
          >
            Delete
          </button>
        </div>

        <label class="field">
          <span>Name</span>
          <input v-model="form.name" required maxlength="120" autocomplete="off" />
        </label>
        <label v-for="field in fields" :key="field.key" class="field">
          <span>{{ field.label }}</span>
          <textarea
            v-model="form[field.key]"
            :rows="field.rows"
            :placeholder="field.placeholder"
            maxlength="20000"
          ></textarea>
        </label>

        <p v-if="actionError" class="notice error" role="alert">{{ actionError }}</p>
        <div class="form-actions">
          <button class="primary-button" type="submit" :disabled="saving">
            {{ saving ? 'Saving...' : selectedId ? 'Save changes' : `Create ${singular}` }}
          </button>
          <button v-if="selectedId" class="text-button" type="button" @click="newProfile">
            Cancel
          </button>
        </div>
      </form>
    </div>
  </main>
</template>

<script setup lang="ts">
  import { computed, reactive, ref, watch } from 'vue'
  import type { ProfileRecord } from '../types/profiles'

  type ProfileField = {
    key: string
    label: string
    rows: number
    placeholder: string
  }

  const props = defineProps<{
    title: string
    description: string
    singular: string
    summaryField: string
    profiles: ProfileRecord[]
    fields: ProfileField[]
    loading: boolean
    error: string
    saveProfile: (id: string | null, values: Record<string, string>) => Promise<ProfileRecord>
    deleteProfile: (id: string) => Promise<void>
  }>()

  const emit = defineEmits<{
    profileSaved: [profile: ProfileRecord]
    profileDeleted: [id: string]
  }>()

  const selectedId = ref<string | null>(null)
  const form = reactive<Record<string, string>>({ name: '' })
  const saving = ref(false)
  const actionError = ref('')
  const selectedProfile = computed(() =>
    props.profiles.find((profile) => profile.id === selectedId.value),
  )

  watch(
    () => props.profiles.length,
    (count) => {
      if (selectedId.value && !props.profiles.some((profile) => profile.id === selectedId.value)) {
        newProfile()
      }
      if (!selectedId.value && count > 0) {
        const firstProfile = props.profiles[0]
        if (firstProfile) selectProfile(firstProfile)
      }
    },
    { immediate: true },
  )

  function populate(profile?: ProfileRecord) {
    form.name = profile?.name ?? ''
    for (const field of props.fields) {
      form[field.key] = profile?.[field.key] ?? ''
    }
    actionError.value = ''
  }

  function newProfile() {
    selectedId.value = null
    populate()
  }

  function selectProfile(profile: ProfileRecord) {
    selectedId.value = profile.id
    populate(profile)
  }

  async function save() {
    saving.value = true
    actionError.value = ''
    try {
      const profile = await props.saveProfile(selectedId.value, { ...form })
      emit('profileSaved', profile)
      selectProfile(profile)
    } catch (error: unknown) {
      actionError.value = error instanceof Error ? error.message : 'Could not save this profile.'
    } finally {
      saving.value = false
    }
  }

  async function remove() {
    const profile = selectedProfile.value
    if (!profile || !window.confirm(`Delete ${profile.name}?`)) return
    saving.value = true
    actionError.value = ''
    try {
      await props.deleteProfile(profile.id)
      emit('profileDeleted', profile.id)
      newProfile()
    } catch (error: unknown) {
      actionError.value = error instanceof Error ? error.message : 'Could not delete this profile.'
    } finally {
      saving.value = false
    }
  }
</script>

<style scoped>
  .library-page {
    width: min(1160px, 100%);
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

  h1,
  h2 {
    color: #e5e5d9;
    font-family: 'Playfair Display', Georgia, serif;
    font-weight: 500;
  }

  h1 {
    margin: 16px 0 6px;
    font-size: 32px;
  }

  .page-header p,
  .muted {
    color: var(--color-muted);
    font-size: 13px;
    line-height: 1.6;
  }

  .library-layout {
    display: grid;
    grid-template-columns: minmax(220px, 0.7fr) minmax(0, 1.6fr);
    gap: 20px;
    align-items: start;
  }

  .profile-list,
  .profile-editor {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 20px;
    border: 1px solid var(--color-line);
    border-radius: 12px;
    background: rgba(23, 33, 27, 0.82);
  }

  .profile-item {
    display: flex;
    min-width: 0;
    flex-direction: column;
    gap: 5px;
    padding: 12px;
    border: 1px solid transparent;
    border-radius: 8px;
    background: transparent;
    text-align: left;
  }

  .profile-item.selected,
  .profile-item:hover {
    border-color: var(--color-line);
    background: rgba(255, 255, 255, 0.04);
  }

  .profile-item strong {
    color: var(--color-text);
    font-size: 13px;
  }

  .profile-item span {
    overflow: hidden;
    color: var(--color-muted);
    font-size: 11px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .editor-heading,
  .form-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .editor-heading {
    margin-bottom: 5px;
  }

  .eyebrow {
    margin: 0 0 5px;
    color: var(--color-gold);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.15em;
  }

  h2 {
    margin: 0;
    font-size: 21px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 7px;
    color: #cdd2c9;
    font-size: 12px;
  }

  .field input,
  .field textarea {
    width: 100%;
    padding: 10px 11px;
    border: 1px solid rgba(211, 218, 201, 0.14);
    border-radius: 7px;
    background: #111813;
    color: var(--color-text);
    font: inherit;
    line-height: 1.5;
    resize: vertical;
  }

  .field input:focus,
  .field textarea:focus {
    border-color: var(--color-gold);
    outline: none;
  }

  .primary-button {
    min-height: 38px;
    padding: 0 13px;
    border: 1px solid rgba(196, 169, 110, 0.45);
    border-radius: 7px;
    background: rgba(60, 91, 65, 0.36);
    color: var(--color-text);
    font-size: 12px;
  }

  .primary-button:disabled,
  .text-button:disabled {
    cursor: wait;
    opacity: 0.6;
  }

  .text-button {
    padding: 8px;
    border-radius: 6px;
    background: transparent;
    color: var(--color-muted);
    font-size: 12px;
  }

  .text-button:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--color-text);
  }

  .danger {
    color: #e5a49b;
  }

  .notice {
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

  @media (max-width: 700px) {
    .library-page {
      padding: 24px 16px;
    }

    .library-layout {
      grid-template-columns: 1fr;
    }
  }
</style>
