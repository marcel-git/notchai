<template>
  <ProfileLibrary
    title="Personas"
    singular="persona"
    description="Create the identity and role the user will act as in a conversation."
    summary-field="identity"
    :profiles="profiles"
    :fields="fields"
    :loading="loading"
    :error="error"
    :save-profile="saveProfile"
    :delete-profile="removeProfile"
    @profile-saved="saveToList"
    @profile-deleted="removeFromList"
  />
</template>

<script setup lang="ts">
  import { onMounted, ref } from 'vue'
  import ProfileLibrary from '../components/ProfileLibrary.vue'
  import {
    createPersona,
    deletePersona,
    listPersonas,
    updatePersona,
  } from '../services/profileApi'
  import type { PersonaFields, ProfileRecord } from '../types/profiles'

  const fields = [
    { key: 'identity', label: 'Identity', rows: 3, placeholder: 'Who is the user acting as?' },
    { key: 'appearance', label: 'Appearance', rows: 3, placeholder: 'Appearance and distinguishing details' },
    { key: 'background', label: 'Background', rows: 4, placeholder: 'Relevant history and context' },
    { key: 'behavior', label: 'Behavior', rows: 4, placeholder: 'How this persona acts and interacts' },
  ]

  const profiles = ref<ProfileRecord[]>([])
  const loading = ref(true)
  const error = ref('')

  onMounted(async () => {
    try {
      profiles.value = await listPersonas()
    } catch (cause: unknown) {
      error.value = cause instanceof Error ? cause.message : 'Could not load personas.'
    } finally {
      loading.value = false
    }
  })

  async function saveProfile(id: string | null, values: Record<string, string>): Promise<ProfileRecord> {
    const fields: PersonaFields = {
      name: values.name ?? '',
      identity: values.identity ?? '',
      appearance: values.appearance ?? '',
      background: values.background ?? '',
      behavior: values.behavior ?? '',
    }
    return id ? updatePersona(id, fields) : createPersona(fields)
  }

  async function removeProfile(id: string) {
    await deletePersona(id)
  }

  function saveToList(profile: ProfileRecord) {
    const existing = profiles.value.some((item) => item.id === profile.id)
    profiles.value = existing
      ? profiles.value.map((item) => (item.id === profile.id ? profile : item))
      : [profile, ...profiles.value]
  }

  function removeFromList(id: string) {
    profiles.value = profiles.value.filter((profile) => profile.id !== id)
  }
</script>
