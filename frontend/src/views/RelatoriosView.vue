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
    const expensesRes = await fetchWithAuth('http://localhost:8000/api/finances/expenses/')

    if (expensesRes.ok) {
      const expenses = await expensesRes.json()

      transactions.value = expenses.map(item => {
        const val = parseFloat(item.amount || item.value || 0)
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
          type: val >= 0 ? 'income' : 'expense'
        }
      })
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

const totalIncome = computed(() => {
  return transactions.value
    .filter(t => t.type === 'income')
    .reduce((acc, curr) => acc + curr.amount, 0)
})

const totalExpense = computed(() => {
  return transactions.value
    .filter(t => t.type === 'expense')
    .reduce((acc, curr) => acc + Math.abs(curr.amount), 0)
})

const savingsRate = computed(() => {
  if (totalIncome.value === 0) return 0
  const rate = ((totalIncome.value - totalExpense.value) / totalIncome.value) * 100
  return rate > 0 ? rate : 0
})

const expensesByCategory = computed(() => {
  const expenses = transactions.value.filter(t => t.type === 'expense')
  const total = totalExpense.value
  
  if (total === 0) return []

  const groups = expenses.reduce((acc, curr) => {
    if (!acc[curr.category]) acc[curr.category] = 0
    acc[curr.category] += Math.abs(curr.amount)
    return acc
  }, {})

  return Object.keys(groups).map(key => {
    return {
      name: key,
      amount: groups[key],
      percentage: Math.round((groups[key] / total) * 100)
    }
  }).sort((a, b) => b.amount - a.amount)
})

const incomeByCategory = computed(() => {
  const incomes = transactions.value.filter(t => t.type === 'income')
  const total = totalIncome.value
  
  if (total === 0) return []

  const groups = incomes.reduce((acc, curr) => {
    if (!acc[curr.category]) acc[curr.category] = 0
    acc[curr.category] += curr.amount
    return acc
  }, {})

  return Object.keys(groups).map(key => {
    return {
      name: key,
      amount: groups[key],
      percentage: Math.round((groups[key] / total) * 100)
    }
  }).sort((a, b) => b.amount - a.amount)
})

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />

  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Relatórios e Análises</h1>
        <p>Visão detalhada de como seu dinheiro está sendo distribuído</p>
      </div>
    </div>

    <div class="summary-cards">
      <div class="card summary-item highlight-card">
        <div class="card-data">
          <h3>Taxa de Economia</h3>
          <span class="summary-value text-white">{{ savingsRate.toFixed(1) }}%</span>
          <p class="summary-subtitle text-white-muted">da renda foi poupada</p>
        </div>
        <div class="card-icon-wrapper highlight-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v20"></path>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
          </svg>
        </div>
      </div>
      
      <div class="card summary-item">
        <div class="card-data">
          <h3>Total de Entradas</h3>
          <span class="summary-value positive">{{ formatCurrency(totalIncome) }}</span>
        </div>
        <div class="card-icon-wrapper positive-bg">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
        </div>
      </div>

      <div class="card summary-item">
        <div class="card-data">
          <h3>Total de Saídas</h3>
          <span class="summary-value negative">{{ formatCurrency(totalExpense) }}</span>
        </div>
        <div class="card-icon-wrapper negative-bg">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline>
            <polyline points="17 18 23 18 23 12"></polyline>
          </svg>
        </div>
      </div>
    </div>

    <div class="reports-grid">
      <div class="report-section">
        <div class="section-header">
          <h2>Despesas por Categoria</h2>
        </div>
        <div class="categories-list">
          <div v-if="expensesByCategory.length === 0" class="empty-state">
            Nenhuma despesa registrada.
          </div>
          <div v-for="cat in expensesByCategory" :key="cat.name" class="category-item">
            <div class="cat-info">
              <span class="cat-name">{{ cat.name }}</span>
              <span class="cat-amount fw-700">{{ formatCurrency(cat.amount) }}</span>
            </div>
            <div class="cat-bar-bg">
              <div class="cat-bar-fill bar-negative" :style="{ width: cat.percentage + '%' }"></div>
            </div>
            <span class="cat-percentage">{{ cat.percentage }}%</span>
          </div>
        </div>
      </div>

      <div class="report-section">
        <div class="section-header">
          <h2>Entradas por Categoria</h2>
        </div>
        <div class="categories-list">
          <div v-if="incomeByCategory.length === 0" class="empty-state">
            Nenhuma entrada registrada.
          </div>
          <div v-for="cat in incomeByCategory" :key="cat.name" class="category-item">
            <div class="cat-info">
              <span class="cat-name">{{ cat.name }}</span>
              <span class="cat-amount fw-700">{{ formatCurrency(cat.amount) }}</span>
            </div>
            <div class="cat-bar-bg">
              <div class="cat-bar-fill bar-positive" :style="{ width: cat.percentage + '%' }"></div>
            </div>
            <span class="cat-percentage">{{ cat.percentage }}%</span>
          </div>
        </div>
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
  margin-bottom: 30px;
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

.summary-subtitle {
  margin: 5px 0 0 0;
  font-size: 0.85rem;
}

.text-white { color: #f8fafc; }
.text-white-muted { color: #94a3b8; }
.positive { color: #059669; }
.negative { color: #dc2626; }

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

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 30px;
  margin-bottom: 40px;
}

.report-section {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 30px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  transition: background-color 0.3s, border-color 0.3s;
}

.section-header {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid var(--border-input);
  transition: border-color 0.3s;
}

.section-header h2 {
  color: var(--text-primary);
  font-size: 1.3rem;
  font-weight: 800;
  margin: 0;
  transition: color 0.3s;
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cat-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cat-name {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 0.95rem;
  transition: color 0.3s;
}

.cat-amount {
  color: var(--text-primary);
  font-size: 0.95rem;
  transition: color 0.3s;
}

.cat-bar-bg {
  width: 100%;
  height: 8px;
  background-color: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  transition: background-color 0.3s;
}

.cat-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

.bar-negative { background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%); }
.bar-positive { background: linear-gradient(90deg, #10b981 0%, #059669 100%); }

.cat-percentage {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 700;
  text-align: right;
  transition: color 0.3s;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: var(--text-secondary);
  font-weight: 500;
  transition: color 0.3s;
}

.fw-700 { font-weight: 700; }

@media (max-width: 768px) {
  .reports-grid {
    grid-template-columns: 1fr;
  }
}
</style>