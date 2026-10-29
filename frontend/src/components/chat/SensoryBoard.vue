<template>
  <div
    v-if="open"
    class="overlay"
    @click.self="close"
    @keydown.esc.stop.prevent="close"
  >
    <section
      ref="dialog"
      class="dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="sensory-board-title"
      tabindex="-1"
    >
      <header class="dialog-header">
        <div>
          <h2 id="sensory-board-title">Sensory board</h2>
          <p>A little collection of visual and clicky fidgets.</p>
        </div>
        <button
          ref="closeButton"
          class="close-button"
          type="button"
          aria-label="Close sensory board"
          @click="close"
        >
          ×
        </button>
      </header>

      <div class="board">
        <section class="board-card surface-card">
          <div class="card-heading">
            <h3>Soft patterns</h3>
            <span>Tap to change</span>
          </div>
          <button
            class="pattern-surface"
            :class="`pattern-${pattern}`"
            type="button"
            :aria-label="`Change surface pattern. Current pattern: ${pattern}`"
            @click="cyclePattern"
          >
            <span class="surface-orb"></span>
          </button>
        </section>

        <section class="board-card">
          <div class="card-heading">
            <h3>Quiet switches</h3>
            <span>Click to toggle</span>
          </div>
          <div class="switch-grid">
            <button
              v-for="(enabled, index) in switches"
              :key="index"
              class="switch-tile"
              :class="{ 'switch-on': enabled }"
              type="button"
              role="switch"
              :aria-checked="enabled"
              :aria-label="`Quiet switch ${index + 1}`"
              @click="toggleSwitch(index)"
            >
              <span class="switch-track"><span class="switch-knob"></span></span>
            </button>
          </div>
        </section>

        <section class="board-card">
          <div class="card-heading">
            <h3>Fidget beads</h3>
            <span>Press and release</span>
          </div>
          <div class="bead-row">
            <button
              v-for="(pressed, index) in beads"
              :key="index"
              class="bead"
              :class="{ 'bead-pressed': pressed }"
              type="button"
              :aria-pressed="pressed"
              :aria-label="`Fidget bead ${index + 1}`"
              @click="toggleBead(index)"
            >
              <span></span>
            </button>
          </div>
        </section>

        <section class="board-card">
          <div class="card-heading">
            <h3>Breathing pebble</h3>
            <span>{{ isBreathing ? 'Breathe with the glow' : 'Start whenever you like' }}</span>
          </div>
          <button
            class="breathing-control"
            type="button"
            :aria-pressed="isBreathing"
            :aria-label="isBreathing ? 'Pause breathing pebble' : 'Start breathing pebble'"
            @click="isBreathing = !isBreathing"
          >
            <span class="breathing-orb" :class="{ breathing: isBreathing }"></span>
            <span>{{ isBreathing ? 'Pause' : 'Start' }}</span>
          </button>
        </section>

        <section class="board-card slider-card">
          <div class="card-heading">
            <h3>Slow slider</h3>
            <span>{{ sliderValue }}%</span>
          </div>
          <span
            class="slider-glow"
            :style="{ left: `${sliderValue}%` }"
            aria-hidden="true"
          ></span>
          <input
            v-model.number="sliderValue"
            class="fidget-slider"
            type="range"
            min="0"
            max="100"
            aria-label="Slow fidget slider"
          />
          <div class="slider-ends"><span>←</span><span>→</span></div>
        </section>
      </div>

      <footer class="dialog-footer">
        <p>Visual and touch fidgets only. No sound or flashing effects.</p>
        <button class="reset-button" type="button" @click="resetBoard">Reset</button>
      </footer>
    </section>
  </div>
</template>

<script setup lang="ts">
  import { nextTick, ref, watch } from 'vue'

  const props = defineProps<{
    open: boolean
  }>()

  const emit = defineEmits<{
    close: []
  }>()

  const dialog = ref<HTMLElement | null>(null)
  const closeButton = ref<HTMLButtonElement | null>(null)
  const switches = ref([false, false, false, false])
  const beads = ref([false, false, false, false, false, false])
  const pattern = ref<'waves' | 'dots' | 'stripes'>('waves')
  const sliderValue = ref(50)
  const isBreathing = ref(false)

  watch(
    () => props.open,
    async (open) => {
      if (!open) return
      await nextTick()
      dialog.value?.focus()
    },
  )

  function close() {
    emit('close')
  }

  function toggleSwitch(index: number) {
    switches.value[index] = !switches.value[index]
  }

  function toggleBead(index: number) {
    beads.value[index] = !beads.value[index]
  }

  function cyclePattern() {
    const patterns = ['waves', 'dots', 'stripes'] as const
    const currentIndex = patterns.indexOf(pattern.value)
    pattern.value = patterns[(currentIndex + 1) % patterns.length] ?? 'waves'
  }

  function resetBoard() {
    switches.value = switches.value.map(() => false)
    beads.value = beads.value.map(() => false)
    pattern.value = 'waves'
    sliderValue.value = 50
    isBreathing.value = false
  }
</script>

<style scoped>
  .overlay {
    position: fixed;
    z-index: 30;
    inset: 0;
    display: grid;
    place-items: center;
    padding: 20px;
    background: rgba(4, 8, 5, 0.78);
    backdrop-filter: blur(4px);
  }

  .dialog {
    display: flex;
    width: min(660px, 100%);
    max-height: min(86vh, 760px);
    flex-direction: column;
    overflow: hidden;
    border: 1px solid rgba(211, 218, 201, 0.16);
    border-radius: 13px;
    background:
      radial-gradient(ellipse at 82% 0%, rgba(87, 118, 79, 0.12), transparent 44%),
      #17211b;
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.48);
  }

  .dialog:focus {
    outline: none;
  }

  .dialog-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    padding: 20px 22px 16px;
    border-bottom: 1px solid var(--color-line);
  }

  .dialog-header h2 {
    margin: 0;
    color: #e5e5d9;
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 22px;
    font-weight: 500;
  }

  .dialog-header p {
    margin: 6px 0 0;
    color: var(--color-muted);
    font-size: 11px;
  }

  .close-button {
    width: 30px;
    height: 30px;
    border-radius: 6px;
    background: transparent;
    color: var(--color-muted);
    font-size: 23px;
    cursor: pointer;
  }

  .close-button:hover {
    background: rgba(255, 255, 255, 0.06);
    color: var(--color-text);
  }

  .board {
    display: grid;
    min-height: 0;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 11px;
    overflow-y: auto;
    padding: 16px 22px;
  }

  .board-card {
    display: flex;
    min-height: 126px;
    flex-direction: column;
    justify-content: space-between;
    gap: 14px;
    padding: 13px;
    border: 1px solid rgba(211, 218, 201, 0.1);
    border-radius: 9px;
    background: rgba(12, 20, 15, 0.62);
  }

  .slider-card {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    border-color: rgba(79, 156, 142, 0.2);
  }

  .slider-card > :not(.slider-glow) {
    position: relative;
    z-index: 1;
  }

  .slider-glow {
    position: absolute;
    z-index: 0;
    top: 66%;
    left: 50%;
    width: 116px;
    height: 58px;
    border-radius: 43% 57% 62% 38% / 54% 43% 57% 46%;
    background:
      radial-gradient(ellipse at 38% 48%, rgba(54, 222, 201, 0.42), transparent 64%),
      radial-gradient(ellipse at 72% 54%, rgba(31, 155, 146, 0.27), transparent 70%);
    filter: blur(17px);
    opacity: 0.62;
    pointer-events: none;
    transform: translate(-50%, -50%);
    animation: slider-glow-drift 7s ease-in-out infinite;
  }

  @keyframes slider-glow-drift {
    0%,
    100% {
      border-radius: 43% 57% 62% 38% / 54% 43% 57% 46%;
      opacity: 0.48;
      margin-left: -5px;
      scale: 0.92;
    }

    50% {
      border-radius: 61% 39% 42% 58% / 40% 62% 38% 60%;
      opacity: 0.82;
      margin-left: 6px;
      scale: 1.08;
    }
  }

  .slider-card:hover .slider-glow,
  .slider-card:focus-within .slider-glow {
    opacity: 0.95;
    filter: blur(20px);
  }

  .slider-card:hover {
    border-color: rgba(75, 204, 190, 0.38);
    box-shadow:
      0 0 26px 4px rgba(35, 190, 176, 0.16),
      inset 0 0 20px rgba(35, 190, 176, 0.045);
  }

  .card-heading {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 8px;
  }

  .card-heading h3 {
    margin: 0;
    color: #d7ddcf;
    font-size: 11px;
    font-weight: 500;
  }

  .card-heading > span {
    color: #829083;
    font-size: 9px;
    text-align: right;
  }

  .pattern-surface {
    position: relative;
    display: grid;
    min-height: 72px;
    place-items: center;
    overflow: hidden;
    border: 1px solid rgba(139, 166, 132, 0.2);
    border-radius: 7px;
    background-color: #1b2b20;
    cursor: pointer;
    transition:
      border-color 180ms ease,
      background-color 180ms ease;
  }

  .pattern-surface:hover {
    border-color: rgba(75, 204, 190, 0.48);
  }

  .pattern-surface:hover,
  .pattern-surface:focus-visible,
  .switch-tile:hover,
  .switch-tile:focus-visible,
  .bead:hover,
  .bead:focus-visible,
  .breathing-control:hover,
  .breathing-control:focus-visible,
  .reset-button:hover,
  .reset-button:focus-visible {
    box-shadow:
      0 0 28px 5px rgba(35, 190, 176, 0.24),
      0 0 46px 8px rgba(35, 190, 176, 0.1),
      inset 0 0 18px rgba(35, 190, 176, 0.08);
  }

  .switch-tile:hover,
  .switch-tile:focus-visible,
  .breathing-control:hover,
  .breathing-control:focus-visible {
    border-color: rgba(75, 204, 190, 0.38);
  }

  .bead:hover,
  .bead:focus-visible {
    border-color: rgba(75, 204, 190, 0.55);
  }

  .pattern-waves {
    background-image: repeating-radial-gradient(
      ellipse at 50% 120%,
      transparent 0 10px,
      rgba(139, 166, 132, 0.14) 11px 12px,
      transparent 13px 22px
    );
  }

  .pattern-dots {
    background-image: radial-gradient(rgba(196, 169, 110, 0.3) 1px, transparent 1.5px);
    background-size: 13px 13px;
  }

  .pattern-stripes {
    background-image: repeating-linear-gradient(
      135deg,
      transparent 0 9px,
      rgba(139, 166, 132, 0.14) 10px 11px,
      transparent 12px 20px
    );
  }

  .surface-orb {
    width: 28px;
    height: 28px;
    border: 1px solid rgba(220, 207, 165, 0.6);
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #a4b99a, #54785a 62%, #294231);
    box-shadow:
      0 0 14px rgba(120, 166, 124, 0.2),
      inset 0 1px 3px rgba(255, 255, 255, 0.3);
    transition: transform 260ms ease;
  }

  .pattern-surface:active .surface-orb {
    transform: scale(0.82);
  }

  .switch-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
  }

  .switch-tile {
    display: grid;
    min-height: 45px;
    place-items: center;
    border: 1px solid rgba(211, 218, 201, 0.09);
    border-radius: 7px;
    background: rgba(255, 255, 255, 0.025);
    cursor: pointer;
  }

  .switch-track {
    display: flex;
    width: 29px;
    height: 16px;
    align-items: center;
    padding: 2px;
    border-radius: 10px;
    background: #29352c;
    transition: background-color 160ms ease;
  }

  .switch-knob {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #a0a99c;
    transition:
      transform 160ms ease,
      background-color 160ms ease;
  }

  .switch-on .switch-track {
    background: #456b4b;
  }

  .switch-on .switch-knob {
    background: #d1c08e;
    transform: translateX(13px);
  }

  .bead-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    padding: 4px 2px;
  }

  .bead {
    display: grid;
    width: 33px;
    height: 33px;
    place-items: center;
    border: 1px solid rgba(196, 169, 110, 0.28);
    border-radius: 50%;
    background: linear-gradient(145deg, #334a37, #1a2a1e);
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.24);
    cursor: pointer;
    transition:
      transform 120ms ease,
      box-shadow 120ms ease,
      background-color 120ms ease;
  }

  .bead span {
    width: 9px;
    height: 9px;
    border: 1px solid rgba(220, 207, 165, 0.35);
    border-radius: 50%;
    background: rgba(196, 169, 110, 0.44);
  }

  .bead-pressed {
    box-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.38);
    transform: translateY(2px) scale(0.96);
  }

  .bead-pressed span {
    background: #c4a96e;
  }

  .breathing-control {
    display: flex;
    min-height: 62px;
    align-items: center;
    justify-content: center;
    gap: 12px;
    border: 1px solid rgba(211, 218, 201, 0.08);
    border-radius: 7px;
    background: rgba(255, 255, 255, 0.02);
    color: #aab5a8;
    font-size: 10px;
    cursor: pointer;
  }

  .breathing-orb {
    width: 22px;
    height: 22px;
    border: 1px solid rgba(196, 169, 110, 0.55);
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #9db291, #46664b 72%);
    box-shadow: 0 0 9px rgba(119, 158, 111, 0.18);
  }

  .breathing-orb.breathing {
    animation: breathe 6s ease-in-out infinite;
  }

  @keyframes breathe {
    0%,
    100% {
      box-shadow: 0 0 8px rgba(119, 158, 111, 0.18);
      transform: scale(0.82);
    }

    50% {
      box-shadow: 0 0 22px rgba(119, 158, 111, 0.46);
      transform: scale(1.25);
    }
  }

  .fidget-slider {
    width: 100%;
    accent-color: #9bab83;
  }

  .fidget-slider::-webkit-slider-thumb {
    transition: box-shadow 160ms ease;
  }

  .fidget-slider:hover::-webkit-slider-thumb,
  .fidget-slider:focus-visible::-webkit-slider-thumb {
    box-shadow: 0 0 13px 4px rgba(35, 190, 176, 0.38);
  }

  .fidget-slider::-moz-range-thumb {
    transition: box-shadow 160ms ease;
  }

  .fidget-slider:hover::-moz-range-thumb,
  .fidget-slider:focus-visible::-moz-range-thumb {
    box-shadow: 0 0 13px 4px rgba(35, 190, 176, 0.38);
  }

  .slider-ends {
    display: flex;
    justify-content: space-between;
    color: #748176;
    font-size: 10px;
  }

  .dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 22px 16px;
    border-top: 1px solid var(--color-line);
  }

  .dialog-footer p {
    margin: 0;
    color: #829083;
    font-size: 9px;
  }

  .reset-button {
    min-height: 30px;
    padding: 0 10px;
    border: 1px solid rgba(211, 218, 201, 0.13);
    border-radius: 6px;
    background: transparent;
    color: #aeb6aa;
    font-size: 10px;
    cursor: pointer;
  }

  .reset-button:hover {
    border-color: rgba(196, 169, 110, 0.4);
    color: #e0d4ae;
  }

  button:focus-visible,
  input:focus-visible {
    outline: 2px solid rgba(196, 169, 110, 0.55);
    outline-offset: 2px;
  }

  @media (max-width: 560px) {
    .overlay {
      padding: 10px;
    }

    .dialog-header {
      padding: 16px 16px 13px;
    }

    .board {
      grid-template-columns: 1fr;
      gap: 8px;
      padding: 12px 16px;
    }

    .board-card {
      min-height: 112px;
    }

    .dialog-footer {
      align-items: flex-start;
      padding: 10px 16px 14px;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      scroll-behavior: auto !important;
      transition-duration: 0.01ms !important;
    }
  }
</style>
