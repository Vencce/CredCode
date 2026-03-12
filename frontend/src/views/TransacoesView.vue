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

const showModal = ref(false)
const modalType = ref('expense')
const editingId = ref(null)

const showDeleteModal = ref(false)
const itemToDelete = ref(null)

const predefinedCategories = {
  income: ['Salário', 'Investimentos', 'Vendas', 'Serviços', 'Outros'],
  expense: ['Alimentação', 'Transporte', 'Moradia', 'Contas', 'Saúde', 'Lazer', 'Outros']
}

const form = reactive({
  description: '',
  amount: '',
  date: new Date().toISOString().split('T')[0],
  category: ''
})

const filters = reactive({
  search: '',
  type: 'all',
  period: 'all'
})

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

const loadData = async (token) => {
  try {
    const walletRes = await fetch('http://localhost:8000/api/finances/wallets/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (walletRes.ok) {
      const wallets = await walletRes.json()
      if (wallets.length > 0) defaultWalletId.value = wallets[0].id
    }

    const expensesRes = await fetch('http://localhost:8000/api/finances/expenses/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (expensesRes.ok) {
      const expenses = await expensesRes.json()

      transactions.value = expenses.map(item => {
        const val = parseFloat(item.amount || item.value || 0)
        const dateVal = item.date || item.created_at || ''
        const dateParts = dateVal.split('-')
        let formattedDate = dateVal
        let rawDate = new Date()

        if (dateParts.length === 3) {
          formattedDate = `${dateParts[2].substring(0, 2)}/${dateParts[1]}/${dateParts[0]}`
          rawDate = new Date(parseInt(dateParts[0]), parseInt(dateParts[1]) - 1, parseInt(dateParts[2].substring(0, 2)))
        }

        let cat = item.category || 'Geral'
        let desc = item.description || 'Sem descrição'

        if (desc.startsWith('[')) {
          const closingBracket = desc.indexOf(']')
          if (closingBracket !== -1) {
            cat = desc.substring(1, closingBracket)
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
          rawDate: rawDate
        }
      }).reverse()
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
    loadData(token)
  }
})

const filteredTransactions = computed(() => {
  const now = new Date()
  now.setHours(0, 0, 0, 0)

  return transactions.value.filter(t => {
    const searchString = filters.search.toLowerCase()
    const matchesSearch = t.description.toLowerCase().includes(searchString) ||
      t.category.toLowerCase().includes(searchString)
    const matchesType = filters.type === 'all' || t.type === filters.type
    
    let matchesPeriod = true
    if (filters.period !== 'all') {
      const days = parseInt(filters.period)
      const tDate = new Date(t.rawDate)
      tDate.setHours(0, 0, 0, 0)
      const diffTime = now.getTime() - tDate.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      matchesPeriod = diffDays >= 0 && diffDays <= days
    }

    return matchesSearch && matchesType && matchesPeriod
  })
})

const totalIncome = computed(() => {
  return filteredTransactions.value
    .filter(t => t.type === 'income')
    .reduce((acc, curr) => acc + curr.amount, 0)
})

const totalExpense = computed(() => {
  return filteredTransactions.value
    .filter(t => t.type === 'expense')
    .reduce((acc, curr) => acc + Math.abs(curr.amount), 0)
})

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}

const currentCategories = computed(() => {
  return modalType.value === 'income' ? predefinedCategories.income : predefinedCategories.expense
})

const openModal = (type, item = null) => {
  modalType.value = type
  
  if (item) {
    editingId.value = item.id
    form.description = item.description
    form.amount = Math.abs(item.amount)
    form.category = item.category
    
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
    form.date = new Date().toISOString().split('T')[0]
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

  const token = localStorage.getItem('access_token')
  let finalAmount = parseFloat(form.amount)

  if (modalType.value === 'expense') {
    finalAmount = -Math.abs(finalAmount)
  } else {
    finalAmount = Math.abs(finalAmount)
  }

  const payload = {
    wallet: defaultWalletId.value,
    description: `[${form.category}] ${form.description}`,
    amount: finalAmount,
    date: form.date
  }

  try {
    const url = editingId.value 
      ? `http://localhost:8000/api/finances/expenses/${editingId.value}/`
      : 'http://localhost:8000/api/finances/expenses/'
      
    const method = editingId.value ? 'PUT' : 'POST'

    const response = await fetch(url, {
      method: method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (response.ok) {
      showToast(editingId.value ? 'Transação atualizada com sucesso!' : 'Transação registrada com sucesso!', 'success')
      closeModal()
      loadData(token)
    } else {
      showToast('Erro ao salvar os dados da transação.', 'error')
    }
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

  const token = localStorage.getItem('access_token')
  
  try {
    const response = await fetch(`http://localhost:8000/api/finances/expenses/${itemToDelete.value}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (response.ok) {
      showToast('Transação excluída com sucesso!', 'success')
      loadData(token)
    } else {
      showToast('Erro ao excluir a transação.', 'error')
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
        <h1>Transações</h1>
        <p>Acompanhe e filtre todas as suas movimentações</p>
      </div>
      <div class="header-actions">
        <button @click="openModal('income')" class="action-btn btn-income">
          <span class="btn-icon">+</span> Nova Entrada
        </button>
        <button @click="openModal('expense')" class="action-btn btn-expense">
          <span class="btn-icon">-</span> Novo Gasto
        </button>
      </div>
    </div>

    <div class="filters-section">
      <div class="search-box">
        <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input type="text" v-model="filters.search" placeholder="Buscar por descrição ou categoria...">
      </div>
      
      <div class="filter-group">
        <select v-model="filters.type">
          <option value="all">Todas as transações</option>
          <option value="income">Apenas Entradas</option>
          <option value="expense">Apenas Saídas</option>
        </select>
      </div>

      <div class="filter-group">
        <select v-model="filters.period">
          <option value="all">Todo o período</option>
          <option value="7">Últimos 7 dias</option>
          <option value="15">Últimos 15 dias</option>
          <option value="30">Últimos 30 dias</option>
          <option value="60">Últimos 2 meses</option>
        </select>
      </div>
    </div>

    <div class="summary-cards">
      <div class="card summary-item">
        <div class="card-icon-wrapper positive-bg">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
        </div>
        <div class="card-data">
          <h3>Entradas</h3>
          <span class="summary-value positive">{{ formatCurrency(totalIncome) }}</span>
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
          <h3>Saídas</h3>
          <span class="summary-value negative">{{ formatCurrency(totalExpense) }}</span>
        </div>
      </div>
      <div class="card summary-item">
        <div class="card-icon-wrapper neutral-bg">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="1" x2="12" y2="23"></line>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
        </div>
        <div class="card-data">
          <h3>Balanço</h3>
          <span :class="['summary-value', (totalIncome - totalExpense) >= 0 ? 'positive' : 'negative']">
            {{ formatCurrency(totalIncome - totalExpense) }}
          </span>
        </div>
      </div>
    </div>

    <div class="transactions-container">
      <table class="transaction-table">
        <thead>
          <tr>
            <th>Data</th>
            <th>Descrição</th>
            <th>Categoria</th>
            <th>Tipo</th>
            <th class="align-right">Valor</th>
            <th class="align-center">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredTransactions.length === 0">
            <td colspan="6" class="empty-state">Nenhuma transação encontrada com os filtros atuais.</td>
          </tr>
          <tr v-for="item in filteredTransactions" :key="item.id">
            <td class="td-date">{{ item.date }}</td>
            <td class="fw-600 td-desc">{{ item.description }}</td>
            <td>
              <span class="category-tag">{{ item.category }}</span>
            </td>
            <td>
              <span :class="['type-badge', item.type]">
                {{ item.type === 'income' ? 'Entrada' : 'Saída' }}
              </span>
            </td>
            <td :class="['align-right fw-700', item.type === 'income' ? 'text-positive' : 'text-negative']">
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
          <h2>{{ editingId ? 'Editar Transação' : (modalType === 'income' ? 'Nova Entrada' : 'Novo Gasto') }}</h2>
          <button class="close-btn" @click="closeModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>

        <form @submit.prevent="saveTransaction" class="modal-form">
          <div class="form-group">
            <label>Descrição</label>
            <input v-model="form.description" type="text" placeholder="Ex: Conta de Luz" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Valor (R$)</label>
              <input v-model="form.amount" type="number" step="0.01" min="0.01" placeholder="0.00" required />
            </div>

            <div class="form-group">
              <label>Data</label>
              <input v-model="form.date" type="date" required />
            </div>
          </div>

          <div class="form-group">
            <label>Categoria</label>
            <select v-model="form.category" required>
              <option value="" disabled>Selecione uma categoria</option>
              <option v-for="cat in currentCategories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeModal">Cancelar</button>
            <button type="submit" :class="['btn-save', modalType === 'income' ? 'bg-positive' : 'bg-negative']">
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
      <div class="modal-container delete-modal">
        <div class="modal-header">
          <h2 class="text-negative">Excluir Transação</h2>
          <button class="close-btn" @click="closeDeleteModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="modal-body">
          <p>Tem certeza que deseja excluir esta transação? Esta ação não poderá ser desfeita.</p>
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

.filters-section {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 25px;
  background: white;
  padding: 20px;
  border-radius: 20px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.02);
  border: 1px solid #f1f5f9;
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
  color: #94a3b8;
}

.search-box input {
  width: 100%;
  padding: 14px 15px 14px 45px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  font-size: 0.95rem;
  outline: none;
  transition: all 0.3s;
  background-color: #f8fafc;
  color: #0f172a;
  font-family: 'Inter', sans-serif;
}

.search-box input:focus {
  border-color: #f7b500;
  background-color: white;
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.filter-group {
  flex: 1;
  min-width: 180px;
}

.filter-group select {
  width: 100%;
  padding: 14px 15px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  font-size: 0.95rem;
  outline: none;
  background-color: #f8fafc;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  color: #0f172a;
  transition: all 0.3s;
}

.filter-group select:focus {
  border-color: #f7b500;
  background-color: white;
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 35px;
}

.card {
  background: white;
  padding: 20px 25px;
  border-radius: 20px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.02);
  border: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05);
}

.card-icon-wrapper {
  width: 55px;
  height: 55px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.positive-bg { background-color: #ecfdf5; color: #10b981; }
.negative-bg { background-color: #fef2f2; color: #ef4444; }
.neutral-bg { background-color: #f8fafc; color: #64748b; }

.card-data h3 {
  color: #64748b;
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 5px 0;
}

.summary-value {
  font-size: 1.6rem;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.5px;
  color: #0f172a;
}

.positive { color: #059669; }
.negative { color: #dc2626; }

.transactions-container {
  background: white;
  border-radius: 20px;
  padding: 10px 25px 25px 25px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.02);
  border: 1px solid #f1f5f9;
  overflow-x: auto;
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
  border-bottom: 1px solid #f1f5f9;
}

.transaction-table th {
  color: #64748b;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-top: 25px;
}

.transaction-table td {
  color: #334155;
  font-size: 1rem;
}

.transaction-table tr:last-child td {
  border-bottom: none;
}

.transaction-table tr {
  transition: background-color 0.2s;
}

.transaction-table tr:hover td {
  background-color: #f8fafc;
}

.td-date {
  color: #64748b !important;
  font-size: 0.95rem !important;
}

.td-desc {
  color: #0f172a !important;
}

.empty-state {
  text-align: center !important;
  padding: 50px !important;
  color: #94a3b8 !important;
  font-weight: 500;
}

.align-right { text-align: right !important; }
.align-center { text-align: center !important; }
.actions-cell { white-space: nowrap; }
.fw-600 { font-weight: 600; }
.fw-700 { font-weight: 700; }
.text-positive { color: #059669 !important; }
.text-negative { color: #dc2626 !important; }

.category-tag {
  background-color: #f1f5f9;
  color: #475569;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.type-badge {
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.type-badge.income { background-color: #ecfdf5; color: #059669; }
.type-badge.expense { background-color: #fef2f2; color: #dc2626; }

.action-icon {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  padding: 8px;
  margin: 0 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-icon:hover {
  background: #f8fafc;
  color: #0f172a;
  border-color: #cbd5e1;
  transform: translateY(-2px);
}

.icon-danger:hover {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fecaca;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-container {
  background: white;
  width: 100%;
  max-width: 480px;
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  padding: 35px;
  transform: translateY(0);
  animation: modalSlideIn 0.3s ease-out;
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
  color: #0f172a;
  font-size: 1.5rem;
  font-weight: 800;
}

.close-btn {
  background: #f1f5f9;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.modal-body {
  color: #475569;
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

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.form-group label {
  font-size: 0.95rem;
  font-weight: 600;
  color: #475569;
}

.form-group input,
.form-group select {
  padding: 16px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  font-size: 1rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
  background-color: #f8fafc;
  color: #0f172a;
}

.form-group input:focus,
.form-group select:focus {
  border-color: #f7b500;
  background-color: white;
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.modal-actions {
  display: flex;
  gap: 15px;
  margin-top: 10px;
}

.btn-cancel {
  flex: 1;
  padding: 16px;
  background-color: #f1f5f9;
  color: #475569;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-cancel:hover {
  background-color: #e2e8f0;
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
  transition: transform 0.2s, box-shadow 0.2s;
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
}
</style>