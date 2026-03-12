<script setup>
import { ref, onMounted, reactive } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const sidebarOpen = ref(true)
const isMobileMenuOpen = ref(false)

const userData = reactive({
  name: 'Usuário'
})

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

const handleLogout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('has_profile')
  router.push('/')
}

onMounted(async () => {
  const token = localStorage.getItem('access_token')
  if (token) {
    try {
      const response = await fetch('http://localhost:8000/api/finances/profile/', {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      })
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

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background-color: #f8fafc;
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background-color: #0f172a;
  color: white;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1), left 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 4px 0 24px rgba(15, 23, 42, 0.1);
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
  color: white;
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
  color: white;
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
  color: #94a3b8;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.nav-item:hover:not(.active) {
  background-color: rgba(255, 255, 255, 0.05);
  color: #f8fafc;
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
  border: 4px solid #f8fafc;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 101;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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
  background-color: white;
  height: 90px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
  flex-shrink: 0;
  z-index: 90;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.breadcrumb {
  color: #334155;
  font-weight: 800;
  font-size: 1.25rem;
  letter-spacing: -0.5px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.user-profile-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 6px 14px 6px 6px;
  background-color: #f8fafc;
  border-radius: 30px;
  border: 1px solid #f1f5f9;
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
  color: #0f172a;
  font-size: 0.95rem;
}

.btn-logout-header {
  background-color: #fff1f2;
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
  background-color: #ffe4e6;
  transform: translateY(-2px);
}

.btn-hamburguer {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  color: #0f172a;
  padding: 8px;
  font-size: 1.6rem;
  border-radius: 8px;
  background-color: #f8fafc;
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
    background: rgba(15, 23, 42, 0.5);
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
}
</style>