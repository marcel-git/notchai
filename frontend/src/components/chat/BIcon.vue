<script setup lang="ts">
import { computed } from 'vue'
import { iconNames } from 'bootstrap-icons-vue'

const props = defineProps<{
  icon: string
}>()

const iconComponents = new Map(
  iconNames.map((componentName) => [
    normalizeIconName(componentName.slice('BIcon'.length)),
    componentName,
  ]),
)

const iconComponent = computed(() => {
  const componentName = iconComponents.get(normalizeIconName(props.icon))
  if (!componentName) {
    throw new RangeError(`Unknown Bootstrap icon: "${props.icon}"`)
  }
  return componentName
})

function normalizeIconName(name: string) {
  return name.replaceAll('-', '').toLowerCase()
}
</script>

<template>
  <component :is="iconComponent" aria-hidden="true" focusable="false" />
</template>
