<template>
  <section class="start-screen" aria-labelledby="start-title">
    <div class="intro">
      <h1 id="start-title">
        <span
          ref="personaPicker"
          class="persona-picker"
          @keydown.esc.stop.prevent="closePersonaMenu(true)"
        >
          <button
            ref="personaTrigger"
            class="persona-trigger"
            type="button"
            aria-label="Choose the persona you will play"
            aria-haspopup="listbox"
            :aria-expanded="isPersonaMenuOpen"
            aria-controls="persona-options"
            :disabled="loading || isStarting"
            @click="isPersonaMenuOpen = !isPersonaMenuOpen"
          >
            {{ selectedPersonaName }}
            <span class="persona-caret" aria-hidden="true"></span>
          </button>
          <span
            v-if="isPersonaMenuOpen"
            id="persona-options"
            class="persona-options"
            role="listbox"
            aria-label="Choose a persona"
          >
            <button
              class="persona-option"
              type="button"
              role="option"
              :aria-selected="!personaId"
              @click="selectPersona(null)"
            >
              <span>Stranger</span>
              <span v-if="!personaId" class="persona-check" aria-hidden="true">✓</span>
            </button>
            <button
              v-for="persona in personas"
              :key="persona.id"
              class="persona-option"
              type="button"
              role="option"
              :aria-selected="persona.id === personaId"
              @click="selectPersona(persona.id)"
            >
              <span>{{ firstName(persona.name) }}</span>
              <span
                v-if="persona.id === personaId"
                class="persona-check"
                aria-hidden="true"
              >✓</span>
            </button>
          </span>
        </span>
        <span>, who would you like to chat with?</span>
      </h1>
    </div>

    <p v-if="error" class="start-error" role="alert">{{ error }}</p>

    <div class="character-tiles">
      <CharacterTile
        v-for="character in characters"
        :key="character.id"
        :character="character"
        :disabled="loading || isStarting"
        @select="start(character.id)"
      />
    </div>

    <p v-if="loading" class="loading-copy" role="status">Loading your profiles...</p>
    <p v-else-if="!characters.length" class="missing-profiles">
      Add at least one character before starting.
      <RouterLink v-if="!characters.length" to="/characters">Create a character</RouterLink>
    </p>
  </section>
</template>

<script setup lang="ts">
  import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
  import type { CharacterProfile, PersonaProfile } from '../../types/profiles'
  import CharacterTile from './CharacterTile.vue'

  const props = defineProps<{
    characters: CharacterProfile[]
    personas: PersonaProfile[]
    loading: boolean
    isStarting: boolean
    error: string
  }>()

  const emit = defineEmits<{
    start: [characterId: string, personaId: string | null]
  }>()

  const personaId = ref('')
  const isPersonaMenuOpen = ref(false)
  const personaPicker = ref<HTMLElement | null>(null)
  const personaTrigger = ref<HTMLButtonElement | null>(null)
  const selectedPersonaName = computed(() => {
    const selectedPersona = props.personas.find((persona) => persona.id === personaId.value)
    return selectedPersona ? firstName(selectedPersona.name) : 'Stranger'
  })

  watch(
    () => props.personas,
    (personas) => {
      if (!personas.some((item) => item.id === personaId.value)) {
        personaId.value = personas[0]?.id ?? ''
      }
    },
    { immediate: true },
  )

  onMounted(() => document.addEventListener('pointerdown', closeOnOutsidePointer))
  onUnmounted(() => document.removeEventListener('pointerdown', closeOnOutsidePointer))

  function start(characterId: string) {
    if (!characterId || props.loading || props.isStarting) return
    emit('start', characterId, personaId.value || null)
  }

  function firstName(name: string) {
    return name.trim().split(/\s+/, 1)[0] ?? ''
  }

  function selectPersona(id: string | null) {
    personaId.value = id ?? ''
    isPersonaMenuOpen.value = false
  }

  function closePersonaMenu(returnFocus = false) {
    isPersonaMenuOpen.value = false
    if (returnFocus) personaTrigger.value?.focus()
  }

  function closeOnOutsidePointer(event: PointerEvent) {
    if (event.target instanceof Node && !personaPicker.value?.contains(event.target)) {
      closePersonaMenu()
    }
  }
</script>

<style scoped>
  .character-tiles {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 220px), 1fr));
    align-items: start;
    gap: 14px;
    margin-bottom: 24px;
  }

  .start-screen {
    width: min(100% - 48px, 610px);
    margin: auto;
    padding: 38px 0;
  }

  .intro {
    margin-bottom: 24px;
    text-align: center;
  }

  .persona-picker {
    position: relative;
    display: inline-flex;
    vertical-align: baseline;
  }

  .persona-trigger {
    display: inline-flex;
    align-items: baseline;
    gap: 0.35em;
    max-width: 25vw;
    margin: 0;
    padding: 0;
    border: 0;
    border-bottom: 1px dotted rgba(196, 169, 110, 0.62);
    border-radius: 0;
    background: transparent;
    color: inherit;
    font: inherit;
    letter-spacing: inherit;
    line-height: inherit;
    cursor: pointer;
    transition:
      color 150ms ease,
      border-color 150ms ease;
  }

  .persona-trigger:hover:not(:disabled),
  .persona-trigger[aria-expanded='true'] {
    border-bottom-color: #c4a96e;
    color: #dce9d9;
  }

  .persona-trigger:focus-visible {
    border-radius: 3px;
    outline: 2px solid rgba(139, 190, 153, 0.42);
    outline-offset: 3px;
  }

  .persona-trigger:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .persona-caret {
    width: 0.32em;
    height: 0.32em;
    flex: 0 0 auto;
    border-right: 1px solid currentColor;
    border-bottom: 1px solid currentColor;
    color: #c4a96e;
    opacity: 0.85;
    transform: translateY(-0.12em) rotate(45deg);
    transition: transform 150ms ease;
  }

  .persona-trigger[aria-expanded='true'] .persona-caret {
    transform: translateY(0.05em) rotate(225deg);
  }

  .persona-options {
    position: absolute;
    z-index: 20;
    top: calc(100% + 12px);
    left: 50%;
    display: grid;
    width: max-content;
    min-width: 136px;
    max-width: min(220px, calc(100vw - 32px));
    max-height: min(280px, 50vh);
    gap: 3px;
    overflow-y: auto;
    padding: 6px;
    border: 1px solid rgba(144, 181, 151, 0.28);
    border-radius: 10px;
    background: rgba(12, 25, 18, 0.98);
    box-shadow:
      0 14px 32px rgba(0, 0, 0, 0.48),
      inset 0 1px 0 rgba(225, 238, 224, 0.035);
    backdrop-filter: blur(12px);
    transform: translateX(-50%);
  }

  .persona-option {
    display: flex;
    min-height: 36px;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 7px 10px;
    border: 1px solid transparent;
    border-radius: 6px;
    background: transparent;
    color: #c2cfc1;
    font: 500 12px/1.35 'DM Sans', 'Segoe UI', sans-serif;
    text-align: left;
    cursor: pointer;
    transition:
      background-color 120ms ease,
      border-color 120ms ease,
      color 120ms ease;
  }

  .persona-option:hover,
  .persona-option:focus-visible {
    border-color: rgba(143, 185, 150, 0.13);
    outline: none;
    background: rgba(52, 91, 62, 0.28);
    color: #f0f4ec;
  }

  .persona-option[aria-selected='true'] {
    color: #e0eadc;
  }

  .persona-check {
    color: #9ebc9f;
    font-size: 11px;
  }

  @media (prefers-reduced-motion: reduce) {
    .persona-trigger,
    .persona-caret,
    .persona-option {
      transition: none;
    }
  }

  .eyebrow {
    margin: 0 0 10px;
    color: var(--color-gold);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.18em;
  }

  h1 {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.32em;
    white-space: nowrap;
    margin: 0;
    color: #e5e5d9;
    font-family: 'Playfair Display', Georgia, serif;
    font-size: clamp(14px, 4.8vw, 30px);
    font-weight: 500;
    letter-spacing: -0.035em;
  }

  .intro>p:last-child {
    max-width: 430px;
    margin: 12px auto 0;
    color: #929c92;
    font-size: 12px;
    line-height: 1.7;
  }

  .missing-profiles,
  .loading-copy,
  .start-error {
    margin: 0;
    color: var(--color-muted);
    font-size: 11px;
    line-height: 1.6;
  }

  .missing-profiles a {
    color: var(--color-gold);
  }

  .start-error {
    margin-bottom: 12px;
    color: #e5a49b;
    text-align: center;
  }

  .loading-copy {
    text-align: center;
  }

  @media (max-width: 580px) {
    .start-screen {
      width: min(100% - 34px, 440px);
      padding: 28px 0;
    }

    .persona-trigger {
      max-width: 23vw;
    }
  }
</style>
