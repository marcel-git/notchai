<template>
    <article
        class="character-tile"
        role="button"
        :aria-label="`Chat with ${character.name}`"
        :aria-disabled="disabled"
        :tabindex="disabled ? -1 : 0"
        @click="selectCharacter"
        @keydown.enter.prevent="selectCharacter"
        @keydown.space.prevent="selectCharacter"
    >
        <div class="character-art" aria-hidden="true">
            <BIcon class="character-icon" icon="person" />
        </div>
        <div class="character-copy">
            <h2>{{ props.character.name }}</h2>
            <div class="character-description">
            <p>{{ props.character.description }}</p>
            </div>
        </div>
    </article>
</template>

<script setup lang="ts">
    import type { CharacterProfile } from '@/types/profiles';
    import BIcon from './BIcon.vue';

    const props = defineProps<{
        character: CharacterProfile
        disabled?: boolean
    }>()

    const emit = defineEmits<{
        select: []
    }>()

    function selectCharacter() {
        if (!props.disabled) emit('select')
    }
</script>

<style scoped>
    .character-tile {
        position: relative;
        display: flex;
        flex-direction: column;
        height: 420px;
        box-sizing: border-box;
        min-width: 0;
        overflow: hidden;
        border: 1px solid rgba(141, 178, 153, 0.2);
        border-radius: 13px;
        background: #102019;
        box-shadow:
            0 10px 26px rgba(0, 0, 0, 0.3),
            inset 0 0 0 1px rgba(187, 205, 188, 0.025);
        transition:
            transform 180ms ease,
            border-color 180ms ease,
            box-shadow 180ms ease;
    }

    .character-tile:hover {
        transform: translateY(-3px);
        border-color: rgba(139, 190, 153, 0.48);
        box-shadow:
            0 15px 34px rgba(0, 0, 0, 0.4),
            0 0 20px rgba(37, 104, 68, 0.16);
    }

    .character-tile:not([aria-disabled='true']) {
        cursor: pointer;
    }

    .character-tile[aria-disabled='true'] {
        cursor: not-allowed;
        opacity: 0.65;
    }

    .character-tile:focus-visible {
        outline: 2px solid rgba(139, 190, 153, 0.8);
        outline-offset: 3px;
    }

    .character-art {
        display: grid;
        width: 100%;
        min-height: 0;
        flex: 1 1 auto;
        place-items: center;
        overflow: hidden;
        background:
            radial-gradient(ellipse at 50% 38%, rgba(170, 197, 174, 0.2), transparent 43%),
            linear-gradient(155deg, #345344 0%, #1b3328 48%, #0a1711 100%);
        color: #d3ddcf;
    }

    .character-icon {
        width: 44%;
        height: 44%;
        filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.55));
        opacity: 0.92;
    }

    .character-copy {
        min-width: 0;
        height: 122px;
        box-sizing: border-box;
        flex: 0 0 122px;
        padding: 12px 13px 14px;
        background: linear-gradient(180deg, #14291f, #0c1b14);
    }

    .character-copy h2 {
        margin: 0 0 5px;
        overflow: hidden;
        color: #e5ebdf;
        font-size: 14px;
        font-weight: 700;
        line-height: 1.35;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .character-description {
        display: -webkit-box;
        overflow: hidden;
        color: #aebcaf;
        font-size: 11px;
        font-style: italic;
        line-height: 1.55;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 4;
    }

    .character-description p {
        margin: 0;
    }

    .character-tile:hover .character-description {
        position: absolute;
        z-index: 2;
        inset: 0;
        display: block;
        overflow-y: auto;
        box-sizing: border-box;
        padding: 18px 13px;
        border-radius: inherit;
        background: linear-gradient(
            180deg,
            rgba(7, 20, 14, 0.96) 0%,
            rgba(11, 31, 21, 0.9) 62%,
            rgba(14, 39, 26, 0.84) 100%
        );
        color: #dce7d9;
        -webkit-line-clamp: unset;
        scrollbar-color: rgba(162, 194, 165, 0.4) transparent;
        scrollbar-width: thin;
    }

    .character-tile:focus-visible .character-description {
        position: absolute;
        z-index: 2;
        inset: 0;
        display: block;
        overflow-y: auto;
        box-sizing: border-box;
        padding: 18px 13px;
        border-radius: inherit;
        background: linear-gradient(
            180deg,
            rgba(7, 20, 14, 0.96) 0%,
            rgba(11, 31, 21, 0.9) 62%,
            rgba(14, 39, 26, 0.84) 100%
        );
        color: #dce7d9;
        -webkit-line-clamp: unset;
        scrollbar-color: rgba(162, 194, 165, 0.4) transparent;
        scrollbar-width: thin;
    }

    @media (max-width: 580px) {
        .character-tile {
            height: 390px;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .character-tile {
            transition: none;
        }
    }

</style>