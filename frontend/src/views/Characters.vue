<template>
  <ProfileLibrary
    title="Characters"
    singular="character"
    description="Create the role the agent will play in a conversation."
    summary-field="description"
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
    createCharacter,
    deleteCharacter,
    listCharacters,
    updateCharacter,
  } from '../services/profileApi'
  import type { CharacterFields, ProfileRecord } from '../types/profiles'

  const fields = [
    { key: 'description', label: 'Description', rows: 3, placeholder: 'Who is this character?' },
    { key: 'personality', label: 'Personality', rows: 3, placeholder: 'How does the character think and speak?' },
    { key: 'background', label: 'Background', rows: 4, placeholder: 'Relevant history and context' },
    {
      key: 'custom_instructions',
      label: 'Custom instructions',
      rows: 4,
      placeholder: 'Specific directions for the agent playing this character',
    },
  ]

  const profiles = ref<ProfileRecord[]>([])
  const loading = ref(true)
  const error = ref('')

  onMounted(async () => {
    try {
      profiles.value = await listCharacters()
    } catch (cause: unknown) {
      error.value = cause instanceof Error ? cause.message : 'Could not load characters.'
    } finally {
      loading.value = false
    }
  })

  async function saveProfile(id: string | null, values: Record<string, string>): Promise<ProfileRecord> {
    const fields: CharacterFields = {
      name: values.name ?? '',
      description: values.description ?? '',
      personality: values.personality ?? '',
      background: values.background ?? '',
      custom_instructions: values.custom_instructions ?? '',
    }
    return id ? updateCharacter(id, fields) : createCharacter(fields)
  }

  async function removeProfile(id: string) {
    await deleteCharacter(id)
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
