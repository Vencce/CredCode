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

const cards = ref([])
const showModal = ref(false)
const showExpenseModal = ref(false)
const showInvoiceModal = ref(false)
const selectedCardId = ref(null)
const activeCardId = ref(null)

const form = reactive({
  id: null,
  name: '',
  flag: 'Mastercard',
  limit: '',
  closingDay: '',
  dueDay: ''
})

const expenseForm = reactive({
  description: '',
  amount: '',
  date: new Date().toISOString().split('T')[0],
  isInstallment: false,
  installmentsCount: 2
})

const activeCard = computed(() => cards.value.find(c => c.id === activeCardId.value) || null)

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
        const refreshResponse = await fetch('https://credcode-backend.onrender.com/api/auth/refresh/', {
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
    const profileRes = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/profile/')
    
    if (profileRes.ok) {
      const data = await profileRes.json()
      if (data.account_balance !== undefined && data.account_balance !== null) {
        baseBalance = parseFloat(data.account_balance) || 0
      }
    }

    const walletRes = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/wallets/')
    
    if (walletRes.ok) {
      const wallets = await walletRes.json()
      if (wallets.length > 0) {
        defaultWalletId.value = wallets[0].id
        if (baseBalance === 0 && wallets[0].balance !== undefined && wallets[0].balance !== null) {
          baseBalance = parseFloat(wallets[0].balance) || 0
        }
      }
    }

    const expensesRes = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/expenses/')

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

const loadCards = () => {
  const saved = localStorage.getItem('finances_cards')
  if (saved) {
    cards.value = JSON.parse(saved)
  }
}

const saveCards = () => {
  localStorage.setItem('finances_cards', JSON.stringify(cards.value))
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
    loadCards()
    await loadBalance()
  }
})

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}

const getFlagIcon = (flag) => {
  if (flag === 'Mastercard') return '🔴🟡'
  if (flag === 'Visa') return '🔵🔴'
  if (flag === 'Elo') return '⚪🔵'
  return '💳'
}

const openModal = () => {
  form.id = Date.now().toString()
  form.name = ''
  form.limit = ''
  form.closingDay = ''
  form.dueDay = ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const saveCard = () => {
  if (!form.name || !form.limit || !form.closingDay || !form.dueDay) {
    showToast('Preencha os campos obrigatórios.', 'error')
    return
  }

  const newCard = {
    id: form.id,
    name: form.name,
    flag: form.flag,
    limit: parseFloat(form.limit),
    used: 0,
    closingDay: parseInt(form.closingDay),
    dueDay: parseInt(form.dueDay),
    expenses: []
  }

  cards.value.push(newCard)
  saveCards()
  closeModal()
  showToast('Cartão cadastrado!', 'success')
}

const openExpenseModal = (id) => {
  selectedCardId.value = id
  expenseForm.description = ''
  expenseForm.amount = ''
  expenseForm.date = new Date().toISOString().split('T')[0]
  expenseForm.isInstallment = false
  expenseForm.installmentsCount = 2
  showExpenseModal.value = true
}

const closeExpenseModal = () => {
  showExpenseModal.value = false
  selectedCardId.value = null
}

const getInvoiceForDate = (dateStr, closingDay) => {
  const [year, month, day] = dateStr.split('-')
  const d = parseInt(day)
  let m = parseInt(month) - 1
  let y = parseInt(year)
  
  if (d > closingDay) {
    m += 1
    if (m > 11) {
      m = 0
      y += 1
    }
  }
  return { month: m, year: y }
}

const getCurrentMonthExpensesForCard = (card) => {
  if (!card) return []
  const todayStr = new Date().toISOString().split('T')[0]
  const currentInvoice = getInvoiceForDate(todayStr, card.closingDay)
  
  return card.expenses.filter(exp => {
    const expInvoice = getInvoiceForDate(exp.date, card.closingDay)
    return expInvoice.month === currentInvoice.month && expInvoice.year === currentInvoice.year
  }).sort((a, b) => new Date(a.date) - new Date(b.date))
}

const getCurrentInvoiceTotal = (card) => {
  return getCurrentMonthExpensesForCard(card).reduce((sum, exp) => sum + exp.amount, 0)
}

const currentMonthExpenses = computed(() => getCurrentMonthExpensesForCard(activeCard.value))
const currentInvoiceTotal = computed(() => getCurrentInvoiceTotal(activeCard.value))

const groupedInvoices = computed(() => {
  if (!activeCard.value) return []
  const groups = {}

  activeCard.value.expenses.forEach(exp => {
    const invoice = getInvoiceForDate(exp.date, activeCard.value.closingDay)
    const key = `${invoice.year}-${String(invoice.month + 1).padStart(2, '0')}`

    if (!groups[key]) {
      const months = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
      groups[key] = {
        key,
        label: `${months[invoice.month]} de ${invoice.year}`,
        total: 0,
        items: []
      }
    }
    groups[key].items.push(exp)
    groups[key].total += exp.amount
  })

  return Object.values(groups).sort((a, b) => a.key.localeCompare(b.key)).map(group => {
    group.items.sort((a, b) => new Date(a.date) - new Date(b.date))
    return group
  })
})

const addCardExpense = () => {
  const amount = parseFloat(expenseForm.amount)
  if (!expenseForm.description || !amount || amount <= 0) {
    showToast('Preencha os dados da compra.', 'error')
    return
  }

  const cardIndex = cards.value.findIndex(c => c.id === selectedCardId.value)
  if (cardIndex !== -1) {
    const card = cards.value[cardIndex]
    
    if (card.used + amount > card.limit) {
      showToast('Limite insuficiente!', 'error')
      return
    }

    card.used += amount

    if (expenseForm.isInstallment && expenseForm.installmentsCount > 1) {
      const valPerInstallment = Number((amount / expenseForm.installmentsCount).toFixed(2))
      const baseDate = new Date(expenseForm.date + 'T12:00:00')
      
      for (let i = 1; i <= expenseForm.installmentsCount; i++) {
        const installmentDate = new Date(baseDate)
        installmentDate.setMonth(installmentDate.getMonth() + (i - 1))
        
        card.expenses.push({
          id: Date.now() + i,
          description: `${expenseForm.description} (${i}/${expenseForm.installmentsCount})`,
          amount: valPerInstallment,
          date: installmentDate.toISOString().split('T')[0]
        })
      }
    } else {
      card.expenses.push({
        id: Date.now(),
        description: expenseForm.description,
        amount: amount,
        date: expenseForm.date
      })
    }

    saveCards()
    closeExpenseModal()
    showToast('Compra registrada na fatura!', 'success')
  }
}

const openInvoiceModal = (id) => {
  activeCardId.value = id
  showInvoiceModal.value = true
}

const closeInvoiceModal = () => {
  showInvoiceModal.value = false
  activeCardId.value = null
}

const paySpecificExpense = async (expense) => {
  if (!defaultWalletId.value) {
    showToast('Carteira principal não encontrada.', 'error')
    return
  }

  if (expense.amount > userData.balance) {
    showToast('Saldo insuficiente em conta.', 'error')
    return
  }

  const payload = {
    wallet: defaultWalletId.value,
    description: `[Cartões] Antecipação: ${expense.description}`,
    amount: Number((-Math.abs(expense.amount)).toFixed(2)),
    date: new Date().toISOString().split('T')[0],
    category: 'Contas'
  }

  try {
    const res = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/expenses/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      showToast('Erro ao processar pagamento.', 'error')
      return
    }

    userData.balance -= expense.amount

    const cardIndex = cards.value.findIndex(c => c.id === activeCardId.value)
    if (cardIndex !== -1) {
      const card = cards.value[cardIndex]
      card.used = Math.max(0, card.used - expense.amount)
      card.expenses = card.expenses.filter(e => e.id !== expense.id)
      saveCards()
    }

    await loadBalance()
    showToast('Parcela antecipada com sucesso!', 'success')
  } catch (e) {
    showToast('Erro de conexão.', 'error')
  }
}

const payInvoice = async (id) => {
  const cardIndex = cards.value.findIndex(c => c.id === id)
  if (cardIndex !== -1) {
    const card = cards.value[cardIndex]

    if (currentInvoiceTotal.value > 0) {
      if (!defaultWalletId.value) {
        showToast('Carteira principal não encontrada.', 'error')
        return
      }

      if (currentInvoiceTotal.value > userData.balance) {
        showToast('Saldo insuficiente em conta para pagar a fatura do mês.', 'error')
        return
      }

      const payload = {
        wallet: defaultWalletId.value,
        description: `[Cartões] Fatura ${card.name} do Mês`,
        amount: Number((-Math.abs(currentInvoiceTotal.value)).toFixed(2)),
        date: new Date().toISOString().split('T')[0],
        category: 'Contas'
      }

      try {
        const res = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/expenses/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })

        if (!res.ok) {
          showToast('Erro ao processar pagamento.', 'error')
          return
        }
        
        userData.balance -= currentInvoiceTotal.value
      } catch (e) {
        showToast('Erro de conexão.', 'error')
        return
      }

      card.used = Math.max(0, card.used - currentInvoiceTotal.value)
      
      const expenseIdsToRemove = currentMonthExpenses.value.map(e => e.id)
      card.expenses = card.expenses.filter(e => !expenseIdsToRemove.includes(e.id))
      
      saveCards()
      await loadBalance()
      showToast('Fatura do mês paga com sucesso!', 'success')
      
      if (showInvoiceModal.value && activeCardId.value === id) {
        closeInvoiceModal()
      }
    } else {
      showToast('Fatura atual já está zerada.', 'success')
    }
  }
}

const deleteCard = (id) => {
  cards.value = cards.value.filter(c => c.id !== id)
  saveCards()
  showToast('Cartão removido.', 'success')
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />

  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Meus Cartões</h1>
        <p>Gestão de faturas e limites de crédito</p>
      </div>
      <div class="header-actions">
        <button @click="openModal" class="action-btn btn-primary">
          <span class="btn-icon">+</span> Adicionar Cartão
        </button>
      </div>
    </div>

    <div v-if="cards.length === 0" class="empty-state-container">
      <div class="empty-icon">💳</div>
      <h3>Nenhum cartão cadastrado</h3>
      <p>Adicione seus cartões de crédito para controlar suas faturas e limites.</p>
    </div>

    <div v-else class="cards-grid">
      <div v-for="card in cards" :key="card.id" class="credit-card-wrapper">
        <div class="credit-card-visual" :class="card.flag.toLowerCase()">
          <div class="card-top">
            <span class="chip">🖲️</span>
            <span class="flag-icon">{{ getFlagIcon(card.flag) }}</span>
          </div>
          <div class="card-middle">
            <span class="card-name">{{ card.name }}</span>
          </div>
          <div class="card-bottom">
            <div class="card-info-item">
              <span class="label">Vencimento</span>
              <span class="value">Dia {{ card.dueDay }}</span>
            </div>
            <div class="card-info-item">
              <span class="label">Fechamento</span>
              <span class="value">Dia {{ card.closingDay }}</span>
            </div>
          </div>
        </div>

        <div class="card-details-panel">
          
          <div class="invoice-header">
            <span class="invoice-title">Fatura Atual</span>
            <span class="invoice-amount">{{ formatCurrency(getCurrentInvoiceTotal(card)) }}</span>
          </div>

          <div class="limit-section">
            <div class="limit-footer">
              <span class="limit-available">Disponível: <strong>{{ formatCurrency(card.limit - card.used) }}</strong></span>
            </div>
            <div class="limit-bar-bg">
              <div class="limit-bar-fill" :style="{ width: (card.used / card.limit * 100) + '%' }"></div>
            </div>
          </div>

          <div class="card-actions">
            <button @click="openExpenseModal(card.id)" class="btn-action-small btn-card-action">Lançar Compra</button>
            <button @click="openInvoiceModal(card.id)" class="btn-action-small btn-card-action">Ver Faturas</button>
            <button @click="deleteCard(card.id)" class="btn-icon-only"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
          </div>
        </div>
      </div>
    </div>

    <FooterComp />

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <div class="modal-header">
          <h2>Novo Cartão</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <form @submit.prevent="saveCard" class="modal-form">
          <div class="form-row">
            <div class="form-group">
              <label>Nome do Cartão</label>
              <input v-model="form.name" type="text" placeholder="Ex: Nubank, Itaú..." required />
            </div>
            <div class="form-group">
              <label>Bandeira</label>
              <select v-model="form.flag" required>
                <option value="Mastercard">Mastercard</option>
                <option value="Visa">Visa</option>
                <option value="Elo">Elo</option>
                <option value="Outros">Outros</option>
              </select>
            </div>
          </div>
          <div class="form-group full-width">
            <label>Limite Total (R$)</label>
            <input v-model="form.limit" type="number" step="0.01" min="1" placeholder="0.00" required />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Dia de Fechamento</label>
              <input v-model="form.closingDay" type="number" min="1" max="31" placeholder="Ex: 25" required />
            </div>
            <div class="form-group">
              <label>Dia de Vencimento</label>
              <input v-model="form.dueDay" type="number" min="1" max="31" placeholder="Ex: 5" required />
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeModal">Cancelar</button>
            <button type="submit" class="btn-save bg-primary">Cadastrar</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showExpenseModal" class="modal-overlay" @click.self="closeExpenseModal">
      <div class="modal-container small-modal">
        <div class="modal-header">
          <h2>Lançar na Fatura</h2>
          <button class="close-btn" @click="closeExpenseModal">&times;</button>
        </div>
        <form @submit.prevent="addCardExpense" class="modal-form">
          <div class="form-group full-width">
            <label>Estabelecimento / Descrição</label>
            <input v-model="expenseForm.description" type="text" placeholder="Ex: Mercado, Uber..." required />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Valor Total (R$)</label>
              <input v-model="expenseForm.amount" type="number" step="0.01" min="0.01" placeholder="0.00" required />
            </div>
            <div class="form-group">
              <label>Data</label>
              <input v-model="expenseForm.date" type="date" required />
            </div>
          </div>

          <div class="form-row align-center">
            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="expenseForm.isInstallment" />
                Compra parcelada?
              </label>
            </div>
            <div class="form-group" v-if="expenseForm.isInstallment">
              <label>Qtd. Parcelas</label>
              <input v-model="expenseForm.installmentsCount" type="number" min="2" max="48" required />
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeExpenseModal">Cancelar</button>
            <button type="submit" class="btn-save bg-negative">Lançar Gasto</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showInvoiceModal" class="modal-overlay" @click.self="closeInvoiceModal">
      <div class="modal-container large-modal">
        <div class="modal-header">
          <h2>Faturas: {{ activeCard?.name }}</h2>
          <button class="close-btn" @click="closeInvoiceModal">&times;</button>
        </div>

        <div class="invoice-summary">
          <div class="summary-col">
            <span class="summary-label">Fatura Atual (Mês Corrente)</span>
            <strong class="summary-total negative">{{ formatCurrency(currentInvoiceTotal) }}</strong>
          </div>
          <button @click="payInvoice(activeCard?.id)" class="btn-pay-full bg-positive" :disabled="currentInvoiceTotal === 0">
            Pagar Fatura Atual
          </button>
        </div>

        <div class="invoice-list-container">
          <h3 class="list-title">Todas as Faturas</h3>
          
          <div v-if="groupedInvoices.length === 0" class="empty-state">
            Nenhum lançamento pendente neste cartão.
          </div>
          
          <div v-else class="invoices-wrapper">
            <div v-for="group in groupedInvoices" :key="group.key" class="invoice-month-group">
              <div class="month-group-header">
                <h4 class="month-name">{{ group.label }}</h4>
                <span class="month-total">{{ formatCurrency(group.total) }}</span>
              </div>
              
              <div class="invoice-list-grouped">
                <div v-for="exp in group.items" :key="exp.id" class="invoice-item">
                  <div class="invoice-item-info">
                    <span class="invoice-item-date">{{ exp.date.split('-').reverse().join('/') }}</span>
                    <span class="invoice-item-desc">{{ exp.description }}</span>
                  </div>
                  <div class="invoice-item-action">
                    <strong class="invoice-item-amount">{{ formatCurrency(exp.amount) }}</strong>
                    <button @click="paySpecificExpense(exp)" class="btn-pay-small">Antecipar</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
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
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 30px; margin-bottom: 40px; }
.credit-card-wrapper { background: var(--bg-card); border-radius: 24px; padding: 25px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 25px; transition: transform 0.2s, box-shadow 0.2s; }
.credit-card-wrapper:hover { transform: translateY(-5px); box-shadow: var(--shadow-lg); }
.credit-card-visual { width: 100%; height: 180px; border-radius: 16px; padding: 20px; display: flex; flex-direction: column; justify-content: space-between; color: white; position: relative; overflow: hidden; box-shadow: 0 10px 20px rgba(0,0,0,0.15); }
.credit-card-visual::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent); transform: rotate(45deg); }
.mastercard { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); }
.visa { background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); }
.elo { background: linear-gradient(135deg, #111827 0%, #000000 100%); }
.outros { background: linear-gradient(135deg, #475569 0%, #334155 100%); }
.card-top { display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 1; }
.chip { font-size: 1.8rem; filter: grayscale(1) brightness(1.5); }
.flag-icon { font-size: 1.5rem; }
.card-middle { position: relative; z-index: 1; }
.card-name { font-size: 1.4rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.card-bottom { display: flex; gap: 20px; position: relative; z-index: 1; }
.card-info-item { display: flex; flex-direction: column; }
.card-info-item .label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.8; }
.card-info-item .value { font-size: 0.9rem; font-weight: 700; }
.card-details-panel { display: flex; flex-direction: column; gap: 20px; }

.invoice-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border-color); padding-bottom: 10px; transition: border-color 0.3s; }
.invoice-title { font-size: 0.9rem; color: var(--text-secondary); font-weight: 600; transition: color 0.3s; }
.invoice-amount { font-size: 1.5rem; font-weight: 900; color: #dc2626; }

.limit-section { display: flex; flex-direction: column; gap: 6px; }
.limit-footer { display: flex; justify-content: flex-end; font-size: 0.85rem; color: var(--text-secondary); transition: color 0.3s; }
.limit-footer strong { color: var(--text-primary); font-weight: 800; transition: color 0.3s; }
.limit-bar-bg { width: 100%; height: 6px; background: var(--border-color); border-radius: 3px; overflow: hidden; transition: background-color 0.3s; }
.limit-bar-fill { height: 100%; background: linear-gradient(90deg, #f87171 0%, #dc2626 100%); transition: width 0.5s ease; }

.card-actions { display: flex; gap: 10px; }
.btn-card-action { flex: 1; padding: 10px; background: var(--input-bg); color: var(--text-primary); border: 1px solid var(--border-input); border-radius: 10px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; text-align: center; }
.btn-card-action:hover { background: var(--border-color); }
.btn-icon-only { background: var(--negative-bg); color: #dc2626; border: none; width: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; }
.btn-icon-only:hover { opacity: 0.8; }
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-container { background: var(--bg-card); width: 100%; max-width: 480px; border-radius: 24px; box-shadow: var(--shadow-lg); border: 1px solid var(--border-color); padding: 35px; animation: modalSlideIn 0.3s ease-out; transition: background-color 0.3s, border-color 0.3s; }
.small-modal { max-width: 400px; }
.large-modal { max-width: 600px; }
@keyframes modalSlideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.modal-header h2 { margin: 0; color: var(--text-primary); font-size: 1.5rem; font-weight: 800; transition: color 0.3s; }
.close-btn { background: var(--bg-main); border: none; width: 36px; height: 36px; border-radius: 50%; font-size: 1.5rem; color: var(--text-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center; line-height: 1; transition: all 0.2s; }
.close-btn:hover { background: var(--border-color); color: var(--text-primary); }
.modal-form { display: flex; flex-direction: column; gap: 20px; }
.form-row { display: flex; gap: 20px; }
.align-center { align-items: flex-end; }
.form-group { display: flex; flex-direction: column; gap: 10px; flex: 1; min-width: 0; }
.full-width { width: 100%; }
.form-group label { font-size: 0.95rem; font-weight: 600; color: var(--text-secondary); transition: color 0.3s; }
.form-group input, .form-group select { width: 100%; box-sizing: border-box; padding: 16px; border: 1px solid var(--border-input); border-radius: 12px; font-size: 1rem; font-family: 'Inter', sans-serif; outline: none; background-color: var(--input-bg); color: var(--text-primary); transition: all 0.3s; }
.form-group input:focus, .form-group select:focus { border-color: #f7b500; background-color: var(--bg-card); box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1); }
.checkbox-group { flex-direction: row; align-items: center; margin-bottom: 5px; }
.checkbox-label { display: flex; align-items: center; gap: 8px; cursor: pointer; user-select: none; font-weight: 600; color: var(--text-primary) !important; font-size: 1rem !important; }
.checkbox-label input { width: 20px; height: 20px; cursor: pointer; margin: 0; }
.modal-actions { display: flex; gap: 15px; margin-top: 15px; }
.btn-cancel { flex: 1; padding: 16px; background-color: var(--bg-main); color: var(--text-secondary); border: 1px solid var(--border-color); border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: all 0.2s; }
.btn-cancel:hover { background: var(--border-color); color: var(--text-primary); }
.btn-save { flex: 1; padding: 16px; color: white; border: none; border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.2s; }
.btn-save:hover { transform: translateY(-2px); }
.bg-negative { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3); }
.invoice-summary { display: flex; justify-content: space-between; align-items: center; background: var(--bg-main); padding: 20px; border-radius: 16px; border: 1px solid var(--border-color); margin-bottom: 25px; transition: background-color 0.3s, border-color 0.3s; }
.summary-col { display: flex; flex-direction: column; gap: 5px; }
.summary-label { font-size: 0.9rem; color: var(--text-secondary); font-weight: 600; text-transform: uppercase; transition: color 0.3s; }
.summary-total { font-size: 1.6rem; font-weight: 800; color: #dc2626; }
.btn-pay-full { padding: 12px 20px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 12px; font-weight: 700; font-size: 0.95rem; cursor: pointer; transition: all 0.2s; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2); }
.btn-pay-full:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3); }
.btn-pay-full:disabled { opacity: 0.5; cursor: not-allowed; background: var(--border-color); box-shadow: none; color: var(--text-secondary); }

.invoice-list-container { display: flex; flex-direction: column; gap: 15px; }
.list-title { font-size: 1.1rem; color: var(--text-primary); font-weight: 700; margin: 0; transition: color 0.3s; }
.invoices-wrapper { display: flex; flex-direction: column; gap: 20px; max-height: 400px; overflow-y: auto; padding-right: 5px; }
.invoices-wrapper::-webkit-scrollbar { width: 6px; }
.invoices-wrapper::-webkit-scrollbar-thumb { background-color: var(--border-input); border-radius: 4px; }
.invoice-month-group { display: flex; flex-direction: column; gap: 10px; background: var(--bg-card); padding: 15px; border-radius: 12px; border: 1px solid var(--border-color); }
.month-group-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-input); padding-bottom: 10px; }
.month-name { font-size: 1.1rem; color: var(--text-primary); font-weight: 700; margin: 0; text-transform: capitalize; }
.month-total { font-weight: 800; color: #dc2626; font-size: 1.2rem; }
.invoice-list-grouped { display: flex; flex-direction: column; gap: 10px; }

.invoice-item { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: var(--input-bg); border: 1px solid var(--border-input); border-radius: 12px; transition: background-color 0.2s, border-color 0.3s; }
.invoice-item:hover { background: var(--bg-card); }
.invoice-item-info { display: flex; flex-direction: column; gap: 4px; }
.invoice-item-date { font-size: 0.8rem; color: var(--text-secondary); font-weight: 600; transition: color 0.3s; }
.invoice-item-desc { font-size: 1rem; color: var(--text-primary); font-weight: 600; transition: color 0.3s; }
.invoice-item-action { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
.invoice-item-amount { font-size: 1.1rem; color: #dc2626; font-weight: 800; }
.btn-pay-small { padding: 6px 12px; border: 1px solid #10b981; background: var(--positive-bg); color: #10b981; border-radius: 8px; font-weight: 700; font-size: 0.8rem; cursor: pointer; transition: all 0.2s; }
.btn-pay-small:hover { background: #10b981; color: white; }
.empty-state { text-align: center; padding: 30px; color: var(--text-secondary); font-weight: 500; background: var(--input-bg); border-radius: 12px; border: 1px dashed var(--border-input); transition: background-color 0.3s, border-color 0.3s, color 0.3s; }

@media (max-width: 768px) { .page-header { flex-direction: column; align-items: flex-start; gap: 15px; } .header-actions { width: 100%; } .action-btn { width: 100%; } .form-row { flex-direction: column; } .invoice-summary { flex-direction: column; gap: 15px; text-align: center; } .btn-pay-full { width: 100%; } }
</style>