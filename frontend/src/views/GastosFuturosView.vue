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

const transactions = ref([])
const defaultWalletId = ref(null)
const userCategories = ref([])

const showModal = ref(false)
const modalType = ref('expense')
const editingId = ref(null)

const showDeleteModal = ref(false)
const itemToDelete = ref(null)

const getTomorrowDate = () => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  return tomorrow.toISOString().split('T')[0]
}

const form = reactive({
  description: '',
  amount: '',
  date: getTomorrowDate(),
  category: '',
  isMonthly: false,
  monthsCount: 12
})

const filters = reactive({
  search: '',
  type: 'all'
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
      const expenses = await expensesRes.json()
      const today = new Date()
      today.setHours(0, 0, 0, 0)

      const parsedTransactions = expenses.map(item => {
        const val = parseFloat(item.amount || item.value || 0)
        const dateVal = item.date || item.created_at || ''
        const dateParts = dateVal.split('-')
        let formattedDate = dateVal
        let rawDate = new Date()

        if (dateParts.length === 3) {
          formattedDate = `${dateParts[2].substring(0, 2)}/${dateParts[1]}/${dateParts[0]}`
          rawDate = new Date(parseInt(dateParts[0]), parseInt(dateParts[1]) - 1, parseInt(dateParts[2].substring(0, 2)))
        }
        
        rawDate.setHours(0, 0, 0, 0)
        
        const diffTime = rawDate.getTime() - today.getTime()
        const daysRemaining = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

        let cat = item.category || 'Geral'
        let desc = item.description || 'Sem descrição'

        if (desc.startsWith('[')) {
          const closingBracket = desc.indexOf(']')
          if (closingBracket !== -1) {
            if (!item.category) {
              cat = desc.substring(1, closingBracket)
            }
            desc = desc.substring(closingBracket + 1).trim()
          }
        }

        return {
          id: item.id,
          description: desc,
          category: cat,
          amount: val,
          type: val >= 0 ? 'income' : 'expense',
          date: formattedDate,
          rawDate: rawDate,
          daysRemaining: daysRemaining
        }
      })

      transactions.value = parsedTransactions.filter(t => t.daysRemaining > 0).sort((a, b) => a.rawDate - b.rawDate)
    }

    const catRes = await fetchWithAuth('http://localhost:8000/api/finances/categories/')
    if (catRes.ok) {
      userCategories.value = await catRes.json()
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

const filteredTransactions = computed(() => {
  return transactions.value.filter(t => {
    const searchString = filters.search.toLowerCase()
    const matchesSearch = t.description.toLowerCase().includes(searchString) ||
      t.category.toLowerCase().includes(searchString)
    const matchesType = filters.type === 'all' || t.type === filters.type
    return matchesSearch && matchesType
  })
})

const totalFutureIncome = computed(() => {
  return filteredTransactions.value
    .filter(t => t.type === 'income')
    .reduce((acc, curr) => acc + curr.amount, 0)
})

const totalFutureExpense = computed(() => {
  return filteredTransactions.value
    .filter(t => t.type === 'expense')
    .reduce((acc, curr) => acc + Math.abs(curr.amount), 0)
})

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}

const currentCategories = computed(() => {
  return userCategories.value
    .filter(c => c.type === modalType.value)
    .map(c => c.name)
})

const openModal = (type, item = null) => {
  modalType.value = type
  
  if (item) {
    editingId.value = item.id
    form.description = item.description
    form.amount = Math.abs(item.amount)
    form.category = item.category
    form.isMonthly = false
    form.monthsCount = 12
    
    const dateParts = item.date.split('/')
    if (dateParts.length === 3) {
      form.date = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}`
    } else {
      form.date = item.date
    }
  } else {
    editingId.value = null
    form.description = ''
    form.amount = ''
    form.category = ''
    form.date = getTomorrowDate()
    form.isMonthly = false
    form.monthsCount = 12
  }
  
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingId.value = null
}

const saveTransaction = async () => {
  if (!form.description || !form.amount || !form.date || !form.category) {
    showToast('Preencha todos os campos obrigatórios', 'error')
    return
  }

  if (!defaultWalletId.value) {
    showToast('Carteira não encontrada. Recarregue a página.', 'error')
    return
  }

  let finalAmount = parseFloat(form.amount)

  if (modalType.value === 'expense') {
    finalAmount = -Math.abs(finalAmount)
  } else {
    finalAmount = Math.abs(finalAmount)
  }

  try {
    if (!editingId.value && form.isMonthly && form.monthsCount > 1) {
      const baseDate = new Date(form.date + 'T12:00:00')
      
      for (let i = 0; i < form.monthsCount; i++) {
        const currentDate = new Date(baseDate)
        currentDate.setMonth(currentDate.getMonth() + i)
        
        const payload = {
          wallet: defaultWalletId.value,
          description: `${form.description} (${i + 1}/${form.monthsCount})`,
          amount: Number(finalAmount.toFixed(2)),
          date: currentDate.toISOString().split('T')[0],
          category: form.category
        }

        await fetchWithAuth('http://localhost:8000/api/finances/expenses/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
      }
      showToast('Lançamentos recorrentes registrados!', 'success')
    } else {
      const payload = {
        wallet: defaultWalletId.value,
        description: form.description,
        amount: Number(finalAmount.toFixed(2)),
        date: form.date,
        category: form.category
      }

      const url = editingId.value 
        ? `http://localhost:8000/api/finances/expenses/${editingId.value}/`
        : 'http://localhost:8000/api/finances/expenses/'
        
      const method = editingId.value ? 'PUT' : 'POST'

      const response = await fetchWithAuth(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        showToast(editingId.value ? 'Lançamento atualizado com sucesso!' : 'Lançamento futuro registrado!', 'success')
      } else {
        showToast('Erro ao salvar os dados.', 'error')
        return
      }
    }
    closeModal()
    loadData()
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  }
}

const confirmDeletePrompt = (id) => {
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
    const response = await fetchWithAuth(`http://localhost:8000/api/finances/expenses/${itemToDelete.value}/`, {
      method: 'DELETE'
    })

    if (response.ok) {
      showToast('Lançamento excluído com sucesso!', 'success')
      loadData()
    } else {
      showToast('Erro ao excluir o lançamento.', 'error')
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
        <h1>Gastos Futuros</h1>
        <p>Programe e acompanhe seus próximos compromissos</p>
      </div>
      <div class="header-actions">
        <button @click="openModal('income')" class="action-btn btn-income">
          <span class="btn-icon">+</span> Receber
        </button>
        <button @click="openModal('expense')" class="action-btn btn-expense">
          <span class="btn-icon">-</span> Pagar
        </button>
      </div>
    </div>

    <div class="summary-cards">
      <div class="card summary-item highlight-card">
        <div class="card-icon-wrapper highlight-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        </div>
        <div class="card-data">
          <h3>Balanço Projetado</h3>
          <span :class="['summary-value', (totalFutureIncome - totalFutureExpense) >= 0 ? 'text-positive' : 'text-negative']">
            {{ formatCurrency(totalFutureIncome - totalFutureExpense) }}
          </span>
        </div>
      </div>
      
      <div class="card summary-item">
        <div class="card-icon-wrapper positive-bg">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
        </div>
        <div class="card-data">
          <h3>A Receber</h3>
          <span class="summary-value positive">{{ formatCurrency(totalFutureIncome) }}</span>
        </div>
      </div>

      <div class="card summary-item">
        <div class="card-icon-wrapper negative-bg">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline>
            <polyline points="17 18 23 18 23 12"></polyline>
          </svg>
        </div>
        <div class="card-data">
          <h3>A Pagar</h3>
          <span class="summary-value negative">{{ formatCurrency(totalFutureExpense) }}</span>
        </div>
      </div>
    </div>

    <div class="filters-section">
      <div class="search-box">
        <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input type="text" v-model="filters.search" placeholder="Buscar lançamentos futuros...">
      </div>
      
      <div class="filter-group">
        <select v-model="filters.type">
          <option value="all">Todos os lançamentos</option>
          <option value="income">Apenas a Receber</option>
          <option value="expense">Apenas a Pagar</option>
        </select>
      </div>
    </div>

    <div class="transactions-container">
      <table class="transaction-table">
        <thead>
          <tr>
            <th>Prazo</th>
            <th>Data</th>
            <th>Descrição</th>
            <th>Categoria</th>
            <th class="align-right">Valor</th>
            <th class="align-center">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredTransactions.length === 0">
            <td colspan="6" class="empty-state">Nenhum lançamento futuro programado.</td>
          </tr>
          <tr v-for="item in filteredTransactions" :key="item.id">
            <td>
              <span :class="['days-badge', item.daysRemaining <= 3 ? 'urgent' : item.daysRemaining <= 7 ? 'warning' : 'safe']">
                Em {{ item.daysRemaining }} dia{{ item.daysRemaining > 1 ? 's' : '' }}
              </span>
            </td>
            <td class="td-date fw-600">{{ item.date }}</td>
            <td class="fw-700 td-desc">{{ item.description }}</td>
            <td>
              <span class="category-tag">{{ item.category }}</span>
            </td>
            <td :class="['align-right fw-800', item.type === 'income' ? 'text-positive' : 'text-negative']">
              {{ item.type === 'income' ? '+' : '-' }} {{ formatCurrency(Math.abs(item.amount)) }}
            </td>
            <td class="align-center actions-cell">
              <button class="action-icon" title="Editar" @click="openModal(item.type, item)">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
              </button>
              <button class="action-icon icon-danger" title="Excluir" @click="confirmDeletePrompt(item.id)">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <FooterComp />

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <div class="modal-header">
          <h2>{{ editingId ? 'Editar Lançamento' : (modalType === 'income' ? 'Novo Recebimento' : 'Novo Gasto') }}</h2>
          <button class="close-btn" @click="closeModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>

        <form @submit.prevent="saveTransaction" class="modal-form">
          <div class="form-group">
            <label>Descrição</label>
            <input v-model="form.description" type="text" placeholder="Ex: Aluguel Mensal" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Valor (R$)</label>
              <input v-model="form.amount" type="number" step="0.01" min="0.01" placeholder="0.00" required />
            </div>

            <div class="form-group">
              <label>Data de Início/Vencimento</label>
              <input v-model="form.date" type="date" required />
            </div>
          </div>

          <div class="form-row align-center" v-if="!editingId">
            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="form.isMonthly" />
                Repetir mensalmente?
              </label>
            </div>
            <div class="form-group" v-if="form.isMonthly">
              <label>Qtd. Meses</label>
              <input v-model="form.monthsCount" type="number" min="2" max="60" required />
            </div>
          </div>

          <div class="form-group">
            <label>Categoria</label>
            <select v-model="form.category" required>
              <option value="" disabled>Selecione uma categoria</option>
              <option v-for="cat in currentCategories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
            <span v-if="currentCategories.length === 0" class="error-text" style="font-size:0.8rem; color:#dc2626; margin-top:4px;">Não há categorias cadastradas. Crie em Configurações.</span>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeModal">Cancelar</button>
            <button type="submit" :class="['btn-save', modalType === 'income' ? 'bg-positive' : 'bg-negative']">
              Agendar
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
      <div class="modal-container delete-modal">
        <div class="modal-header">
          <h2 class="text-negative">Excluir Lançamento</h2>
          <button class="close-btn" @click="closeDeleteModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="modal-body">
          <p>Tem certeza que deseja excluir este lançamento programado? Esta ação não poderá ser desfeita.</p>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="closeDeleteModal">Cancelar</button>
          <button type="button" class="btn-save bg-negative" @click="executeDelete">Sim, Excluir</button>
        </div>
      </div>
    </div>

  </SideLayout>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
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

.header-actions {
  display: flex;
  gap: 15px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 24px;
  border-radius: 14px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: white;
}

.action-btn:hover {
  transform: translateY(-2px);
}

.btn-icon {
  font-size: 1.3rem;
  font-weight: 900;
  line-height: 1;
}

.btn-income {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
}

.btn-income:hover {
  box-shadow: 0 15px 25px -5px rgba(16, 185, 129, 0.4);
}

.btn-expense {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3);
}

.btn-expense:hover {
  box-shadow: 0 15px 25px -5px rgba(239, 68, 68, 0.4);
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 35px;
}

.card {
  background: var(--bg-card);
  padding: 25px 30px;
  border-radius: 20px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.3s, border-color 0.3s;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.highlight-card {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border: none;
}

.card-data h3 {
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 8px 0;
  transition: color 0.3s;
}

.highlight-card .card-data h3 {
  color: #94a3b8;
}

.summary-value {
  font-size: 1.8rem;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.5px;
  color: var(--text-primary);
  display: block;
  transition: color 0.3s;
}

.text-positive { color: #059669; }
.text-negative { color: #dc2626; }

.card-icon-wrapper {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.positive-bg { background-color: var(--positive-bg); color: #10b981; }
.negative-bg { background-color: var(--negative-bg); color: #ef4444; }
.highlight-icon { background-color: rgba(255, 255, 255, 0.1); color: #f7b500; }

.filters-section {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 25px;
  background: var(--bg-card);
  padding: 20px;
  border-radius: 20px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  transition: background-color 0.3s, border-color 0.3s;
}

.search-box {
  flex: 2;
  min-width: 250px;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 16px;
  color: var(--text-secondary);
}

.search-box input {
  width: 100%;
  padding: 14px 15px 14px 45px;
  border: 1px solid var(--border-input);
  border-radius: 12px;
  font-size: 0.95rem;
  outline: none;
  transition: all 0.3s;
  background-color: var(--input-bg);
  color: var(--text-primary);
  font-family: 'Inter', sans-serif;
}

.search-box input:focus {
  border-color: #f7b500;
  background-color: var(--bg-card);
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.filter-group {
  flex: 1;
  min-width: 200px;
}

.filter-group select {
  width: 100%;
  padding: 14px 15px;
  border: 1px solid var(--border-input);
  border-radius: 12px;
  font-size: 0.95rem;
  outline: none;
  background-color: var(--input-bg);
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  color: var(--text-primary);
  transition: all 0.3s;
}

.filter-group select:focus {
  border-color: #f7b500;
  background-color: var(--bg-card);
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.transactions-container {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 10px 25px 25px 25px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  overflow-x: auto;
  transition: background-color 0.3s, border-color 0.3s;
}

.transaction-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 800px;
}

.transaction-table th,
.transaction-table td {
  padding: 18px 15px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
  transition: border-color 0.3s;
}

.transaction-table th {
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-top: 25px;
  transition: color 0.3s;
}

.transaction-table td {
  color: var(--text-primary);
  font-size: 1rem;
  transition: color 0.3s;
}

.transaction-table tr:last-child td {
  border-bottom: none;
}

.transaction-table tr {
  transition: background-color 0.2s;
}

.transaction-table tr:hover td {
  background-color: var(--bg-main);
}

.days-badge {
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.urgent { background-color: var(--negative-bg); color: #dc2626; }
.warning { background-color: rgba(245, 158, 11, 0.15); color: #d97706; }
.safe { background-color: var(--positive-bg); color: #059669; }

.td-date {
  color: var(--text-secondary) !important;
  font-size: 0.95rem !important;
}

.td-desc {
  color: var(--text-primary) !important;
}

.empty-state {
  text-align: center !important;
  padding: 50px !important;
  color: var(--text-secondary) !important;
  font-weight: 500;
}

.align-right { text-align: right !important; }
.align-center { text-align: center !important; }
.actions-cell { white-space: nowrap; }
.fw-600 { font-weight: 600; }
.fw-700 { font-weight: 700; }
.fw-800 { font-weight: 800; }

.category-tag {
  background-color: var(--neutral-bg);
  color: var(--text-secondary);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.action-icon {
  background: var(--bg-card);
  border: 1px solid var(--border-input);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  margin: 0 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-icon:hover {
  background: var(--bg-main);
  color: var(--text-primary);
  border-color: var(--text-secondary);
  transform: translateY(-2px);
}

.icon-danger:hover {
  background: var(--negative-bg);
  color: #dc2626;
  border-color: #fecaca;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-container {
  background: var(--bg-card);
  width: 100%;
  max-width: 480px;
  border-radius: 24px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-color);
  padding: 35px;
  transform: translateY(0);
  animation: modalSlideIn 0.3s ease-out;
  transition: background-color 0.3s, border-color 0.3s;
}

.delete-modal {
  max-width: 400px;
}

@keyframes modalSlideIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.modal-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.5rem;
  font-weight: 800;
  transition: color 0.3s;
}

.close-btn {
  background: var(--bg-main);
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 1.2rem;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--border-color);
  color: var(--text-primary);
}

.modal-body {
  color: var(--text-secondary);
  font-size: 1.05rem;
  line-height: 1.5;
  margin-bottom: 25px;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: flex;
  gap: 20px;
}

.align-center {
  align-items: flex-end;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.form-group label {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-secondary);
  transition: color 0.3s;
}

.form-group input,
.form-group select {
  padding: 16px;
  border: 1px solid var(--border-input);
  border-radius: 12px;
  font-size: 1rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s, background-color 0.3s, color 0.3s;
  background-color: var(--input-bg);
  color: var(--text-primary);
}

.form-group input:focus,
.form-group select:focus {
  border-color: #f7b500;
  background-color: var(--bg-card);
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.checkbox-group {
  flex-direction: row;
  align-items: center;
  margin-bottom: 5px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  font-weight: 600;
  color: var(--text-primary) !important;
  font-size: 1rem !important;
}

.checkbox-label input {
  width: 20px;
  height: 20px;
  cursor: pointer;
  margin: 0;
}

.modal-actions {
  display: flex;
  gap: 15px;
  margin-top: 10px;
}

.btn-cancel {
  flex: 1;
  padding: 16px;
  background-color: var(--bg-main);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: var(--border-color);
  color: var(--text-primary);
}

.btn-save {
  flex: 1;
  padding: 16px;
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-save:hover {
  transform: translateY(-2px);
}

.bg-positive { 
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
}

.bg-negative { 
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3);
}

@media (max-width: 1024px) {
  .category-dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  .action-btn {
    width: 100%;
  }

  .filters-section {
    flex-direction: column;
  }

  .search-box, .filter-group {
    width: 100%;
  }

  .form-row {
    flex-direction: column;
    gap: 20px;
  }

  .summary-table-head,
  .summary-table-row {
    grid-template-columns: 1.3fr 1fr 1fr;
  }

  .summary-table-head span:nth-child(4),
  .summary-table-head span:nth-child(5),
  .summary-table-row span:nth-child(4),
  .summary-table-row span:nth-child(5) {
    display: none;
  }

  .category-card-header {
    flex-direction: column;
  }
}
</style>