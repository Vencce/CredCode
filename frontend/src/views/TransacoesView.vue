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

const form = reactive({
  description: '',
  amount: '',
  date: new Date().toISOString().split('T')[0],
  category: '',
  isMonthly: false,
  monthsCount: 12
})

const filters = reactive({
  search: '',
  type: 'all',
  period: 'all',
  category: 'all'
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

const uniqueCategories = computed(() => {
  const cats = new Set(transactions.value.map(t => t.category))
  return Array.from(cats).sort()
})

const filteredTransactions = computed(() => {
  const now = new Date()
  now.setHours(0, 0, 0, 0)

  return transactions.value.filter(t => {
    const searchString = filters.search.toLowerCase()
    const matchesSearch = t.description.toLowerCase().includes(searchString) ||
      t.category.toLowerCase().includes(searchString)
    const matchesType = filters.type === 'all' || t.type === filters.type
    const matchesCategory = filters.category === 'all' || t.category === filters.category
    
    let matchesPeriod = true
    if (filters.period !== 'all') {
      const days = parseInt(filters.period)
      const tDate = new Date(t.rawDate)
      tDate.setHours(0, 0, 0, 0)
      const diffTime = now.getTime() - tDate.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      matchesPeriod = diffDays >= 0 && diffDays <= days
    }

    return matchesSearch && matchesType && matchesPeriod && matchesCategory
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

const totalBalance = computed(() => totalIncome.value - totalExpense.value)

const totalTransactionsCount = computed(() => filteredTransactions.value.length)

const categorySummary = computed(() => {
  const map = {}

  filteredTransactions.value.forEach(item => {
    const key = item.category || 'Sem categoria'

    if (!map[key]) {
      map[key] = {
        category: key,
        income: 0,
        expense: 0,
        total: 0,
        count: 0
      }
    }

    if (item.type === 'income') {
      map[key].income += Math.abs(item.amount)
    } else {
      map[key].expense += Math.abs(item.amount)
    }

    map[key].total = map[key].income + map[key].expense
    map[key].count += 1
  })

  const list = Object.values(map)

  const grandTotal = list.reduce((acc, curr) => acc + curr.total, 0) || 1

  return list
    .map(item => ({
      category: item.category,
      income: item.income,
      expense: item.expense,
      total: item.total,
      count: item.count,
      balance: item.income - item.expense,
      percentage: (item.total / grandTotal) * 100
    }))
    .sort((a, b) => b.total - a.total)
})

const expenseCategories = computed(() => {
  const total = totalExpense.value || 1

  return categorySummary.value
    .filter(item => item.expense > 0)
    .map(item => ({
      ...item,
      percentageExpense: (item.expense / total) * 100
    }))
    .sort((a, b) => b.expense - a.expense)
})

const incomeCategories = computed(() => {
  const total = totalIncome.value || 1

  return categorySummary.value
    .filter(item => item.income > 0)
    .map(item => ({
      ...item,
      percentageIncome: (item.income / total) * 100
    }))
    .sort((a, b) => b.income - a.income)
})

const topExpenseCategory = computed(() => expenseCategories.value[0] || null)
const topIncomeCategory = computed(() => incomeCategories.value[0] || null)

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
    form.date = new Date().toISOString().split('T')[0]
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
      showToast('Transações recorrentes registradas!', 'success')
      closeModal()
      loadData()
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
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        showToast(editingId.value ? 'Transação atualizada com sucesso!' : 'Transação registrada com sucesso!', 'success')
        closeModal()
        loadData()
      } else {
        showToast('Erro ao salvar os dados da transação.', 'error')
      }
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

  try {
    const response = await fetchWithAuth(`http://localhost:8000/api/finances/expenses/${itemToDelete.value}/`, {
      method: 'DELETE'
    })

    if (response.ok) {
      showToast('Transação excluída com sucesso!', 'success')
      loadData()
    } else {
      showToast('Erro ao excluir a transação.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  } finally {
    closeDeleteModal()
  }
}

const exportToCSV = () => {
  if (filteredTransactions.value.length === 0) {
    showToast('Nenhuma transação para exportar.', 'error')
    return
  }
  
  const headers = ['Data', 'Descricao', 'Categoria', 'Tipo', 'Valor']
  const rows = filteredTransactions.value.map(t => [
    t.date,
    `"${t.description}"`,
    `"${t.category}"`,
    t.type === 'income' ? 'Entrada' : 'Saida',
    t.amount.toString().replace('.', ',')
  ])
  
  const csvContent = [headers.join(';'), ...rows.map(r => r.join(';'))].join('\n')
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `transacoes_${new Date().toISOString().split('T')[0]}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  showToast('Exportação concluída!', 'success')
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
        <button @click="exportToCSV" class="action-btn btn-neutral">
          <span class="btn-icon">⬇️</span> Exportar CSV
        </button>
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

      <div class="filter-group">
        <select v-model="filters.category">
          <option value="all">Todas as categorias</option>
          <option v-for="cat in uniqueCategories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
    </div>

    <section class="dashboard-overview">
      <div class="overview-cards">
        <div class="card overview-card">
          <div class="card-icon-wrapper positive-bg">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
              <polyline points="17 6 23 6 23 12"></polyline>
            </svg>
          </div>
          <div class="card-data">
            <h3>Total de Entradas</h3>
            <span class="summary-value positive">{{ formatCurrency(totalIncome) }}</span>
          </div>
        </div>

        <div class="card overview-card">
          <div class="card-icon-wrapper negative-bg">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline>
              <polyline points="17 18 23 18 23 12"></polyline>
            </svg>
          </div>
          <div class="card-data">
            <h3>Total de Saídas</h3>
            <span class="summary-value negative">{{ formatCurrency(totalExpense) }}</span>
          </div>
        </div>

        <div class="card overview-card">
          <div class="card-icon-wrapper neutral-bg">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="1" x2="12" y2="23"></line>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
            </svg>
          </div>
          <div class="card-data">
            <h3>Saldo do Período</h3>
            <span :class="['summary-value', totalBalance >= 0 ? 'positive' : 'negative']">
              {{ formatCurrency(totalBalance) }}
            </span>
          </div>
        </div>

        <div class="card overview-card">
          <div class="card-icon-wrapper neutral-bg">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2"></rect>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
          </div>
          <div class="card-data">
            <h3>Transações</h3>
            <span class="summary-value">{{ totalTransactionsCount }}</span>
          </div>
        </div>
      </div>

      <div class="category-dashboard-grid">
        <div class="category-card">
          <div class="category-card-header">
            <div>
              <h3>Saídas por Categoria</h3>
              <p>Distribuição detalhada dos gastos no período filtrado</p>
            </div>
            <span v-if="topExpenseCategory" class="highlight-badge negative-soft">
              Maior gasto: {{ topExpenseCategory.category }}
            </span>
          </div>

          <div v-if="expenseCategories.length === 0" class="empty-category-state">
            Nenhuma saída encontrada no período atual.
          </div>

          <div v-else class="category-list">
            <div v-for="item in expenseCategories" :key="'exp-' + item.category" class="category-row">
              <div class="category-row-top">
                <div class="category-main">
                  <span class="category-name">{{ item.category }}</span>
                  <span class="category-count">{{ item.count }} transação(ões)</span>
                </div>
                <div class="category-values">
                  <strong class="negative">{{ formatCurrency(item.expense) }}</strong>
                  <span>{{ item.percentageExpense.toFixed(1) }}%</span>
                </div>
              </div>
              <div class="progress-track">
                <div class="progress-fill negative-fill" :style="{ width: item.percentageExpense + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="category-card">
          <div class="category-card-header">
            <div>
              <h3>Entradas por Categoria</h3>
              <p>Distribuição detalhada das receitas no período filtrado</p>
            </div>
            <span v-if="topIncomeCategory" class="highlight-badge positive-soft">
              Maior entrada: {{ topIncomeCategory.category }}
            </span>
          </div>

          <div v-if="incomeCategories.length === 0" class="empty-category-state">
            Nenhuma entrada encontrada no período atual.
          </div>

          <div v-else class="category-list">
            <div v-for="item in incomeCategories" :key="'inc-' + item.category" class="category-row">
              <div class="category-row-top">
                <div class="category-main">
                  <span class="category-name">{{ item.category }}</span>
                  <span class="category-count">{{ item.count }} transação(ões)</span>
                </div>
                <div class="category-values">
                  <strong class="positive">{{ formatCurrency(item.income) }}</strong>
                  <span>{{ item.percentageIncome.toFixed(1) }}%</span>
                </div>
              </div>
              <div class="progress-track">
                <div class="progress-fill positive-fill" :style="{ width: item.percentageIncome + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="category-card full-width-card">
        <div class="category-card-header">
          <div>
            <h3>Resumo Geral por Categoria</h3>
            <p>Comparativo consolidado entre entradas, saídas e saldo</p>
          </div>
        </div>

        <div v-if="categorySummary.length === 0" class="empty-category-state">
          Nenhuma categoria encontrada com os filtros atuais.
        </div>

        <div v-else class="category-summary-table">
          <div class="summary-table-head">
            <span>Categoria</span>
            <span>Entradas</span>
            <span>Saídas</span>
            <span>Saldo</span>
            <span>Volume</span>
          </div>

          <div
            v-for="item in categorySummary"
            :key="'sum-' + item.category"
            class="summary-table-row"
          >
            <span class="summary-cat-name">{{ item.category }}</span>
            <span class="positive">{{ formatCurrency(item.income) }}</span>
            <span class="negative">{{ formatCurrency(item.expense) }}</span>
            <span :class="item.balance >= 0 ? 'positive' : 'negative'">
              {{ formatCurrency(item.balance) }}
            </span>
            <span>{{ item.percentage.toFixed(1) }}%</span>
          </div>
        </div>
      </div>
    </section>

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

.btn-neutral {
  background-color: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-input);
  box-shadow: var(--shadow-sm);
}

.btn-neutral:hover {
  background-color: var(--bg-main);
  border-color: var(--text-secondary);
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
  min-width: 180px;
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

.dashboard-overview {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 35px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.overview-card {
  min-height: 110px;
}

.category-dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.category-card {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 24px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  transition: background-color 0.3s, border-color 0.3s;
}

.full-width-card {
  width: 100%;
}

.category-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 15px;
  margin-bottom: 22px;
}

.category-card-header h3 {
  margin: 0 0 6px 0;
  color: var(--text-primary);
  font-size: 1.15rem;
  font-weight: 800;
  transition: color 0.3s;
}

.category-card-header p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.95rem;
  transition: color 0.3s;
}

.highlight-badge {
  white-space: nowrap;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 0.82rem;
  font-weight: 700;
}

.positive-soft {
  background: var(--positive-bg);
  color: #059669;
}

.negative-soft {
  background: var(--negative-bg);
  color: #dc2626;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.category-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.category-row-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.category-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  transition: color 0.3s;
}

.category-count {
  font-size: 0.85rem;
  color: var(--text-secondary);
  transition: color 0.3s;
}

.category-values {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  font-size: 0.9rem;
  color: var(--text-secondary);
  transition: color 0.3s;
}

.progress-track {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: var(--border-color);
  overflow: hidden;
  transition: background-color 0.3s;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.positive-fill {
  background: linear-gradient(90deg, #34d399 0%, #10b981 100%);
}

.negative-fill {
  background: linear-gradient(90deg, #f87171 0%, #ef4444 100%);
}

.empty-category-state {
  color: var(--text-secondary);
  font-weight: 500;
  padding: 20px 0;
  transition: color 0.3s;
}

.category-summary-table {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-table-head,
.summary-table-row {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 1fr 0.8fr;
  gap: 14px;
  align-items: center;
}

.summary-table-head {
  color: var(--text-secondary);
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 700;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-input);
  transition: color 0.3s, border-color 0.3s;
}

.summary-table-row {
  padding: 14px 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.95rem;
  transition: border-color 0.3s;
}

.summary-table-row:last-child {
  border-bottom: none;
}

.summary-cat-name {
  font-weight: 700;
  color: var(--text-primary);
  transition: color 0.3s;
}

.card {
  background: var(--bg-card);
  padding: 20px 25px;
  border-radius: 20px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 20px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.3s, border-color 0.3s;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.card-icon-wrapper {
  width: 55px;
  height: 55px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.positive-bg { background-color: var(--positive-bg); color: #10b981; }
.negative-bg { background-color: var(--negative-bg); color: #ef4444; }
.neutral-bg { background-color: var(--neutral-bg); color: var(--text-secondary); }

.card-data h3 {
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 5px 0;
  transition: color 0.3s;
}

.summary-value {
  font-size: 1.6rem;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.5px;
  color: var(--text-primary);
  transition: color 0.3s;
}

.positive { color: #059669; }
.negative { color: #dc2626; }

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
.text-positive { color: #059669 !important; }
.text-negative { color: #dc2626 !important; }

.category-tag {
  background-color: var(--neutral-bg);
  color: var(--text-secondary);
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

.type-badge.income { background-color: var(--positive-bg); color: #059669; }
.type-badge.expense { background-color: var(--negative-bg); color: #dc2626; }

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
  background-color: var(--border-color);
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