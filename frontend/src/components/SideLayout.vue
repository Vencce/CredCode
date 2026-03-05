<script setup>
import { ref, onMounted, reactive } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
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

        <RouterLink to="/relatorios" class="nav-item" :class="{ active: isActive('/relatorios') }" @click="closeMobileMenu">
          <span class="icon">📈</span>
          <span v-if="sidebarOpen" class="nav-text">Relatórios</span>
        </RouterLink>

        <RouterLink to="/configuracoes" class="nav-item" :class="{ active: isActive('/configuracoes') }" @click="closeMobileMenu">
          <span class="icon">⚙️</span>
          <span v-if="sidebarOpen" class="nav-text">Configurações</span>
        </RouterLink>
      </nav>
      
      <div class="sidebar-footer">
        <div class="user-info" v-if="sidebarOpen">
          <div class="avatar">{{ userData.name.charAt(0).toUpperCase() }}</div>
          <span class="user-name">{{ userData.name }}</span>
        </div>
        <div class="user-info-closed" v-else>
          <div class="avatar-small">{{ userData.name.charAt(0).toUpperCase() }}</div>
        </div>
      </div>
      
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
          <a href="https://wa.me/SEUNUMERO" target="_blank" class="btn-whatsapp-desktop">
            <span class="icon-zap">💬</span> <span class="whatsapp-text">Suporte</span>
          </a>
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
  background-color: #f4f7f9;
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}

.sidebar {
  width: 260px;
  background-color: #0a2a43;
  color: white;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.3s ease, left 0.3s ease;
  box-shadow: 4px 0 15px rgba(0, 0, 0, 0.05);
  z-index: 100;
}

.sidebar.closed {
  width: 80px;
}

.sidebar-brand {
  padding: 30px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
  height: 85px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-logo {
  font-weight: 900;
  font-size: 1.8rem;
  margin: 0;
  letter-spacing: -1px;
}

.main-logo span {
  color: #f7b500;
}

.main-logo-collapsed {
  font-weight: 900;
  font-size: 1.8rem;
  margin: 0;
  color: #f7b500;
}

.main-logo-collapsed span {
  color: white;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
  overflow-y: auto;
}

.sidebar-nav::-webkit-scrollbar {
  display: none;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 15px 25px;
  color: #cbd5e1;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s;
  border-left: 4px solid transparent;
  white-space: nowrap;
}

.nav-item:hover, .nav-item.active {
  background-color: rgba(255, 255, 255, 0.05);
  color: white;
  border-left-color: #f7b500;
}

.sidebar.closed .nav-item {
  justify-content: center;
  padding: 15px;
}

.icon {
  margin-right: 15px;
  font-size: 1.2rem;
}

.sidebar.closed .icon {
  margin-right: 0;
  font-size: 1.4rem;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
  width: 100%;
}

.user-info-closed {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #f7b500;
  color: #0a2a43;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.avatar-small {
  width: 35px;
  height: 35px;
  border-radius: 50%;
  background-color: #f7b500;
  color: #0a2a43;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1rem;
}

.user-name {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.95rem;
}

.toggle-btn {
  position: absolute;
  right: -14px;
  top: 100px;
  background-color: #f7b500;
  color: #0a2a43;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 101;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  font-size: 0.8rem;
  font-weight: 900;
  transition: transform 0.3s, background-color 0.3s;
}

.toggle-btn:hover {
  background-color: #e6a800;
  transform: scale(1.1);
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.top-header {
  background-color: white;
  height: 85px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.breadcrumb {
  color: #0a2a43;
  font-weight: 800;
  font-size: 1.2rem;
}

.btn-hamburguer {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  color: #0a2a43;
  padding: 5px;
  font-size: 1.5rem;
}

.btn-whatsapp-desktop {
  background-color: #10b981;
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
}

.btn-whatsapp-desktop:hover {
  background-color: #059669;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.icon-zap {
  font-size: 1.2rem;
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
    left: -280px;
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
    background: rgba(10, 42, 67, 0.6);
    backdrop-filter: blur(2px);
    z-index: 99;
  }
  
  .top-header {
    padding: 0 20px;
  }
  
  .content-body {
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .whatsapp-text {
    display: none;
  }
  
  .btn-whatsapp-desktop {
    padding: 10px;
    border-radius: 50%;
  }
  
  .btn-whatsapp-desktop .icon-zap {
    margin: 0;
  }
}
</style>