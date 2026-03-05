<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  const token = localStorage.getItem('access_token')
  
  if (!token) {
    alert('Acesso negado. Por favor, faça login no terminal.')
    router.push('/')
  }
})

const handleLogout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  router.push('/')
}
</script>

<template>
  <div class="home-container">
    <header class="home-header">
      <h2 class="main-logo">CRED<span>CODE</span></h2>
      <button @click="handleLogout" class="btn-logout">Sair do Terminal</button>
    </header>
    
    <main class="dashboard">
      <h1>Bem-vindo ao Dashboard Financeiro</h1>
      <p>Seu terminal está pronto para processar dados.</p>
    </main>
  </div>
</template>

<style scoped>
.home-container {
  padding: 20px;
  font-family: 'Inter', sans-serif;
  color: #0a2a43;
}

.home-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #f7b500;
  padding-bottom: 15px;
}

.main-logo { font-weight: 900; font-size: 1.5rem; }
.main-logo span { color: #f7b500; }

.btn-logout {
  background: #0a2a43;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 600;
}

.dashboard {
  margin-top: 40px;
  text-align: center;
}
</style>