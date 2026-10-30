import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import Characters from '../views/Characters.vue'
import Personas from '../views/Personas.vue'
import Settings from '../views/Settings.vue'
import Guidance from '../views/Guidance.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/characters',
      name: 'characters',
      component: Characters,
    },
    {
      path: '/personas',
      name: 'personas',
      component: Personas,
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings,
    },
    {
      path: '/guidance',
      name: 'guidance',
      component: Guidance,
    },
  ],
})

export default router
