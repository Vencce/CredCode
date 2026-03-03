<script setup>
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
const sidebarOpen = ref(true)
const isMobileMenuOpen = ref(false)

// Alterna o menu no desktop (recolhe/expande)
const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

// Alterna o menu no mobile (abre/fecha como overlay)
const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

// Verifica se a rota está ativa
const isActive = (path) => {
  return route.path === path
}
</script>

<template>
  <div class="dashboard-layout">
    <div v-if="isMobileMenuOpen" class="mobile-overlay" @click="closeMobileMenu"></div>

    <aside :class="['sidebar', { closed: !sidebarOpen, 'mobile-open': isMobileMenuOpen }]">
      <div class="sidebar-header">
        <div class="logo-area">
          <img v-if="sidebarOpen" src="../components/imagens/logo.png" alt="Capital X Invest" class="brand-logo" />
          <strong v-else class="brand-icon-collapsed">CX</strong>
        </div>
      </div>

      <nav class="sidebar-nav">
        <ul>
          <li :class="{ active: isActive('/home') }">
            <RouterLink to="/home" @click="closeMobileMenu">
              <i class="fa-solid fa-house icon-menu"></i>
              <span v-if="sidebarOpen">Home</span>
            </RouterLink>
          </li>

          <li :class="{ active: isActive('/como-funciona') }">
            <RouterLink to="/como-funciona" @click="closeMobileMenu">
              <i class="fa-solid fa-gears icon-menu"></i>
              <span v-if="sidebarOpen">Como Funciona</span>
            </RouterLink>
          </li>

          <li :class="{ active: isActive('/duvidas') }">
            <RouterLink to="/duvidas" @click="closeMobileMenu">
              <i class="fa-solid fa-circle-question icon-menu"></i>
              <span v-if="sidebarOpen">Dúvidas</span>
            </RouterLink>
          </li>

          <li :class="{ active: isActive('/onde-encontrar') }">
            <RouterLink to="/onde-encontrar" @click="closeMobileMenu">
              <i class="fa-solid fa-location-dot icon-menu"></i>
              <span v-if="sidebarOpen">Onde Estamos</span>
            </RouterLink>
          </li>
        </ul>
      </nav>

      <button class="toggle-btn" @click="toggleSidebar">
        <i v-if="sidebarOpen" class="fa-solid fa-chevron-left"></i>
        <i v-else class="fa-solid fa-chevron-right"></i>
      </button>
    </aside>

    <main class="main-content">
      <header class="top-bar">
        <div class="topbar-left">
          <button class="btn-hamburguer" @click="toggleMobileMenu">
            <i class="fa-solid fa-bars"></i>
          </button>
          
          <div class="breadcrumb" v-if="!isMobileMenuOpen">
             <span>Investimentos Inteligentes</span>
          </div>
        </div>

        <div class="topbar-right">
           <a href="https://wa.me/SEUNUMERO" target="_blank" class="btn-whatsapp-desktop">
              <i class="fa-brands fa-whatsapp"></i> Falar no WhatsApp
           </a>
        </div>
      </header>

      <div class="content-body">
        <slot></slot>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard-layout {
  display: flex;
  height: 100vh;
  background-color: #f8fafc;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  overflow: hidden;
}

/* Sidebar Base */
.sidebar {
  width: 260px;
  background-color: #ffffff;
  color: #4b5563;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  position: relative;
  box-shadow: 2px 0 10px rgba(0,0,0,0.05);
  z-index: 100;
}

.sidebar.closed {
  width: 80px;
}

/* Cabeçalho da Sidebar */
.sidebar-header {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 15px;
  border-bottom: 1px solid #f1f5f9;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-logo {
  height: 45px;
  max-width: 100%;
  object-fit: contain;
}

.brand-icon-collapsed {
  font-size: 1.5rem;
  font-weight: 800;
  color: #f7b500;
}

/* Navegação da Sidebar */
.sidebar-nav {
  flex: 1;
  padding: 20px 0;
  overflow-y: auto;
  scrollbar-width: none;
}
.sidebar-nav::-webkit-scrollbar {
  display: none;
}

.sidebar-nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-nav li {
  margin-bottom: 5px;
  position: relative;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  padding: 14px 24px;
  color: #4b5563;
  text-decoration: none;
  transition: all 0.2s;
  font-weight: 600;
  font-size: 0.95rem;
}

.sidebar-nav a:hover {
  background-color: #fdfdfd;
  color: #252f3f;
}

/* Estado Ativo = Amarelo da sua marca */
.sidebar-nav li.active a {
  color: #f7b500;
  background-color: #fffbeb; 
  border-right: 4px solid #f7b500;
}

/* Estilização dos ícones do FontAwesome no menu */
.sidebar-nav a i.icon-menu {
  font-size: 1.25rem;
  width: 24px; /* Fixa uma largura para alinhar o texto perfeitamente */
  text-align: center;
  margin-right: 15px;
  flex-shrink: 0;
  transition: color 0.2s;
}

/* Quando ativo, muda a cor do ícone */
.sidebar-nav li.active a i.icon-menu {
  color: #f7b500;
}

/* Ajustes quando fechado */
.sidebar.closed .sidebar-nav a {
  justify-content: center;
  padding: 14px;
}
.sidebar.closed .sidebar-nav a i.icon-menu {
  margin-right: 0;
}

/* Botão de Recolher/Expandir Sidebar */
.toggle-btn {
  position: absolute;
  right: -12px;
  top: 90px;
  background-color: #ffffff;
  color: #4b5563;
  border: 1px solid #e2e8f0;
  border-radius: 50%;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 101;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  font-size: 0.8rem; /* Tamanho do ícone menorzinho */
}
.toggle-btn:hover {
  color: #F6D001;
}

/* Main Content e Topbar */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.top-bar {
  background-color: white;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.breadcrumb {
  color: #64748b;
  font-weight: 500;
}

.btn-whatsapp-desktop {
  background-color: #25D366;
  color: white;
  padding: 10px 20px;
  border-radius: 30px;
  font-weight: 700;
  font-size: 0.9rem;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px; /* Espaço entre o ícone e texto */
  transition: all 0.2s;
}
.btn-whatsapp-desktop i {
  font-size: 1.2rem;
}
.btn-whatsapp-desktop:hover {
  background-color: #1da851;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 211, 102, 0.2);
}

.content-body {
  padding: 30px;
}

.btn-hamburguer {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  color: #4b5563;
  padding: 5px;
  font-size: 1.5rem;
}

/* Responsividade Mobile */
@media (max-width: 1024px) {
  .toggle-btn {
    display: none; 
  }

  .sidebar {
    position: fixed;
    height: 100%;
    left: -280px;
    width: 280px !important;
    transition: left 0.3s ease;
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
    background: rgba(0,0,0,0.5);
    z-index: 99;
  }
}

@media (max-width: 480px) {
  .top-bar {
    padding: 0 15px;
  }
  .content-body {
    padding: 15px;
  }
}
</style>