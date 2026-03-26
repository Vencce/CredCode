<script setup>
import { ref, onMounted, onUnmounted, reactive, computed, nextTick, shallowRef, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
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
  name: 'Usuário',
  balance: 0,
  income: 0,
  expenses: 0
})

const displayedBalance = ref(0)
const totalInvestments = ref(0)
const totalGoals = ref(0)

const totalBalance = computed(() => userData.balance + userData.income - userData.expenses)

const recentTransactions = ref([])
const recentTransactionsLimited = computed(() => recentTransactions.value.slice(0, 5))

const defaultWalletId = ref(null)
const cards = ref([])
const userCategories = ref([])

const showModal = ref(false)
const modalType = ref('expense')

const chartRef = ref(null)
const chartInstance = shallowRef(null) 

const form = reactive({
  description: '',
  amount: '',
  date: new Date().toISOString().split('T')[0],
  category: '',
  paymentMethod: 'account',
  cardId: '',
  isInstallment: false,
  installmentsCount: 2,
  isMonthly: false,
  monthsCount: 12
})

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

const animateValue = (start, end, duration) => {
  let startTimestamp = null
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp
    const progress = Math.min((timestamp - startTimestamp) / duration, 1)
    const easeOutQuart = 1 - Math.pow(1 - progress, 4)
    displayedBalance.value = start + (end - start) * easeOutQuart
    if (progress < 1) {
      window.requestAnimationFrame(step)
    } else {
      displayedBalance.value = end
    }
  }
  window.requestAnimationFrame(step)
}

watch(totalBalance, (newVal) => {
  animateValue(0, newVal, 1500)
})

const handleThemeChange = () => {
  if (chartInstance.value) {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
    chartInstance.value.setOption({
      legend: {
        textStyle: { color: isDark ? '#94a3b8' : '#64748b' }
      }
    })
  }
}

const initChart = () => {
  if (!chartRef.value) return
  
  if (!chartInstance.value) {
    chartInstance.value = echarts.init(chartRef.value)
  }

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: R$ {c} ({d}%)'
    },
    legend: {
      bottom: '5%',
      left: 'center',
      textStyle: { color: isDark ? '#94a3b8' : '#64748b', fontWeight: 600 }
    },
    color: ['#10b981', '#ef4444'], 
    series: [
      {
        name: 'Movimentações',
        type: 'pie',
        radius: ['45%', '75%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: isDark ? '#0f172a' : '#fff',
          borderWidth: 4
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 18, fontWeight: 'bold', color: isDark ? '#f8fafc' : '#0f172a' }
        },
        labelLine: { show: false },
        data: [
          { value: userData.income, name: 'Entradas' },
          { value: userData.expenses, name: 'Saídas' }
        ]
      }
    ]
  }

  chartInstance.value.setOption(option)
}

const handleResize = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
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

const loadCards = () => {
  const saved = localStorage.getItem('finances_cards')
  if (saved) {
    cards.value = JSON.parse(saved)
  }
}

const loadData = async () => {
  try {
    let baseBalance = 0
    
    const profileRes = await fetchWithAuth('http://localhost:8000/api/finances/profile/')
    
    if (profileRes.ok) {
      const data = await profileRes.json()
      if (data.full_name) userData.name = data.full_name
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
      } else {
        const createWalletRes = await fetchWithAuth('http://localhost:8000/api/finances/wallets/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Carteira Principal', balance: baseBalance })
        })
        if (createWalletRes.ok) {
          const newWallet = await createWalletRes.json()
          defaultWalletId.value = newWallet.id
        }
      }
    }

    userData.balance = baseBalance

    const expensesRes = await fetchWithAuth('http://localhost:8000/api/finances/expenses/')

    if (expensesRes.ok) {
      const expenses = await expensesRes.json()
      
      let totalInc = 0
      let totalExp = 0

      recentTransactions.value = expenses.map(item => {
        const val = parseFloat(item.amount || item.value || 0)
        if (val >= 0) totalInc += val
        else totalExp += Math.abs(val)

        const dateVal = item.date || item.created_at || ''
        const dateParts = dateVal.split('-')
        const formattedDate = dateParts.length === 3 ? `${dateParts[2].substring(0,2)}/${dateParts[1]}/${dateParts[0]}` : dateVal

        let desc = item.description || item.title || item.name || 'Sem descrição'
        if (desc.startsWith('[')) {
          const closingBracket = desc.indexOf(']')
          if (closingBracket !== -1) {
            desc = desc.substring(closingBracket + 1).trim()
          }
        }

        return {
          id: item.id,
          description: desc,
          amount: val,
          type: val >= 0 ? 'income' : 'expense',
          date: formattedDate
        }
      }).reverse()

      userData.income = totalInc
      userData.expenses = totalExp

      nextTick(() => {
        if (userData.income > 0 || userData.expenses > 0) {
          initChart()
        }
      })
    }

    const catRes = await fetchWithAuth('http://localhost:8000/api/finances/categories/')
    if (catRes.ok) {
      userCategories.value = await catRes.json()
    }

    try {
      const invRes = await fetchWithAuth('http://localhost:8000/api/finances/investments/')
      if (invRes.ok) {
        const invData = await invRes.json()
        let tradTotal = 0
        invData.forEach(inv => {
          tradTotal += parseFloat(inv.current_value)
        })
        
        let cryptoTotal = 0
        const savedCrypto = localStorage.getItem('crypto_wallet')
        if (savedCrypto) {
          const parsedCrypto = JSON.parse(savedCrypto)
          const cryptoIds = Object.keys(parsedCrypto)
          if (cryptoIds.length > 0) {
            const cgRes = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${cryptoIds.join(',')}&vs_currencies=brl`)
            if (cgRes.ok) {
              const cgData = await cgRes.json()
              cryptoIds.forEach(id => {
                if (cgData[id]) {
                  const amt = typeof parsedCrypto[id] === 'number' ? parsedCrypto[id] : parsedCrypto[id].amount
                  cryptoTotal += (amt * cgData[id].brl)
                }
              })
            }
          }
        }
        totalInvestments.value = tradTotal + cryptoTotal
      }
    } catch (e) {}

    try {
      const goalsRes = await fetchWithAuth('http://localhost:8000/api/finances/goals/')
      if (goalsRes.ok) {
        const goalsData = await goalsRes.json()
        totalGoals.value = goalsData.reduce((acc, g) => acc + parseFloat(g.saved_amount), 0)
      }
    } catch (e) {}

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
    loadCards()
    loadData()
    window.addEventListener('resize', handleResize)
    window.addEventListener('theme-changed', handleThemeChange)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('theme-changed', handleThemeChange)
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null
  }
})

const currentCategories = computed(() => {
  return userCategories.value
    .filter(c => c.type === modalType.value)
    .map(c => c.name)
})

let debounceTimer = null

watch(() => form.description, (newVal) => {
  clearTimeout(debounceTimer)
  if (newVal && newVal.length >= 3 && showModal.value) {
    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetchWithAuth(`http://localhost:8000/api/finances/suggest-category/?description=${encodeURIComponent(newVal)}`)
        if (res.ok) {
          const data = await res.json()
          if (data.category) {
            const matchedCategory = currentCategories.value.find(c => c.toLowerCase() === data.category.toLowerCase())
            
            if (matchedCategory && form.category !== matchedCategory) {
              form.category = matchedCategory
              showToast('✨ Categoria preenchida automaticamente', 'success')
            }
          }
        }
      } catch (e) {
      }
    }, 600)
  }
})

const openModal = (type) => {
  modalType.value = type
  form.description = ''
  form.amount = ''
  form.category = ''
  form.date = new Date().toISOString().split('T')[0]
  form.paymentMethod = 'account'
  form.cardId = ''
  form.isInstallment = false
  form.installmentsCount = 2
  form.isMonthly = false
  form.monthsCount = 12
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const saveTransaction = async () => {
  if (!form.description || !form.amount || !form.date || !form.category) {
    showToast('Preencha todos os campos obrigatórios', 'error')
    return
  }

  let finalAmount = parseFloat(form.amount)

  if (modalType.value === 'expense' && form.paymentMethod === 'card') {
    if (!form.cardId) {
      showToast('Selecione um cartão.', 'error')
      return
    }

    const cardIndex = cards.value.findIndex(c => c.id === form.cardId)
    if (cardIndex === -1) {
      showToast('Cartão não encontrado.', 'error')
      return
    }

    const card = cards.value[cardIndex]

    if (card.used + finalAmount > card.limit) {
      showToast('Limite insuficiente no cartão.', 'error')
      return
    }

    card.used += finalAmount

    if (form.isInstallment && form.installmentsCount > 1) {
      const valPerInstallment = Number((finalAmount / form.installmentsCount).toFixed(2))
      const baseDate = new Date(form.date + 'T12:00:00')
      
      for (let i = 1; i <= form.installmentsCount; i++) {
        const installmentDate = new Date(baseDate)
        installmentDate.setMonth(installmentDate.getMonth() + (i - 1))
        
        card.expenses.push({
          id: Date.now() + i,
          description: `${form.description} (${i}/${form.installmentsCount})`,
          amount: valPerInstallment,
          date: installmentDate.toISOString().split('T')[0],
          category: form.category
        })
      }
    } else {
      card.expenses.push({
        id: Date.now(),
        description: form.description,
        amount: finalAmount,
        date: form.date,
        category: form.category
      })
    }

    localStorage.setItem('finances_cards', JSON.stringify(cards.value))
    showToast('Compra lançada no cartão com sucesso!', 'success')
    closeModal()
    return
  }

  if (!defaultWalletId.value) {
    showToast('Carteira principal não encontrada. Recarregue a página.', 'error')
    return
  }
  
  if (modalType.value === 'expense') {
    finalAmount = -Math.abs(finalAmount)
  } else {
    finalAmount = Math.abs(finalAmount)
  }

  try {
    if (form.isMonthly && form.monthsCount > 1) {
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

      const response = await fetchWithAuth('http://localhost:8000/api/finances/expenses/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        showToast('Transação registrada com sucesso!', 'success')
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

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  
  <SideLayout v-if="isAuthorized">
    <div class="dashboard-header">
      <div class="header-greeting">
        <h1>Dashboard Financeiro</h1>
        <p>Acompanhe e gerencie seu patrimônio</p>
      </div>
    </div>

    <div class="dashboard-grid">
      
      <div class="dashboard-col-left">
        <div class="main-balance-container">
          <div class="balance-card-primary">
            <div class="balance-info">
              <h3>Saldo Atual</h3>
              <p class="amount-huge">{{ formatCurrency(displayedBalance) }}</p>

              <div class="net-worth-row">
                <div class="net-item">
                  <span class="net-label">Investimentos</span>
                  <span class="net-val">{{ formatCurrency(totalInvestments) }}</span>
                </div>
                <div class="net-item">
                  <span class="net-label">Metas</span>
                  <span class="net-val">{{ formatCurrency(totalGoals) }}</span>
                </div>
                <div class="net-item total-item">
                  <span class="net-label">Patrimônio Total</span>
                  <span class="net-val highlight">{{ formatCurrency(displayedBalance + totalInvestments + totalGoals) }}</span>
                </div>
              </div>
            </div>
            <div class="balance-decoration">
              <div class="circle circle-1"></div>
              <div class="circle circle-2"></div>
            </div>
          </div>
        </div>

        <section class="charts-section">
          <div class="chart-card">
            <h3>Distribuição do Mês</h3>
            <div v-if="userData.income === 0 && userData.expenses === 0" class="empty-chart">
              <p>Nenhuma transação registada para gerar o gráfico.</p>
            </div>
            <div v-if="userData.income > 0 || userData.expenses > 0" ref="chartRef" class="echarts-container"></div>
          </div>
        </section>
      </div>

      <div class="dashboard-col-right">
        <section class="summary-cards">
          <div class="card income-card">
            <div class="card-icon-wrapper positive-bg">
              <span class="card-icon">↗</span>
            </div>
            <div class="card-data">
              <h3>Entradas do Mês</h3>
              <p class="amount positive">{{ formatCurrency(userData.income) }}</p>
            </div>
          </div>
          <div class="card expense-card">
            <div class="card-icon-wrapper negative-bg">
              <span class="card-icon">↘</span>
            </div>
            <div class="card-data">
              <h3>Saídas do Mês</h3>
              <p class="amount negative">{{ formatCurrency(userData.expenses) }}</p>
            </div>
          </div>
        </section>

        <section class="action-panel">
          <button @click="openModal('income')" class="action-btn btn-income">
            <span class="btn-icon">+</span> Nova Entrada
          </button>
          <button @click="openModal('expense')" class="action-btn btn-expense">
            <span class="btn-icon">-</span> Novo Gasto
          </button>
        </section>
      </div>

    </div> 
    
    <section class="recent-transactions">
      <div class="section-title-wrapper">
        <h2>Transações Recentes</h2>
      </div>
      
      <div class="table-container desktop-only">
        <table class="transaction-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Descrição</th>
              <th>Tipo</th>
              <th class="align-right">Valor</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="recentTransactionsLimited.length === 0">
              <td colspan="4" class="empty-state">Nenhuma transação registrada.</td>
            </tr>
            <tr v-for="item in recentTransactionsLimited" :key="item.id">
              <td class="td-date">{{ item.date }}</td>
              <td class="fw-600 td-desc">{{ item.description }}</td>
              <td>
                <span :class="['type-badge', item.type]">
                  {{ item.type === 'income' ? 'Entrada' : 'Saída' }}
                </span>
              </td>
              <td :class="['align-right fw-700', item.type === 'income' ? 'text-positive' : 'text-negative']">
                {{ item.type === 'income' ? '+' : '-' }} {{ formatCurrency(Math.abs(item.amount)) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="mobile-transactions-list mobile-only">
        <div v-if="recentTransactionsLimited.length === 0" class="empty-state">Nenhuma transação registrada.</div>
        <div v-for="item in recentTransactionsLimited" :key="item.id" class="mobile-transaction-item">
          <div class="m-t-info">
            <span class="m-t-desc">{{ item.description }}</span>
            <span class="m-t-date">{{ item.date }} • {{ item.type === 'income' ? 'Entrada' : 'Saída' }}</span>
          </div>
          <div :class="['m-t-amount', item.type === 'income' ? 'text-positive' : 'text-negative']">
            {{ item.type === 'income' ? '+' : '-' }} {{ formatCurrency(Math.abs(item.amount)) }}
          </div>
        </div>
      </div>
    </section>

    <FooterComp />

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <div class="modal-header">
          <h2>{{ modalType === 'income' ? 'Nova Entrada' : 'Novo Gasto' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        
        <form @submit.prevent="saveTransaction" class="modal-form">
          <div class="form-group full-width" v-if="modalType === 'expense'">
            <label>Forma de Pagamento</label>
            <select v-model="form.paymentMethod">
              <option value="account">Saldo da Conta (Débito)</option>
              <option value="card">Cartão de Crédito</option>
            </select>
          </div>

          <div class="form-group full-width" v-if="modalType === 'expense' && form.paymentMethod === 'card'">
            <label>Qual Cartão?</label>
            <select v-model="form.cardId" required>
              <option value="" disabled>Selecione o cartão</option>
              <option v-for="c in cards" :key="c.id" :value="c.id">
                {{ c.name }} (Livre: {{ formatCurrency(c.limit - c.used) }})
              </option>
            </select>
            <span v-if="cards.length === 0" class="error-text">Nenhum cartão cadastrado. Cadastre na aba Cartões.</span>
          </div>

          <div class="form-group full-width">
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

          <div class="form-row align-center" v-if="modalType === 'expense' && form.paymentMethod === 'card'">
            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="form.isInstallment" />
                Compra parcelada?
              </label>
            </div>
            <div class="form-group" v-if="form.isInstallment">
              <label>Qtd. Parcelas</label>
              <input v-model="form.installmentsCount" type="number" min="2" max="48" required />
            </div>
          </div>

          <div class="form-row align-center" v-if="modalType === 'income' || (modalType === 'expense' && form.paymentMethod === 'account')">
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

          <div class="form-group full-width">
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
  </SideLayout>
</template>

<style scoped>
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.header-greeting h1 {
  color: var(--text-primary);
  font-size: 2rem;
  font-weight: 800;
  margin: 0 0 4px 0;
  letter-spacing: -0.5px;
  transition: color 0.3s;
}

.header-greeting p {
  color: var(--text-secondary);
  margin: 0;
  font-size: 1.05rem;
  transition: color 0.3s;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 25px;
  margin-bottom: 35px;
}

.dashboard-col-left, .dashboard-col-right {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.main-balance-container {
  width: 100%;
}

.balance-card-primary {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: white;
  padding: 45px 40px;
  border-radius: 24px;
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.balance-info {
  position: relative;
  z-index: 2;
  width: 100%;
}

.balance-card-primary h3 {
  color: #cbd5e1;
  font-size: 1.1rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 12px 0;
}

.amount-huge {
  font-size: 3.5rem;
  font-weight: 900;
  margin: 0;
  color: #f7b500;
  letter-spacing: -1.5px;
  text-shadow: 0 2px 10px rgba(247, 181, 0, 0.2);
}

.net-worth-row {
  display: flex;
  gap: 25px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  flex-wrap: wrap;
}

.net-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.net-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #94a3b8;
  font-weight: 700;
}

.net-val {
  font-size: 1.05rem;
  font-weight: 700;
  color: #f8fafc;
}

.total-item {
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  padding-left: 20px;
}

.net-val.highlight {
  color: #10b981;
}

.balance-decoration {
  position: absolute;
  right: 0;
  top: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  right: -50px;
}

.circle-2 {
  width: 200px;
  height: 200px;
  bottom: -80px;
  right: 150px;
}

.charts-section {
  width: 100%;
  height: 100%;
}

.chart-card {
  background: var(--bg-card);
  border-radius: 24px;
  padding: 25px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: background-color 0.3s, border-color 0.3s;
}

.chart-card h3 {
  color: var(--text-primary);
  font-size: 1.2rem;
  font-weight: 800;
  margin: 0 0 15px 0;
  transition: color 0.3s;
}

.echarts-container {
  width: 100%;
  height: 320px;
  display: block;
}

.empty-chart {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-secondary);
  font-weight: 500;
  min-height: 320px;
}

.summary-cards {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.card {
  background: var(--bg-card);
  padding: 25px 30px;
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
  width: 60px;
  height: 60px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.positive-bg {
  background-color: var(--positive-bg);
  color: #10b981;
}

.negative-bg {
  background-color: var(--negative-bg);
  color: #ef4444;
}

.card-icon {
  font-size: 1.8rem;
  font-weight: 900;
}

.card-data h3 {
  color: var(--text-secondary);
  font-size: 0.95rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 8px 0;
  transition: color 0.3s;
}

.amount {
  font-size: 1.8rem;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.5px;
}

.positive { color: #059669; }
.negative { color: #dc2626; }

.action-panel {
  display: flex;
  gap: 20px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 18px 25px;
  border-radius: 16px;
  font-weight: 700;
  font-size: 1.05rem;
  cursor: pointer;
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex: 1;
}

.btn-income {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
}

.btn-income:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 25px -5px rgba(16, 185, 129, 0.4);
}

.btn-expense {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3);
}

.btn-expense:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 25px -5px rgba(239, 68, 68, 0.4);
}

.btn-icon {
  font-size: 1.4rem;
  font-weight: 900;
}

.section-title-wrapper {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--border-color);
  transition: border-color 0.3s;
}

.recent-transactions h2 {
  color: var(--text-primary);
  font-size: 1.4rem;
  font-weight: 800;
  margin: 0;
  transition: color 0.3s;
}

.table-container {
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
  min-width: 700px;
}

.transaction-table th, .transaction-table td {
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
.fw-600 { font-weight: 600; }
.fw-700 { font-weight: 700; }
.text-positive { color: #059669 !important; }
.text-negative { color: #dc2626 !important; }

.type-badge {
  padding: 8px 14px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.type-badge.income {
  background-color: var(--positive-bg);
  color: #059669;
}

.type-badge.expense {
  background-color: var(--negative-bg);
  color: #dc2626;
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
  min-width: 0;
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

.form-group input, .form-group select {
  width: 100%;
  box-sizing: border-box;
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

.form-group input:focus, .form-group select:focus {
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

.error-text {
  color: #ef4444;
  font-size: 0.85rem;
  font-weight: 600;
  margin-top: 5px;
}

.modal-actions {
  display: flex;
  gap: 15px;
  margin-top: 25px;
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

.mobile-only {
  display: none;
}

@media (max-width: 1024px) {
  .dashboard-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .dashboard-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .balance-card-primary { padding: 30px 25px; }
  .amount-huge { font-size: 2.8rem; }
  
  .net-worth-row { flex-direction: column; gap: 12px; }
  .total-item { border-left: none; padding-left: 0; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 12px; }
  
  .summary-cards { flex-direction: row; gap: 15px; }
  .summary-cards .card { padding: 15px; flex-direction: column; text-align: center; gap: 10px; }
  .summary-cards .card-icon-wrapper { width: 40px; height: 40px; font-size: 1.2rem; }
  .summary-cards .amount { font-size: 1.3rem; }
  
  .action-panel { flex-direction: row; gap: 10px; }
  .action-btn { padding: 12px; font-size: 0.95rem; }
  
  .form-row { flex-direction: column; gap: 15px; }
  
  .desktop-only { display: none; }
  .mobile-only { display: block; }
  
  .mobile-transactions-list {
    background: var(--bg-card);
    border-radius: 16px;
    border: 1px solid var(--border-color);
    padding: 5px 0;
  }
  
  .mobile-transaction-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    border-bottom: 1px solid var(--border-color);
  }
  
  .mobile-transaction-item:last-child {
    border-bottom: none;
  }
  
  .m-t-info { display: flex; flex-direction: column; gap: 4px; }
  .m-t-desc { font-weight: 700; color: var(--text-primary); font-size: 0.95rem; }
  .m-t-date { font-size: 0.75rem; color: var(--text-secondary); }
  .m-t-amount { font-weight: 800; font-size: 1rem; }
  
  .modal-container { padding: 25px 20px; max-height: 85vh; overflow-y: auto; }
}
</style>