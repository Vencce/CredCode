<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

const isMenuOpen = ref(false)

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const closeMenu = () => {
  isMenuOpen.value = false
}
</script>

<template>
  <header class="main-header">
    <div class="header-container">
      <div class="logo-area">
        <RouterLink to="/" @click="closeMenu">
          <img alt="Capital X Invest" class="brand-logo" />
        </RouterLink>
      </div>
      
      <div v-if="isMenuOpen" class="menu-overlay" @click="closeMenu"></div>

      <nav class="nav-menu" :class="{ 'is-open': isMenuOpen }">
        <button class="btn-close-menu" @click="toggleMenu">
          <X :size="30" />
        </button>

        <RouterLink to="/quem-somos" class="nav-link" active-class="active" @click="closeMenu">Quem Somos</RouterLink>
        <RouterLink to="/como-funciona" class="nav-link" active-class="active" @click="closeMenu">Como Funciona</RouterLink>
        <RouterLink to="/" class="nav-link" active-class="active" @click="closeMenu">Cartas Contempladas</RouterLink>
        <RouterLink to="/duvidas" class="nav-link" active-class="active" @click="closeMenu">Duvidas</RouterLink>
        <RouterLink to="/onde-encontrar" class="nav-link" active-class="active" @click="closeMenu">Onde Estamos</RouterLink>

      </nav>
    </div>
  </header>
</template>

<style scoped>
.main-header {
  background: white;
  height: 90px;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 4px 20px -5px rgba(0,0,0,0.05);
  display: flex;
  align-items: center;
}

.header-container {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand-logo {
  height: 65px;
  width: auto;
  object-fit: contain;
}

.nav-menu {
  display: flex;
  gap: 30px;
}

.nav-link {
  text-decoration: none;
  color: #4b5563;
  font-weight: 600;
  font-size: 0.95rem;
  transition: color 0.2s;
  position: relative;
}

.nav-link:hover, .nav-link.active { color: #F6D001; }

.nav-link::after {
  content: '';
  position: absolute;
  width: 0;
  height: 3px;
  bottom: -6px;
  left: 0;
  background-color: #F6D001;
  transition: width 0.3s;
  border-radius: 2px;
}
.nav-link:hover::after, .nav-link.active::after { width: 100%; }

.btn-whatsapp-desktop {
  background-color: #25D366;
  color: white;
  padding: 12px 24px;
  border-radius: 30px;
  font-weight: 700;
  font-size: 0.9rem;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-whatsapp-desktop:hover {
  background-color: #1da851;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 211, 102, 0.2);
}

.btn-hamburguer, .btn-close-menu, .mobile-only-cta {
  display: none;
}

@media (max-width: 1024px) {
  .nav-menu {
    position: fixed;
    top: 0;
    right: -100%;
    width: 280px;
    height: 100vh;
    background: white;
    flex-direction: column;
    padding: 100px 30px;
    gap: 20px;
    box-shadow: -10px 0 30px rgba(0,0,0,0.1);
    transition: right 0.4s ease;
    z-index: 1001;
  }

  .nav-menu.is-open {
    right: 0;
  }

  .btn-hamburguer {
    display: block;
    background: none;
    border: none;
    cursor: pointer;
    color: #1e3a8a;
  }

  .btn-close-menu {
    display: block;
    position: absolute;
    top: 30px;
    right: 20px;
    background: none;
    border: none;
    color: #64748b;
  }

  .menu-overlay {
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.4);
    z-index: 1000;
  }

  .btn-whatsapp-desktop {
    display: none; 
  }

  .mobile-only-cta {
    display: block;
    margin-top: 20px;
  }

  .btn-whatsapp-mobile {
    background-color: #25D366;
    color: white;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    text-decoration: none;
    font-weight: 800;
    display: block;
  }

  .nav-link {
    font-size: 1.1rem;
    padding: 10px 0;
    border-bottom: 1px solid #f1f5f9;
  }

  .brand-logo {
    height: 50px;
  }
}
</style>