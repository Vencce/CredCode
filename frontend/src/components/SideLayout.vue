<script setup>
import { ref, onMounted, reactive, computed, onUnmounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const sidebarOpen = ref(true)
const isMobileMenuOpen = ref(false)
const theme = ref('light')

const userData = reactive({
  name: 'Usuário'
})

const upcomingExpenses = ref([])
const showNotifications = ref(false)
const notificationRef = ref(null)

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

const isActive = (path) => {
  return route.path === path
}

const toggleTheme = () => {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
  localStorage.setItem('theme', theme.value)
  document.documentElement.setAttribute('data-theme', theme.value)
  window.dispatchEvent(new Event('theme-changed'))
}

const fetchWithAuth = async (url, options = {}) => {
  let token = localStorage.getItem('access_token')
  let headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  }
  
  let response = await fetch(url, { ...options, headers })
  
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      try {
        const refreshResponse = await fetch('http://localhost:8000/api/auth/refresh/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: refreshToken })
        })
        
        if (refreshResponse.ok) {
          const data = await refreshResponse.json()
          localStorage.setItem('access_token', data.access)
          headers['Authorization'] = `Bearer ${data.access}`
          response = await fetch(url, { ...options, headers })
        } else {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('has_profile')
          router.push('/')
        }
      } catch (e) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('has_profile')
        router.push('/')
      }
    } else {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('has_profile')
      router.push('/')
    }
  }
  return response
}

const fetchUpcomingExpenses = async () => {
  try {
    const res = await fetchWithAuth('http://localhost:8000/api/finances/expenses/')
    if (res.ok) {
      const expenses = await res.json()
      const now = new Date()
      now.setHours(0,0,0,0)
      
      const limiar = new Date()
      limiar.setDate(now.getDate() + 7)
      limiar.setHours(23,59,59,999)

      upcomingExpenses.value = expenses
        .map(e => {
          const parts = e.date.split('-')
          let cleanDesc = e.description
          if (cleanDesc.startsWith('[')) {
            const closingBracket = cleanDesc.indexOf(']')
            if (closingBracket !== -1) {
              cleanDesc = cleanDesc.substring(closingBracket + 1).trim()
            }
          }
          return {
            ...e,
            rawDate: new Date(parseInt(parts[0]), parseInt(parts[1])-1, parseInt(parts[2].substring(0, 2))),
            cleanDesc: cleanDesc
          }
        })
        .filter(e => e.amount < 0 && e.rawDate > now && e.rawDate <= limiar)
        .sort((a, b) => a.rawDate - b.rawDate)
    }
  } catch (e) {
  }
}

const hasNotifications = computed(() => upcomingExpenses.value.length > 0)

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Math.abs(value))
}

const formatDateShort = (rawDate) => {
  return rawDate.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

const handleClickOutside = (event) => {
  if (notificationRef.value && !notificationRef.value.contains(event.target)) {
    showNotifications.value = false
  }
}

const handleLogout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('has_profile')
  router.push('/')
}

onMounted(async () => {
  const savedTheme = localStorage.getItem('theme') || 'light'
  theme.value = savedTheme
  document.documentElement.setAttribute('data-theme', savedTheme)

  document.addEventListener('click', handleClickOutside)

  const token = localStorage.getItem('access_token')
  if (token) {
    fetchUpcomingExpenses()
    try {
      const response = await fetchWithAuth('http://localhost:8000/api/finances/profile/')
      if (response.ok) {
        const data = await response.json()
        if (data.full_name) {
          userData.name = data.full_name
        }
      }
    } catch (error) {
    }
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="app-layout">
    <div v-if="isMobileMenuOpen" class="mobile-overlay" @click="closeMobileMenu"></div>

    <aside :class="['sidebar', { closed: !sidebarOpen, 'mobile-open': isMobileMenuOpen }]">
      <div class="sidebar-brand">
        <h2 v-if="sidebarOpen" class="main-logo">CRED<span>CODE</span></h2>
        <h2 v-else class="main-logo-collapsed">C<span>C</span></h2>
      </div>
      
      <nav class="sidebar-nav">
        <RouterLink to="/home" class="nav-item" :class="{ active: isActive('/home') }" @click="closeMobileMenu">
          <span class="icon">📊</span>
          <span v-if="sidebarOpen" class="nav-text">Dashboard</span>
        </RouterLink>

        <RouterLink to="/transacoes" class="nav-item" :class="{ active: isActive('/transacoes') }" @click="closeMobileMenu">
          <span class="icon">💸</span>
          <span v-if="sidebarOpen" class="nav-text">Transações</span>
        </RouterLink>

        <RouterLink to="/gastos-futuros" class="nav-item" :class="{ active: isActive('/gastos-futuros') }" @click="closeMobileMenu">
          <span class="icon">📅</span>
          <span v-if="sidebarOpen" class="nav-text">Gastos Futuros</span>
        </RouterLink>

        <RouterLink to="/metas" class="nav-item" :class="{ active: isActive('/metas') }" @click="closeMobileMenu">
          <span class="icon">🎯</span>
          <span v-if="sidebarOpen" class="nav-text">Metas</span>
        </RouterLink>

        <RouterLink to="/cartoes" class="nav-item" :class="{ active: isActive('/cartoes') }" @click="closeMobileMenu">
          <span class="icon">💳</span>
          <span v-if="sidebarOpen" class="nav-text">Cartões</span>
        </RouterLink>
        
        <RouterLink to="/investimentos" class="nav-item" :class="{ active: isActive('/investimentos') }" @click="closeMobileMenu">
          <span class="icon">💰</span>
          <span v-if="sidebarOpen" class="nav-text">Investimentos</span>
        </RouterLink>

        <RouterLink to="/relatorios" class="nav-item" :class="{ active: isActive('/relatorios') }" @click="closeMobileMenu">
          <span class="icon">📈</span>
          <span v-if="sidebarOpen" class="nav-text">Relatórios</span>
        </RouterLink>

        <RouterLink to="/configuracoes" class="nav-item" :class="{ active: isActive('/configuracoes') }" @click="closeMobileMenu">
          <span class="icon">⚙️</span>
          <span v-if="sidebarOpen" class="nav-text">Configurações</span>
        </RouterLink>
      </nav>
      
      <button class="toggle-btn" @click="toggleSidebar">
        <span v-if="sidebarOpen">◀</span>
        <span v-else>▶</span>
      </button>
    </aside>

    <div class="main-wrapper">
      <header class="top-header">
        <div class="topbar-left">
          <button class="btn-hamburguer" @click="toggleMobileMenu">
            <span>☰</span>
          </button>
          
          <div class="breadcrumb" v-if="!isMobileMenuOpen">
            <span>Terminal Financeiro</span>
          </div>
        </div>

        <div class="topbar-right">

          <div class="notification-container" ref="notificationRef">
            <button class="icon-btn notification-btn" @click="showNotifications = !showNotifications">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
              <span v-if="hasNotifications" class="notification-badge">{{ upcomingExpenses.length }}</span>
            </button>

            <div v-if="showNotifications" class="notification-dropdown">
              <div class="dropdown-header">
                <h3>Vencimentos Próximos</h3>
                <span class="subtitle">Próximos 7 dias</span>
              </div>
              <div v-if="!hasNotifications" class="dropdown-empty">
                🎉 Nenhuma conta vencendo logo.
              </div>
              <div v-else class="dropdown-list">
                <div v-for="exp in upcomingExpenses" :key="exp.id" class="dropdown-item">
                  <div class="item-icon">💸</div>
                  <div class="item-content">
                    <span class="item-title fw-600">{{ exp.cleanDesc }}</span>
                    <span class="item-date">Vence {{ formatDateShort(exp.rawDate) }}</span>
                  </div>
                  <div class="item-amount negative fw-700">
                    {{ formatCurrency(exp.amount) }}
                  </div>
                </div>
              </div>
              <div class="dropdown-footer">
                <RouterLink to="/gastos-futuros" @click="showNotifications = false">Ver planejamento completo</RouterLink>
              </div>
            </div>
          </div>

          <button @click="toggleTheme" class="icon-btn btn-theme">
            <svg v-if="theme === 'light'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
          </button>

          <div class="user-profile-header">
            <div class="avatar-header">{{ userData.name.charAt(0).toUpperCase() }}</div>
            <span class="user-name-header">{{ userData.name }}</span>
          </div>
          
          <button @click="handleLogout" class="btn-logout-header">
            Sair
          </button>
        </div>
      </header>
      
      <main class="content-body">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<style>
:root {
  --bg-main: #f8fafc;
  --bg-card: #ffffff;
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --border-color: #f1f5f9;
  --border-input: #cbd5e1;
  --sidebar-bg: #0f172a;
  --sidebar-text: #94a3b8;
  --sidebar-text-hover: #f8fafc;
  --topbar-bg: #ffffff;
  --input-bg: #f8fafc;
  --positive-bg: #ecfdf5;
  --negative-bg: #fef2f2;
  --neutral-bg: #f8fafc;
  --shadow-sm: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.02);
  --shadow-lg: 0 20px 25px -5px rgba(15, 23, 42, 0.05);
  --logo-text: white;
}

[data-theme="dark"] {
  --bg-main: #020617;
  --bg-card: #0f172a;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --border-color: #1e293b;
  --border-input: #334155;
  --sidebar-bg: #020617;
  --sidebar-text: #94a3b8;
  --sidebar-text-hover: #f8fafc;
  --topbar-bg: #020617;
  --input-bg: #1e293b;
  --positive-bg: rgba(16, 185, 129, 0.15);
  --negative-bg: rgba(239, 68, 68, 0.15);
  --neutral-bg: rgba(148, 163, 184, 0.1);
  --shadow-sm: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  --logo-text: white;
}

body {
  background-color: var(--bg-main);
  color: var(--text-primary);
  transition: background-color 0.3s, color 0.3s;
}
</style>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-main);
  font-family: 'Inter', sans-serif;
  overflow: hidden;
  transition: background-color 0.3s;
}

.sidebar {
  width: 280px;
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1), left 0.4s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.3s;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.sidebar.closed {
  width: 90px;
}

.sidebar-brand {
  padding: 35px 20px;
  text-align: center;
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.main-logo {
  font-weight: 900;
  font-size: 2rem;
  margin: 0;
  letter-spacing: -1.5px;
  color: var(--logo-text);
}

.main-logo span {
  color: #f7b500;
}

.main-logo-collapsed {
  font-weight: 900;
  font-size: 2rem;
  margin: 0;
  color: #f7b500;
  letter-spacing: -1px;
}

.main-logo-collapsed span {
  color: var(--logo-text);
}

.sidebar-nav {
  flex: 1;
  padding: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
}

.sidebar-nav::-webkit-scrollbar {
  display: none;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  margin: 0 16px;
  border-radius: 14px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.nav-item:hover:not(.active) {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--sidebar-text-hover);
  transform: translateX(4px);
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(247, 181, 0, 0.15) 0%, rgba(247, 181, 0, 0.05) 100%);
  color: #f7b500;
  box-shadow: inset 2px 0 0 0 #f7b500;
}

.sidebar.closed .nav-item {
  justify-content: center;
  padding: 14px;
  margin: 0 12px;
}

.sidebar.closed .nav-item:hover:not(.active) {
  transform: translateY(-2px);
}

.icon {
  margin-right: 16px;
  font-size: 1.3rem;
  transition: margin 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar.closed .icon {
  margin-right: 0;
  font-size: 1.5rem;
}

.toggle-btn {
  position: absolute;
  right: -16px;
  top: 100px;
  background-color: #f7b500;
  color: #0f172a;
  border: 4px solid var(--bg-main);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 101;
  box-shadow: var(--shadow-sm);
  font-size: 0.7rem;
  font-weight: 900;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toggle-btn:hover {
  transform: scale(1.15);
  background-color: #e6a800;
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.top-header {
  background-color: var(--topbar-bg);
  height: 90px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  z-index: 90;
  transition: background-color 0.3s, border-color 0.3s;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.breadcrumb {
  color: var(--text-primary);
  font-weight: 800;
  font-size: 1.25rem;
  letter-spacing: -0.5px;
  transition: color 0.3s;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.icon-btn {
  background-color: var(--bg-main);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  background-color: var(--border-color);
  color: var(--text-primary);
  transform: translateY(-2px);
}

.notification-container {
  position: relative;
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background-color: #ef4444;
  color: white;
  font-size: 0.7rem;
  font-weight: 700;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--topbar-bg);
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 15px);
  right: -50px;
  width: 320px;
  background-color: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  animation: dropdownIn 0.2s ease-out;
}

@keyframes dropdownIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.dropdown-header {
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-main);
}

.dropdown-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.dropdown-header .subtitle {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.dropdown-empty {
  padding: 30px 20px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.dropdown-list {
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-list::-webkit-scrollbar {
  width: 6px;
}

.dropdown-list::-webkit-scrollbar-thumb {
  background-color: var(--border-input);
  border-radius: 4px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.2s;
}

.dropdown-item:hover {
  background-color: var(--bg-main);
}

.dropdown-item:last-child {
  border-bottom: none;
}

.item-icon {
  font-size: 1.2rem;
}

.item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.item-title {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.item-date {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.item-amount {
  font-size: 0.95rem;
}

.negative { color: #dc2626; }
.fw-600 { font-weight: 600; }
.fw-700 { font-weight: 700; }

.dropdown-footer {
  padding: 12px;
  text-align: center;
  background-color: var(--bg-main);
  border-top: 1px solid var(--border-color);
}

.dropdown-footer a {
  font-size: 0.85rem;
  color: #f7b500;
  text-decoration: none;
  font-weight: 600;
}

.dropdown-footer a:hover {
  text-decoration: underline;
}

.user-profile-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 6px 14px 6px 6px;
  background-color: var(--bg-main);
  border-radius: 30px;
  border: 1px solid var(--border-color);
  transition: background-color 0.3s, border-color 0.3s;
}

.avatar-header {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f7b500 0%, #e6a800 100%);
  color: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.2rem;
  box-shadow: 0 4px 10px rgba(247, 181, 0, 0.3);
}

.user-name-header {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 0.95rem;
  transition: color 0.3s;
}

.btn-logout-header {
  background-color: rgba(225, 29, 72, 0.1);
  color: #e11d48;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-logout-header:hover {
  background-color: rgba(225, 29, 72, 0.2);
  transform: translateY(-2px);
}

.btn-hamburguer {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-primary);
  padding: 8px;
  font-size: 1.6rem;
  border-radius: 8px;
  background-color: var(--bg-main);
}

.content-body {
  padding: 40px;
  flex: 1;
}

@media (max-width: 1024px) {
  .toggle-btn {
    display: none; 
  }

  .sidebar {
    position: fixed;
    height: 100%;
    left: -300px;
    width: 280px !important;
  }

  .sidebar.mobile-open {
    left: 0;
  }

  .btn-hamburguer {
    display: block;
  }

  .mobile-overlay {
    position: fixed;
    top: 0; 
    left: 0; 
    width: 100%; 
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    z-index: 99;
  }
  
  .top-header {
    padding: 0 24px;
    height: 80px;
  }
  
  .content-body {
    padding: 24px;
  }
}

@media (max-width: 480px) {
  .user-profile-header {
    background-color: transparent;
    border: none;
    padding: 0;
  }
  .user-name-header {
    display: none;
  }
  .btn-logout-header {
    padding: 10px 16px;
  }
  .topbar-right {
    gap: 16px;
  }
  .notification-dropdown {
    width: 280px;
    right: -40px;
  }
}
</style>