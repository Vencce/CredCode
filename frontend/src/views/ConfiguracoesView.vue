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

const loadProfile = async (token) => {
  try {
    const response = await fetch('http://localhost:8000/api/finances/profile/', {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
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
    loadProfile(token)
  }
})

const saveProfile = async () => {
  if (!form.full_name) {
    showToast('O nome completo é obrigatório.', 'error')
    return
  }

  isSaving.value = true
  const token = localStorage.getItem('access_token')

  const payload = {
    full_name: form.full_name,
    monthly_income: form.monthly_income ? parseFloat(form.monthly_income) : 0,
    account_balance: form.account_balance ? parseFloat(form.account_balance) : 0
  }

  try {
    const response = await fetch('http://localhost:8000/api/finances/profile/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (response.ok) {
      showToast('Perfil atualizado com sucesso!', 'success')
      loadProfile(token)
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
  color: #0f172a;
  font-size: 2rem;
  font-weight: 800;
  margin: 0 0 4px 0;
  letter-spacing: -0.5px;
}

.header-titles p {
  color: #64748b;
  margin: 0;
  font-size: 1.05rem;
}

.settings-container {
  max-width: 850px;
  margin-bottom: 40px;
}

.settings-card {
  background: white;
  border-radius: 24px;
  padding: 45px 40px;
  box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.05), 0 8px 10px -6px rgba(15, 23, 42, 0.02);
  border: 1px solid #f1f5f9;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 35px;
  padding-bottom: 25px;
  border-bottom: 2px solid #f8fafc;
}

.header-icon {
  width: 60px;
  height: 60px;
  background-color: #f8fafc;
  color: #f7b500;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-text h2 {
  color: #0f172a;
  font-size: 1.4rem;
  font-weight: 800;
  margin: 0 0 6px 0;
  letter-spacing: -0.5px;
}

.header-text p {
  color: #64748b;
  margin: 0;
  font-size: 1rem;
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
  color: #475569;
}

.form-group input {
  padding: 16px;
  border: 1px solid #cbd5e1;
  background-color: #f8fafc;
  border-radius: 12px;
  font-size: 1rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #0f172a;
}

.form-group input::placeholder {
  color: #94a3b8;
  font-weight: 500;
}

.form-group input:focus {
  border-color: #f7b500;
  background-color: white;
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
  background: #e2e8f0;
  color: #94a3b8;
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