<template>
  <div class="welcome">
    <h1>Well hello there!</h1>
    <p class="welcome-description">What would you like to write about?</p>
  </div>
</template>

<script setup lang="ts">
  const emit = defineEmits<{
    selectSuggestion: [prompt: string]
  }>()
</script>

<style scoped>
.welcome {
  width: min(100% - 48px, 700px);
  flex: 0 0 auto;
  margin: auto;
  padding: 44px 0 36px;
  text-align: center;
}

.welcome h1 {
  margin: 0;
  color: #e5e5d9;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: clamp(29px, 3vw, 39px);
  font-weight: 500;
  letter-spacing: -0.035em;
}

.welcome-description {
  margin: 12px 0 37px;
  color: #929c92;
  font-size: 12px;
}

@media (max-width: 580px) {
  .welcome {
    width: min(100% - 34px, 440px);
    padding-top: 38px;
    padding-bottom: 28px;
  }

  .welcome h1 {
    font-size: 30px;
  }

  .welcome-description {
    margin-bottom: 27px;
  }
}
</style>
