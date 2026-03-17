<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue'

const router = useRouter()
const isAuthorized = ref(false)

const toast = reactive({
  show: false,
  message: '',
  type: 'error'
})

const userData = reactive({
  balance: 0
})
const defaultWalletId = ref(null)

const goals = ref([])
const showModal = ref(false)
const showFundsModal = ref(false)
const selectedGoalId = ref(null)

const form = reactive({
  id: null,
  title: '',
  targetAmount: '',
  currentAmount: '',
  deadline: ''
})

const fundsForm = reactive({
  amount: ''
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

const loadBalance = async () => {
  try {
    let baseBalance = 0
    const profileRes = await fetchWithAuth('http://localhost:8000/api/finances/profile/')
    
    if (profileRes.ok) {
      const data = await profileRes.json()
      if (data.account_balance !== undefined && data.account_balance !== null) {
        baseBalance = parseFloat(data.account_balance) || 0
      }
    }

    const walletRes = await fetchWithAuth('http://localhost:8000/api/finances/wallets/')
    
    if (walletRes.ok) {
      const wallets = await walletRes.json()
      if (wallets.length > 0) {
        defaultWalletId.value = wallets[0].id
        if (baseBalance === 0 && wallets[0].balance !== undefined && wallets[0].balance !== null) {
          baseBalance = parseFloat(wallets[0].balance) || 0
        }
      }
    }

    const expensesRes = await fetchWithAuth('http://localhost:8000/api/finances/expenses/')

    if (expensesRes.ok) {
      const expenses = await expensesRes.json()
      let totalInc = 0
      let totalExp = 0

      expenses.forEach(item => {
        const val = parseFloat(item.amount || item.value || 0)
        if (val >= 0) totalInc += val
        else totalExp += Math.abs(val)
      })

      userData.balance = baseBalance + totalInc - totalExp
    } else {
      userData.balance = baseBalance
    }
  } catch (error) {
    showToast('Erro ao carregar saldo da conta.', 'error')
  }
}

const loadGoals = () => {
  const saved = localStorage.getItem('finances_goals')
  if (saved) {
    goals.value = JSON.parse(saved)
  }
}

const saveGoals = () => {
  localStorage.setItem('finances_goals', JSON.stringify(goals.value))
}

onMounted(async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    showToast('Acesso negado. Por favor, faça login.', 'error')
    setTimeout(() => {
      router.push('/')
    }, 1500)
  } else {
    isAuthorized.value = true
    loadGoals()
    await loadBalance()
  }
})

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}

const calculateProgress = (current, target) => {
  if (!target || target <= 0) return 0
  const progress = (current / target) * 100
  return progress > 100 ? 100 : progress
}

const totalTarget = computed(() => {
  return goals.value.reduce((acc, goal) => acc + parseFloat(goal.targetAmount || 0), 0)
})

const totalSaved = computed(() => {
  return goals.value.reduce((acc, goal) => acc + parseFloat(goal.currentAmount || 0), 0)
})

const overallProgress = computed(() => {
  return calculateProgress(totalSaved.value, totalTarget.value)
})

const openModal = () => {
  form.id = Date.now().toString()
  form.title = ''
  form.targetAmount = ''
  form.currentAmount = ''
  form.deadline = ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const saveGoal = async () => {
  if (!form.title || !form.targetAmount || !form.deadline) {
    showToast('Preencha os campos obrigatórios.', 'error')
    return
  }

  const initialAmount = parseFloat(form.currentAmount) || 0

  if (initialAmount > 0) {
    if (!defaultWalletId.value) {
      showToast('Carteira não encontrada.', 'error')
      return
    }

    if (initialAmount > userData.balance) {
      showToast('Saldo insuficiente para o depósito inicial.', 'error')
      return
    }

    const payload = {
      wallet: defaultWalletId.value,
      description: `[Metas] Reserva: ${form.title}`,
      amount: -Math.abs(initialAmount),
      date: new Date().toISOString().split('T')[0],
      category: 'Metas'
    }

    try {
      const res = await fetchWithAuth('http://localhost:8000/api/finances/expenses/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        showToast('Erro ao registrar desconto no saldo.', 'error')
        return
      }
      
      userData.balance -= initialAmount
    } catch (e) {
      showToast('Erro de conexão.', 'error')
      return
    }
  }

  const newGoal = {
    id: form.id,
    title: form.title,
    targetAmount: parseFloat(form.targetAmount),
    currentAmount: initialAmount,
    deadline: form.deadline
  }

  goals.value.push(newGoal)
  saveGoals()
  await loadBalance()
  closeModal()
  showToast('Meta criada com sucesso!', 'success')
}

const openFundsModal = (id) => {
  selectedGoalId.value = id
  fundsForm.amount = ''
  showFundsModal.value = true
}

const closeFundsModal = () => {
  showFundsModal.value = false
  selectedGoalId.value = null
}

const addFunds = async () => {
  const amount = parseFloat(fundsForm.amount)
  if (!amount || amount <= 0) {
    showToast('Insira um valor válido.', 'error')
    return
  }

  const goalIndex = goals.value.findIndex(g => g.id === selectedGoalId.value)
  if (goalIndex !== -1) {
    const goal = goals.value[goalIndex]

    if (!defaultWalletId.value) {
      showToast('Carteira não encontrada.', 'error')
      return
    }

    if (amount > userData.balance) {
      showToast('Saldo insuficiente na sua conta principal.', 'error')
      return
    }

    const payload = {
      wallet: defaultWalletId.value,
      description: `[Metas] Depósito: ${goal.title}`,
      amount: -Math.abs(amount),
      date: new Date().toISOString().split('T')[0],
      category: 'Metas'
    }

    try {
      const res = await fetchWithAuth('http://localhost:8000/api/finances/expenses/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        showToast('Erro ao registrar desconto no saldo.', 'error')
        return
      }
      
      userData.balance -= amount
    } catch (e) {
      showToast('Erro de conexão.', 'error')
      return
    }

    goals.value[goalIndex].currentAmount += amount
    saveGoals()
    await loadBalance()
    closeFundsModal()
    showToast('Valor guardado com sucesso!', 'success')
  }
}

const deleteGoal = (id) => {
  goals.value = goals.value.filter(g => g.id !== id)
  saveGoals()
  showToast('Meta excluída.', 'success')
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />

  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Metas de Economia</h1>
        <p>Acompanhe seus objetivos e realize seus sonhos</p>
      </div>
      <div class="header-actions">
        <button @click="openModal" class="action-btn btn-primary">
          <span class="btn-icon">+</span> Nova Meta
        </button>
      </div>
    </div>

    <div class="dashboard-overview">
      <div class="overview-cards">
        <div class="card overview-card primary-card">
          <div class="card-data">
            <h3>Progresso Geral</h3>
            <span class="summary-value text-white">{{ overallProgress.toFixed(1) }}%</span>
          </div>
          <div class="progress-track-large">
            <div class="progress-fill-large" :style="{ width: overallProgress + '%' }"></div>
          </div>
        </div>

        <div class="card overview-card">
          <div class="card-icon-wrapper positive-bg">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20"></path><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
          </div>
          <div class="card-data">
            <h3>Total Guardado</h3>
            <span class="summary-value positive">{{ formatCurrency(totalSaved) }}</span>
          </div>
        </div>

        <div class="card overview-card">
          <div class="card-icon-wrapper neutral-bg">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          </div>
          <div class="card-data">
            <h3>Objetivo Total</h3>
            <span class="summary-value">{{ formatCurrency(totalTarget) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="goals.length === 0" class="empty-state-container">
      <div class="empty-icon">🎯</div>
      <h3>Nenhuma meta definida</h3>
      <p>Crie sua primeira meta financeira para começar a poupar com propósito.</p>
    </div>

    <div v-else class="goals-grid">
      <div v-for="goal in goals" :key="goal.id" class="goal-card">
        <div class="goal-header">
          <div class="goal-title-group">
            <div class="goal-icon">⭐</div>
            <div>
              <h3 class="goal-title">{{ goal.title }}</h3>
              <span class="goal-deadline">Prazo: {{ goal.deadline.split('-').reverse().join('/') }}</span>
            </div>
          </div>
          <button @click="deleteGoal(goal.id)" class="btn-delete-goal">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>

        <div class="goal-amounts">
          <div class="amount-block">
            <span class="amount-label">Guardado</span>
            <span class="amount-current">{{ formatCurrency(goal.currentAmount) }}</span>
          </div>
          <div class="amount-block text-right">
            <span class="amount-label">Objetivo</span>
            <span class="amount-target">{{ formatCurrency(goal.targetAmount) }}</span>
          </div>
        </div>

        <div class="goal-progress-section">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :style="{ width: calculateProgress(goal.currentAmount, goal.targetAmount) + '%' }"></div>
          </div>
          <div class="progress-percentage">{{ calculateProgress(goal.currentAmount, goal.targetAmount).toFixed(1) }}%</div>
        </div>

        <button @click="openFundsModal(goal.id)" class="btn-add-funds">
          Adicionar Valor
        </button>
      </div>
    </div>

    <FooterComp />

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <div class="modal-header">
          <h2>Nova Meta</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <form @submit.prevent="saveGoal" class="modal-form">
          <div class="form-group full-width">
            <label>Nome da Meta</label>
            <input v-model="form.title" type="text" placeholder="Ex: Viagem para Paris" required />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Valor Alvo (R$)</label>
              <input v-model="form.targetAmount" type="number" step="0.01" min="1" placeholder="0.00" required />
            </div>
            <div class="form-group">
              <label>Já guardou algo? (R$)</label>
              <input v-model="form.currentAmount" type="number" step="0.01" min="0" placeholder="0.00" />
            </div>
          </div>
          <div class="form-group full-width">
            <label>Data Limite</label>
            <input v-model="form.deadline" type="date" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeModal">Cancelar</button>
            <button type="submit" class="btn-save bg-primary">Criar Meta</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showFundsModal" class="modal-overlay" @click.self="closeFundsModal">
      <div class="modal-container small-modal">
        <div class="modal-header">
          <h2>Adicionar Fundos</h2>
          <button class="close-btn" @click="closeFundsModal">&times;</button>
        </div>
        <form @submit.prevent="addFunds" class="modal-form">
          <div class="form-group full-width">
            <label>Valor a adicionar (R$)</label>
            <input v-model="fundsForm.amount" type="number" step="0.01" min="0.01" placeholder="0.00" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeFundsModal">Cancelar</button>
            <button type="submit" class="btn-save bg-positive">Guardar</button>
          </div>
        </form>
      </div>
    </div>
  </SideLayout>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.header-titles h1 { color: var(--text-primary); font-size: 2rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.5px; transition: color 0.3s; }
.header-titles p { color: var(--text-secondary); margin: 0; font-size: 1.05rem; transition: color 0.3s; }
.header-actions { display: flex; gap: 15px; }
.action-btn { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 14px 24px; border-radius: 14px; font-weight: 700; font-size: 1rem; cursor: pointer; border: none; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); color: white; }
.btn-primary { background: linear-gradient(135deg, #f7b500 0%, #e6a800 100%); color: #0f172a; box-shadow: 0 10px 15px -3px rgba(247, 181, 0, 0.3); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 15px 25px -5px rgba(247, 181, 0, 0.4); }
.btn-icon { font-size: 1.3rem; font-weight: 900; line-height: 1; }
.dashboard-overview { display: flex; flex-direction: column; gap: 24px; margin-bottom: 35px; }
.overview-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
.card { background: var(--bg-card); padding: 25px 30px; border-radius: 20px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); display: flex; align-items: center; gap: 20px; transition: all 0.3s; }
.primary-card { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; flex-direction: column; align-items: flex-start; justify-content: center; gap: 15px; border: none; }
.card-data { width: 100%; }
.primary-card .card-data h3 { color: #94a3b8; }
.card-data h3 { color: var(--text-secondary); font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 5px 0; }
.summary-value { font-size: 1.8rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; color: var(--text-primary); }
.text-white { color: #f8fafc; }
.positive { color: #059669; }
.card-icon-wrapper { width: 55px; height: 55px; border-radius: 14px; display: flex; align-items: center; justify-content: center; }
.positive-bg { background-color: var(--positive-bg); color: #10b981; }
.neutral-bg { background-color: var(--neutral-bg); color: var(--text-secondary); }
.progress-track-large { width: 100%; height: 8px; background: rgba(255, 255, 255, 0.1); border-radius: 4px; overflow: hidden; }
.progress-fill-large { height: 100%; background: #f7b500; transition: width 0.5s ease; }
.empty-state-container { text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: 20px; border: 1px dashed var(--border-color); margin-top: 20px; }
.empty-icon { font-size: 3rem; margin-bottom: 15px; }
.empty-state-container h3 { color: var(--text-primary); font-size: 1.4rem; margin: 0 0 10px 0; }
.empty-state-container p { color: var(--text-secondary); margin: 0; font-size: 1rem; }
.goals-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; margin-bottom: 40px; }
.goal-card { background: var(--bg-card); border-radius: 20px; padding: 25px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s; }
.goal-card:hover { transform: translateY(-5px); box-shadow: var(--shadow-lg); }
.goal-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 25px; }
.goal-title-group { display: flex; align-items: center; gap: 15px; }
.goal-icon { width: 40px; height: 40px; border-radius: 12px; background: var(--neutral-bg); display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
.goal-title { color: var(--text-primary); font-size: 1.1rem; font-weight: 800; margin: 0 0 4px 0; }
.goal-deadline { color: var(--text-secondary); font-size: 0.8rem; font-weight: 600; }
.btn-delete-goal { background: none; border: none; color: var(--text-secondary); cursor: pointer; padding: 5px; border-radius: 8px; transition: all 0.2s; }
.btn-delete-goal:hover { background: var(--negative-bg); color: #dc2626; }
.goal-amounts { display: flex; justify-content: space-between; margin-bottom: 15px; }
.amount-block { display: flex; flex-direction: column; gap: 2px; }
.text-right { text-align: right; }
.amount-label { font-size: 0.8rem; color: var(--text-secondary); font-weight: 600; text-transform: uppercase; }
.amount-current { font-size: 1.2rem; font-weight: 800; color: #10b981; }
.amount-target { font-size: 1.2rem; font-weight: 800; color: var(--text-primary); }
.goal-progress-section { display: flex; align-items: center; gap: 15px; margin-bottom: 25px; }
.progress-bar-bg { flex: 1; height: 10px; background: var(--border-color); border-radius: 5px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: linear-gradient(90deg, #34d399 0%, #10b981 100%); transition: width 0.5s ease; }
.progress-percentage { font-size: 0.85rem; font-weight: 700; color: var(--text-secondary); min-width: 45px; text-align: right; }
.btn-add-funds { width: 100%; padding: 12px; background: var(--input-bg); border: 1px solid var(--border-input); border-radius: 12px; color: var(--text-primary); font-weight: 700; font-size: 0.95rem; cursor: pointer; transition: all 0.2s; }
.btn-add-funds:hover { background: var(--border-color); }
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-container { background: var(--bg-card); width: 100%; max-width: 480px; border-radius: 24px; box-shadow: var(--shadow-lg); border: 1px solid var(--border-color); padding: 35px; animation: modalSlideIn 0.3s ease-out; }
.small-modal { max-width: 400px; }
@keyframes modalSlideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.modal-header h2 { margin: 0; color: var(--text-primary); font-size: 1.5rem; font-weight: 800; }
.close-btn { background: var(--bg-main); border: none; width: 36px; height: 36px; border-radius: 50%; font-size: 1.5rem; color: var(--text-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center; line-height: 1; transition: all 0.2s; }
.close-btn:hover { background: var(--border-color); color: var(--text-primary); }
.modal-form { display: flex; flex-direction: column; gap: 20px; }
.form-row { display: flex; gap: 20px; }
.form-group { display: flex; flex-direction: column; gap: 10px; flex: 1; min-width: 0; }
.full-width { width: 100%; }
.form-group label { font-size: 0.95rem; font-weight: 600; color: var(--text-secondary); }
.form-group input { width: 100%; box-sizing: border-box; padding: 16px; border: 1px solid var(--border-input); border-radius: 12px; font-size: 1rem; font-family: 'Inter', sans-serif; outline: none; background-color: var(--input-bg); color: var(--text-primary); transition: all 0.3s; }
.form-group input:focus { border-color: #f7b500; background-color: var(--bg-card); box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1); }
.modal-actions { display: flex; gap: 15px; margin-top: 15px; }
.btn-cancel { flex: 1; padding: 16px; background-color: var(--bg-main); color: var(--text-secondary); border: 1px solid var(--border-color); border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: all 0.2s; }
.btn-cancel:hover { background: var(--border-color); color: var(--text-primary); }
.btn-save { flex: 1; padding: 16px; color: white; border: none; border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.2s; }
.btn-save:hover { transform: translateY(-2px); }
.bg-primary { background: linear-gradient(135deg, #f7b500 0%, #e6a800 100%); color: #0f172a; box-shadow: 0 10px 15px -3px rgba(247, 181, 0, 0.3); }
.bg-positive { background: linear-gradient(135deg, #10b981 0%, #059669 100%); box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3); }
@media (max-width: 768px) { .page-header { flex-direction: column; align-items: flex-start; gap: 15px; } .header-actions { width: 100%; } .action-btn { width: 100%; } .form-row { flex-direction: column; } }
</style>