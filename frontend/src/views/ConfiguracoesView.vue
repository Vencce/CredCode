<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue'

const router = useRouter()
const isAuthorized = ref(false)
const isSaving = ref(false)

const toast = reactive({
  show: false,
  message: '',
  type: 'error'
})

const form = reactive({
  full_name: '',
  monthly_income: '',
  account_balance: ''
})

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
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

const loadProfile = async () => {
  try {
    const response = await fetchWithAuth('http://localhost:8000/api/finances/profile/')
    
    if (response.ok) {
      const data = await response.json()
      form.full_name = data.full_name || ''
      form.monthly_income = data.monthly_income !== undefined && data.monthly_income !== null ? data.monthly_income : ''
      form.account_balance = data.account_balance !== undefined && data.account_balance !== null ? data.account_balance : ''
    }
  } catch (error) {
    showToast('Erro ao carregar dados do perfil.', 'error')
  }
}

onMounted(() => {
  const token = localStorage.getItem('access_token')
  
  if (!token) {
    showToast('Acesso negado. Por favor, faça login no terminal.', 'error')
    setTimeout(() => {
      router.push('/')
    }, 1500)
  } else {
    isAuthorized.value = true
    loadProfile()
  }
})

const saveProfile = async () => {
  if (!form.full_name) {
    showToast('O nome completo é obrigatório.', 'error')
    return
  }

  isSaving.value = true

  const payload = {
    full_name: form.full_name,
    monthly_income: form.monthly_income ? parseFloat(form.monthly_income) : 0,
    account_balance: form.account_balance ? parseFloat(form.account_balance) : 0
  }

  try {
    const response = await fetchWithAuth('http://localhost:8000/api/finances/profile/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (response.ok) {
      showToast('Perfil atualizado com sucesso!', 'success')
      loadProfile()
    } else {
      showToast('Erro ao salvar os dados do perfil.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  
  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Configurações</h1>
        <p>Gerencie seus dados pessoais e preferências do terminal</p>
      </div>
    </div>

    <div class="settings-container">
      <div class="settings-card">
        <div class="card-header">
          <div class="header-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </div>
          <div class="header-text">
            <h2>Perfil do Usuário</h2>
            <p>Atualize suas informações básicas e saldos iniciais.</p>
          </div>
        </div>

        <form @submit.prevent="saveProfile" class="settings-form">
          <div class="form-group full-width">
            <label>Nome Completo</label>
            <input v-model="form.full_name" type="text" placeholder="Seu nome completo" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Renda Mensal (R$)</label>
              <input v-model="form.monthly_income" type="number" step="0.01" min="0" placeholder="0.00" />
            </div>

            <div class="form-group">
              <label>Saldo Inicial da Conta (R$)</label>
              <input v-model="form.account_balance" type="number" step="0.01" placeholder="0.00" />
            </div>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn-save" :disabled="isSaving">
              {{ isSaving ? 'Salvando...' : 'Salvar Alterações' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <FooterComp />
  </SideLayout>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 35px;
}

.header-titles h1 {
  color: var(--text-primary);
  font-size: 2rem;
  font-weight: 800;
  margin: 0 0 4px 0;
  letter-spacing: -0.5px;
  transition: color 0.3s;
}

.header-titles p {
  color: var(--text-secondary);
  margin: 0;
  font-size: 1.05rem;
  transition: color 0.3s;
}

.settings-container {
  max-width: 850px;
  margin-bottom: 40px;
}

.settings-card {
  background: var(--bg-card);
  border-radius: 24px;
  padding: 45px 40px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-color);
  transition: background-color 0.3s, border-color 0.3s;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 35px;
  padding-bottom: 25px;
  border-bottom: 2px solid var(--border-color);
  transition: border-color 0.3s;
}

.header-icon {
  width: 60px;
  height: 60px;
  background-color: var(--bg-main);
  color: #f7b500;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s;
}

.header-text h2 {
  color: var(--text-primary);
  font-size: 1.4rem;
  font-weight: 800;
  margin: 0 0 6px 0;
  letter-spacing: -0.5px;
  transition: color 0.3s;
}

.header-text p {
  color: var(--text-secondary);
  margin: 0;
  font-size: 1rem;
  transition: color 0.3s;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.form-row {
  display: flex;
  gap: 25px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.full-width {
  width: 100%;
}

.form-group label {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-secondary);
  transition: color 0.3s;
}

.form-group input {
  padding: 16px;
  border: 1px solid var(--border-input);
  background-color: var(--input-bg);
  border-radius: 12px;
  font-size: 1rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--text-primary);
}

.form-group input::placeholder {
  color: #94a3b8;
  font-weight: 500;
}

.form-group input:focus {
  border-color: #f7b500;
  background-color: var(--bg-card);
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.form-actions {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.btn-save {
  padding: 16px 35px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 800;
  font-size: 1.05rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 15px 25px -5px rgba(16, 185, 129, 0.4);
}

.btn-save:disabled {
  background: var(--border-color);
  color: var(--text-secondary);
  box-shadow: none;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 768px) {
  .settings-card {
    padding: 30px 25px;
  }

  .form-row {
    flex-direction: column;
    gap: 25px;
  }
  
  .btn-save {
    width: 100%;
  }
}
</style>