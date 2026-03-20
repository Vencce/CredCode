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

const defaultWalletId = ref(null)
const budgets = ref([])
const expenses = ref([])

const showModal = ref(false)
const showDeleteModal = ref(false)
const editingId = ref(null)
const itemToDelete = ref(null)

const expenseCategories = ['Alimentação', 'Transporte', 'Moradia', 'Contas', 'Saúde', 'Lazer', 'Outros']

const form = reactive({
  category: '',
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

const loadData = async () => {
  try {
    const walletRes = await fetchWithAuth('http://localhost:8000/api/finances/wallets/')
    if (walletRes.ok) {
      const wallets = await walletRes.json()
      if (wallets.length > 0) defaultWalletId.value = wallets[0].id
    }

    const expensesRes = await fetchWithAuth('http://localhost:8000/api/finances/expenses/')
    if (expensesRes.ok) {
      expenses.value = await expensesRes.json()
    }

    const budgetsRes = await fetchWithAuth('http://localhost:8000/api/finances/budgets/')
    if (budgetsRes.ok) {
      budgets.value = await budgetsRes.json()
    }
  } catch (error) {
    showToast('Erro ao sincronizar dados com o terminal.', 'error')
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
    loadData()
  }
})

const budgetsWithProgress = computed(() => {
  const now = new Date()
  const currentMonth = now.getMonth()
  const currentYear = now.getFullYear()

  const spentByCategory = {}
  
  expenses.value.forEach(e => {
    const parts = e.date.split('-')
    const expDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2].substring(0, 2)))
    
    if (e.amount < 0 && expDate.getMonth() === currentMonth && expDate.getFullYear() === currentYear) {
      const cat = e.category || 'Outros'
      spentByCategory[cat] = (spentByCategory[cat] || 0) + Math.abs(e.amount)
    }
  })

  return budgets.value.map(b => {
    const spent = spentByCategory[b.category] || 0
    const limit = parseFloat(b.amount)
    let percentage = (spent / limit) * 100
    if (percentage > 100) percentage = 100
    
    let status = 'success'
    if (percentage >= 80 && percentage < 100) status = 'warning'
    if (percentage >= 100) status = 'danger'

    return {
      ...b,
      spent,
      limit,
      percentage,
      status
    }
  }).sort((a, b) => b.percentage - a.percentage)
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

const openModal = (item = null) => {
  if (item) {
    editingId.value = item.id
    form.category = item.category
    form.amount = item.amount
  } else {
    editingId.value = null
    form.category = ''
    form.amount = ''
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingId.value = null
}

const saveBudget = async () => {
  if (!form.category || !form.amount) {
    showToast('Preencha todos os campos.', 'error')
    return
  }

  if (!defaultWalletId.value) {
    showToast('Carteira não encontrada. Recarregue a página.', 'error')
    return
  }

  const payload = {
    wallet: defaultWalletId.value,
    category: form.category,
    amount: parseFloat(form.amount)
  }

  try {
    const url = editingId.value 
      ? `http://localhost:8000/api/finances/budgets/${editingId.value}/`
      : 'http://localhost:8000/api/finances/budgets/'
      
    const method = editingId.value ? 'PUT' : 'POST'

    const response = await fetchWithAuth(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (response.ok) {
      showToast(editingId.value ? 'Orçamento atualizado!' : 'Orçamento criado!', 'success')
      closeModal()
      loadData()
    } else {
      showToast('Erro ao salvar orçamento.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  }
}

const confirmDelete = (id) => {
  itemToDelete.value = id
  showDeleteModal.value = true
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  itemToDelete.value = null
}

const executeDelete = async () => {
  if (!itemToDelete.value) return

  try {
    const response = await fetchWithAuth(`http://localhost:8000/api/finances/budgets/${itemToDelete.value}/`, {
      method: 'DELETE'
    })

    if (response.ok) {
      showToast('Orçamento excluído!', 'success')
      loadData()
    } else {
      showToast('Erro ao excluir orçamento.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  } finally {
    closeDeleteModal()
  }
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />

  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Orçamentos</h1>
        <p>Defina limites de gastos por categoria no mês</p>
      </div>
      <div class="header-actions">
        <button @click="openModal()" class="action-btn btn-primary">
          <span class="btn-icon">+</span> Novo Orçamento
        </button>
      </div>
    </div>

    <div v-if="budgetsWithProgress.length === 0" class="empty-state-container">
      <div class="empty-icon">🚧</div>
      <h3>Nenhum orçamento definido</h3>
      <p>Crie orçamentos para controlar seus gastos e receber alertas antes de extrapolar.</p>
    </div>

    <div v-else class="budgets-grid">
      <div v-for="budget in budgetsWithProgress" :key="budget.id" class="budget-card">
        <div class="budget-header">
          <h3 class="budget-title">{{ budget.category }}</h3>
          <div class="budget-actions">
            <button @click="openModal(budget)" class="action-icon" title="Editar">✏️</button>
            <button @click="confirmDelete(budget.id)" class="action-icon delete-icon" title="Excluir">🗑️</button>
          </div>
        </div>

        <div class="budget-values">
          <div class="value-block">
            <span class="label">Gasto no mês</span>
            <span :class="['amount', budget.status === 'danger' ? 'text-negative' : '']">{{ formatCurrency(budget.spent) }}</span>
          </div>
          <div class="value-block align-right">
            <span class="label">Limite</span>
            <span class="amount">{{ formatCurrency(budget.limit) }}</span>
          </div>
        </div>

        <div class="progress-container">
          <div class="progress-bar-bg">
            <div :class="['progress-bar-fill', `fill-${budget.status}`]" :style="{ width: budget.percentage + '%' }"></div>
          </div>
          <div class="progress-labels">
            <span class="percentage-text">{{ budget.percentage.toFixed(1) }}% consumido</span>
            <span v-if="budget.limit - budget.spent > 0" class="remaining-text">Disponível: {{ formatCurrency(budget.limit - budget.spent) }}</span>
            <span v-else class="remaining-text text-negative">Estourado: {{ formatCurrency(budget.spent - budget.limit) }}</span>
          </div>
        </div>
      </div>
    </div>

    <FooterComp />

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <div class="modal-header">
          <h2>{{ editingId ? 'Editar Orçamento' : 'Novo Orçamento' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        
        <form @submit.prevent="saveBudget" class="modal-form">
          <div class="form-group full-width">
            <label>Categoria</label>
            <select v-model="form.category" required :disabled="editingId !== null">
              <option value="" disabled>Selecione a categoria</option>
              <option v-for="cat in expenseCategories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>

          <div class="form-group full-width">
            <label>Limite Mensal (R$)</label>
            <input v-model="form.amount" type="number" step="0.01" min="1" placeholder="Ex: 600.00" required />
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeModal">Cancelar</button>
            <button type="submit" class="btn-save btn-primary">Salvar</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
      <div class="modal-container small-modal">
        <div class="modal-header">
          <h2 class="text-negative">Excluir Orçamento</h2>
          <button class="close-btn" @click="closeDeleteModal">&times;</button>
        </div>
        <div class="modal-body">
          <p>Tem certeza que deseja excluir este orçamento? Seu histórico de gastos da categoria não será afetado.</p>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="closeDeleteModal">Cancelar</button>
          <button type="button" class="btn-save bg-negative" @click="executeDelete">Excluir</button>
        </div>
      </div>
    </div>
  </SideLayout>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.header-titles h1 { color: var(--text-primary); font-size: 2rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.5px; transition: color 0.3s; }
.header-titles p { color: var(--text-secondary); margin: 0; font-size: 1.05rem; transition: color 0.3s; }
.header-actions { display: flex; gap: 15px; }
.action-btn { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 14px 24px; border-radius: 14px; font-weight: 700; font-size: 1rem; cursor: pointer; border: none; transition: all 0.3s; color: white; }
.btn-primary { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.3); color: white; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 15px 25px -5px rgba(15, 23, 42, 0.4); }
.btn-icon { font-size: 1.3rem; font-weight: 900; line-height: 1; }

.empty-state-container { text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: 20px; border: 1px dashed var(--border-color); margin-top: 20px; }
.empty-icon { font-size: 3rem; margin-bottom: 15px; }
.empty-state-container h3 { color: var(--text-primary); font-size: 1.4rem; margin: 0 0 10px 0; }
.empty-state-container p { color: var(--text-secondary); margin: 0; font-size: 1rem; }

.budgets-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; margin-bottom: 40px; }
.budget-card { background: var(--bg-card); border-radius: 20px; padding: 25px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; gap: 20px; }
.budget-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }

.budget-header { display: flex; justify-content: space-between; align-items: center; }
.budget-title { font-size: 1.2rem; font-weight: 800; color: var(--text-primary); margin: 0; }
.budget-actions { display: flex; gap: 8px; }
.action-icon { background: var(--input-bg); border: 1px solid var(--border-input); border-radius: 8px; padding: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; font-size: 0.9rem; }
.action-icon:hover { background: var(--border-color); transform: translateY(-2px); }
.delete-icon:hover { background: var(--negative-bg); border-color: #fecaca; }

.budget-values { display: flex; justify-content: space-between; align-items: flex-end; }
.value-block { display: flex; flex-direction: column; gap: 4px; }
.align-right { text-align: right; }
.label { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
.amount { font-size: 1.4rem; font-weight: 800; color: var(--text-primary); }

.progress-container { display: flex; flex-direction: column; gap: 8px; }
.progress-bar-bg { width: 100%; height: 10px; background-color: var(--border-color); border-radius: 5px; overflow: hidden; }
.progress-bar-fill { height: 100%; border-radius: 5px; transition: width 0.5s ease; }
.fill-success { background: linear-gradient(90deg, #34d399 0%, #10b981 100%); }
.fill-warning { background: linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%); }
.fill-danger { background: linear-gradient(90deg, #f87171 0%, #ef4444 100%); }

.progress-labels { display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; }
.percentage-text { color: var(--text-secondary); }
.remaining-text { color: var(--text-primary); }
.text-negative { color: #dc2626 !important; }

.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-container { background: var(--bg-card); width: 100%; max-width: 480px; border-radius: 24px; box-shadow: var(--shadow-lg); border: 1px solid var(--border-color); padding: 35px; animation: modalSlideIn 0.3s ease-out; transition: background-color 0.3s, border-color 0.3s; }
.small-modal { max-width: 400px; }
@keyframes modalSlideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.modal-header h2 { margin: 0; color: var(--text-primary); font-size: 1.5rem; font-weight: 800; }
.close-btn { background: var(--bg-main); border: none; width: 36px; height: 36px; border-radius: 50%; font-size: 1.5rem; color: var(--text-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.close-btn:hover { background: var(--border-color); color: var(--text-primary); }

.modal-form { display: flex; flex-direction: column; gap: 20px; }
.form-group { display: flex; flex-direction: column; gap: 10px; }
.full-width { width: 100%; }
.form-group label { font-size: 0.95rem; font-weight: 600; color: var(--text-secondary); }
.form-group input, .form-group select { width: 100%; box-sizing: border-box; padding: 16px; border: 1px solid var(--border-input); border-radius: 12px; font-size: 1rem; outline: none; background-color: var(--input-bg); color: var(--text-primary); transition: all 0.3s; }
.form-group input:focus, .form-group select:focus { border-color: #f7b500; background-color: var(--bg-card); box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1); }
.form-group select:disabled { opacity: 0.6; cursor: not-allowed; }

.modal-actions { display: flex; gap: 15px; margin-top: 15px; }
.btn-cancel { flex: 1; padding: 16px; background-color: var(--bg-main); color: var(--text-secondary); border: 1px solid var(--border-color); border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: all 0.2s; }
.btn-cancel:hover { background: var(--border-color); color: var(--text-primary); }
.btn-save { flex: 1; padding: 16px; color: white; border: none; border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.2s; }
.btn-save:hover { transform: translateY(-2px); }
.bg-negative { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3); }

.modal-body p { color: var(--text-secondary); font-size: 1.05rem; line-height: 1.5; margin-bottom: 25px; }

@media (max-width: 768px) { .page-header { flex-direction: column; align-items: flex-start; gap: 15px; } .header-actions { width: 100%; } .action-btn { width: 100%; } }
</style>