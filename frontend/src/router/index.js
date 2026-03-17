import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/home',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/formulario',
      name: 'formulario',
      component: () => import('../views/OnboardingView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/cadastro',
      name: 'cadastro',
      component: () => import('../views/CadastroView.vue'),
    },
    {
      path: '/transacoes',
      name: 'transacoes',
      component: () => import('../views/TransacoesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/investimentos',
      name: 'investimentos',
      component: () => import('../views/InvestimentosView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/configuracoes',
      name: 'configuracoes',
      component: () => import('../views/ConfiguracoesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/relatorios',
      name: 'relatorios',
      component: () => import('../views/RelatoriosView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/gastos-futuros',
      name: 'gastos-futuros',
      component: () => import('../views/GastosFuturosView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/metas',
      name: 'metas',
      component: () => import('../views/MetasView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/cartoes',
      name: 'cartoes',
      component: () => import('../views/CartoesView.vue'),
      meta: { requiresAuth: true }
    },
  ],
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login' })
  } else if ((to.name === 'login' || to.name === 'cadastro') && isAuthenticated) {
    next({ name: 'home' })
  } else {
    next()
  } 
})

export default router