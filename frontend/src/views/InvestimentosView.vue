<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue'

const router = useRouter()
const isAuthorized = ref(false)
const isLoading = ref(true)

const activeTab = ref('crypto')

const toast = reactive({
  show: false,
  message: '',
  type: 'error'
})

const userData = reactive({
  balance: 0
})

const defaultWalletId = ref(null)

const cryptoMarket = ref([])
const searchQuery = ref('')
const myCrypto = reactive({})

const showTradeModal = ref(false)
const tradeType = ref('buy')
const selectedCoin = ref(null)
const tradeAmountStr = ref('')

const traditionalInvestments = ref([])
const showTradModal = ref(false)
const showTradDeleteModal = ref(false)
const tradEditingId = ref(null)
const tradItemToDelete = ref(null)

const investmentTypes = ['Ações', 'Fundos Imobiliários (FIIs)', 'Renda Fixa', 'ETFs', 'BDRs', 'Outros']
const paymentFrequencies = ['1 mês', '3 meses', '6 meses', '12 meses', 'Nenhum']

const tradForm = reactive({
  name: '',
  type: '',
  amount_invested: '',
  current_value: '',
  purchase_date: new Date().toISOString().split('T')[0],
  quantity: '',
  payment_frequency: 'Nenhum',
  dividend_per_share: ''
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

const fetchMarketData = async () => {
  try {
    const response = await fetch('https://api.coingecko.com/api/v3/coins/markets?vs_currency=brl&order=market_cap_desc&per_page=100&page=1&sparkline=false')
    if (response.ok) {
      const data = await response.json()
      cryptoMarket.value = data.map(coin => ({
        id: coin.id,
        symbol: coin.symbol.toUpperCase(),
        name: coin.name,
        price: coin.current_price,
        change: coin.price_change_percentage_24h || 0,
        image: coin.image
      }))
    }
  } catch (error) {
    showToast('Erro ao atualizar cotações de mercado.', 'error')
  }
}

const loadBalanceAndTraditional = async () => {
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

    const tradRes = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/investments/')
    if (tradRes.ok) {
      const tradData = await tradRes.json()
      traditionalInvestments.value = tradData.map(inv => ({
        ...inv,
        amount_invested: parseFloat(inv.amount_invested),
        current_value: parseFloat(inv.current_value),
        quantity: parseFloat(inv.quantity || 1),
        dividend_per_share: parseFloat(inv.dividend_per_share || 0),
        payment_frequency: inv.payment_frequency || 'Nenhum'
      })).sort((a, b) => new Date(b.purchase_date) - new Date(a.purchase_date))
    }

  } catch (error) {
    showToast('Erro ao carregar dados financeiros.', 'error')
  }
}

const loadLocalCryptoWallet = () => {
  const saved = localStorage.getItem('crypto_wallet')
  if (saved) {
    const parsed = JSON.parse(saved)
    Object.keys(parsed).forEach(key => {
      const value = parsed[key]
      if (typeof value === 'number') {
        myCrypto[key] = { amount: value, investedBRL: 0 }
      } else {
        myCrypto[key] = {
          amount: Number(value.amount || 0),
          investedBRL: Number(value.investedBRL || 0)
        }
      }
    })
  }
}

const saveLocalCryptoWallet = () => {
  localStorage.setItem('crypto_wallet', JSON.stringify(myCrypto))
}

onMounted(async () => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    showToast('Acesso negado. Por favor, faça login no terminal.', 'error')
    setTimeout(() => { router.push('/') }, 1500)
  } else {
    isAuthorized.value = true
    loadLocalCryptoWallet()
    await fetchMarketData()
    await loadBalanceAndTraditional()
    isLoading.value = false
  }
})

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}

const formatCrypto = (value, symbol) => {
  return `${Number(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 6 })} ${symbol}`
}

const formatPercent = (value) => {
  return Number(value).toFixed(2) + '%'
}

const filteredMarket = computed(() => {
  if (!searchQuery.value) return cryptoMarket.value.slice(0, 12)
  const query = searchQuery.value.toLowerCase()
  return cryptoMarket.value.filter(c => c.name.toLowerCase().includes(query) || c.symbol.toLowerCase().includes(query))
})

const myCoinsList = computed(() => {
  return cryptoMarket.value.filter(c => myCrypto[c.id] && myCrypto[c.id].amount > 0)
})

const totalCryptoPortfolioBRL = computed(() => {
  let total = 0
  myCoinsList.value.forEach(coin => { total += (myCrypto[coin.id]?.amount || 0) * coin.price })
  return total
})

const calculatedTradeValue = computed(() => {
  if (!selectedCoin.value || !tradeAmountStr.value) return 0
  const amount = parseFloat(tradeAmountStr.value) || 0
  return tradeType.value === 'buy' ? amount / selectedCoin.value.price : amount * selectedCoin.value.price
})

const openTradeModal = (type, coin) => {
  tradeType.value = type
  selectedCoin.value = coin
  tradeAmountStr.value = ''
  showTradeModal.value = true
}

const closeTradeModal = () => {
  showTradeModal.value = false
  tradeAmountStr.value = ''
  selectedCoin.value = null
}

const setSellAll = () => {
  if (selectedCoin.value && myCrypto[selectedCoin.value.id]) {
    tradeAmountStr.value = myCrypto[selectedCoin.value.id].amount.toString()
  }
}

const executeTrade = async () => {
  if (!selectedCoin.value) return
  let amount = parseFloat(tradeAmountStr.value)
  if (!amount || amount <= 0) { showToast('Insira um valor válido.', 'error'); return }
  if (!defaultWalletId.value) { showToast('Carteira principal não encontrada.', 'error'); return }

  const coin = selectedCoin.value
  let brlImpact = 0
  let cryptoImpact = 0

  if (tradeType.value === 'buy') {
    if (amount > userData.balance) { showToast('Saldo insuficiente em BRL.', 'error'); return }
    brlImpact = -Math.abs(amount)
    cryptoImpact = amount / coin.price
  } else {
    const currentPosition = myCrypto[coin.id]
    if (!currentPosition || currentPosition.amount <= 0) { showToast(`Saldo insuficiente de ${coin.symbol}.`, 'error'); return }
    if (Math.abs(amount - currentPosition.amount) < 0.000001) amount = currentPosition.amount
    if (amount > currentPosition.amount) { showToast(`Saldo insuficiente de ${coin.symbol}.`, 'error'); return }
    brlImpact = Math.abs(amount * coin.price)
    cryptoImpact = -Math.abs(amount)
  }

  const description = tradeType.value === 'buy' ? `[Investimentos] Compra de ${coin.symbol}` : `[Investimentos] Venda de ${coin.symbol}`
  const payload = { wallet: defaultWalletId.value, description, amount: brlImpact, date: new Date().toISOString().split('T')[0], category: 'Investimentos' }

  try {
    const response = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/expenses/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (response.ok) {
      if (!myCrypto[coin.id]) myCrypto[coin.id] = { amount: 0, investedBRL: 0 }
      const position = myCrypto[coin.id]

      if (tradeType.value === 'buy') {
        position.amount += cryptoImpact
        position.investedBRL += amount
      } else {
        const avgCost = position.amount > 0 ? position.investedBRL / position.amount : 0
        const costRemoved = avgCost * amount
        position.amount -= amount
        position.investedBRL -= costRemoved
        if (position.amount < 0.000001) { position.amount = 0; position.investedBRL = 0 }
      }

      saveLocalCryptoWallet()
      await loadBalanceAndTraditional()
      showToast('Ordem executada com sucesso!', 'success')
      closeTradeModal()
    } else {
      showToast('Erro ao processar transação no banco.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão.', 'error')
  }
}

const portfolioPerformance = computed(() => {
  return myCoinsList.value.map(coin => {
    const position = myCrypto[coin.id] || { amount: 0, investedBRL: 0 }
    const amount = Number(position.amount || 0)
    const investedBRL = Number(position.investedBRL || 0)
    const currentValue = amount * coin.price
    const profitLoss = currentValue - investedBRL
    const avgPrice = amount > 0 ? investedBRL / amount : 0
    const profitLossPct = investedBRL > 0 ? (profitLoss / investedBRL) * 100 : 0

    return {
      id: coin.id, symbol: coin.symbol, name: coin.name, image: coin.image,
      amount, investedBRL, avgPrice, currentPrice: coin.price, currentValue, profitLoss, profitLossPct
    }
  })
})

const totalTradInvested = computed(() => traditionalInvestments.value.reduce((acc, curr) => acc + curr.amount_invested, 0))
const totalTradCurrent = computed(() => traditionalInvestments.value.reduce((acc, curr) => acc + curr.current_value, 0))
const totalTradProfit = computed(() => totalTradCurrent.value - totalTradInvested.value)
const tradProfitPct = computed(() => totalTradInvested.value === 0 ? 0 : (totalTradProfit.value / totalTradInvested.value) * 100)

const openTradModal = (item = null) => {
  if (item) {
    tradEditingId.value = item.id
    tradForm.name = item.name
    tradForm.type = item.type
    tradForm.amount_invested = item.amount_invested
    tradForm.current_value = item.current_value
    tradForm.purchase_date = item.purchase_date
    tradForm.quantity = item.quantity
    tradForm.payment_frequency = item.payment_frequency || 'Nenhum'
    tradForm.dividend_per_share = item.dividend_per_share
  } else {
    tradEditingId.value = null
    tradForm.name = ''
    tradForm.type = ''
    tradForm.amount_invested = ''
    tradForm.current_value = ''
    tradForm.purchase_date = new Date().toISOString().split('T')[0]
    tradForm.quantity = ''
    tradForm.payment_frequency = 'Nenhum'
    tradForm.dividend_per_share = ''
  }
  showTradModal.value = true
}

const closeTradModal = () => { showTradModal.value = false; tradEditingId.value = null }

const saveTradInvestment = async () => {
  if (!tradForm.name || !tradForm.type || !tradForm.amount_invested || !tradForm.current_value || !tradForm.purchase_date) {
    showToast('Preencha todos os campos obrigatórios.', 'error')
    return
  }

  const payload = {
    name: tradForm.name,
    type: tradForm.type,
    amount_invested: parseFloat(tradForm.amount_invested).toFixed(2),
    current_value: parseFloat(tradForm.current_value).toFixed(2),
    purchase_date: tradForm.purchase_date,
    quantity: parseFloat(tradForm.quantity || 1).toFixed(4),
    payment_frequency: tradForm.payment_frequency,
    dividend_per_share: parseFloat(tradForm.dividend_per_share || 0).toFixed(4)
  }

  try {
    const url = tradEditingId.value ? `https://credcode-backend.onrender.com/api/finances/investments/${tradEditingId.value}/` : 'https://credcode-backend.onrender.com/api/finances/investments/'
    const method = tradEditingId.value ? 'PUT' : 'POST'
    const response = await fetchWithAuth(url, { method: method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })

    if (response.ok) {
      showToast(tradEditingId.value ? 'Ativo atualizado!' : 'Ativo registado!', 'success')
      closeTradModal()
      loadBalanceAndTraditional()
    } else {
      showToast('Erro ao guardar ativo.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão.', 'error')
  }
}

const confirmTradDelete = (id) => { tradItemToDelete.value = id; showTradDeleteModal.value = true }
const closeTradDeleteModal = () => { showTradDeleteModal.value = false; tradItemToDelete.value = null }

const executeTradDelete = async () => {
  if (!tradItemToDelete.value) return
  try {
    const response = await fetchWithAuth(`https://credcode-backend.onrender.com/api/finances/investments/${tradItemToDelete.value}/`, { method: 'DELETE' })
    if (response.ok) {
      showToast('Ativo removido!', 'success')
      loadBalanceAndTraditional()
    } else {
      showToast('Erro ao remover ativo.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão.', 'error')
  } finally {
    closeTradDeleteModal()
  }
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  
  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Investimentos</h1>
        <p>Acompanhe e gira o seu portefólio completo</p>
      </div>
      <button v-if="activeTab === 'crypto'" @click="fetchMarketData" class="btn-refresh">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><polyline points="3 3 3 8 8 8"></polyline></svg>
        Sincronizar
      </button>
      <button v-if="activeTab === 'traditional'" @click="openTradModal()" class="action-btn btn-primary">
        <span class="btn-icon">+</span> Novo Ativo
      </button>
    </div>

    <div class="tabs-container">
      <button :class="['tab-btn', { active: activeTab === 'crypto' }]" @click="activeTab = 'crypto'">
        Criptomoedas (Broker)
      </button>
      <button :class="['tab-btn', { active: activeTab === 'traditional' }]" @click="activeTab = 'traditional'">
        Bolsa e Fundos (Manual)
      </button>
    </div>

    <div v-if="isLoading" class="loading-state">
      <div class="loader-spinner"></div>
      <p>A carregar dados...</p>
    </div>

    <div v-else>
      <div v-if="activeTab === 'crypto'">
        <div class="portfolio-overview">
          <div class="overview-card primary-card">
            <h3>Portefólio Cripto</h3>
            <p class="amount-huge">{{ formatCurrency(totalCryptoPortfolioBRL) }}</p>
            <p class="subtitle">Valor total estimado em conta</p>
          </div>
          <div class="overview-card secondary-card">
            <h3>Poder de Compra</h3>
            <p class="amount-medium">{{ formatCurrency(userData.balance) }}</p>
            <p class="subtitle">Saldo disponível em R$</p>
          </div>
        </div>

        <section class="performance-section" v-if="portfolioPerformance.length > 0">
          <div class="section-header"><h2>Margem de Lucro por Moeda</h2></div>
          <div class="performance-card">
            <div class="performance-table-head">
              <span>Moeda</span><span>Preço Médio</span><span>Preço Atual</span><span>Resultado</span><span>Variação</span>
            </div>
            <div v-for="item in portfolioPerformance" :key="item.id" class="performance-row">
              <div class="coin-cell">
                <img :src="item.image" :alt="item.name" class="mini-coin-logo" />
                <div><strong class="text-primary">{{ item.symbol }}</strong><p class="text-secondary-sub">{{ item.name }}</p></div>
              </div>
              <span class="text-primary">{{ formatCurrency(item.avgPrice) }}</span>
              <span class="text-primary">{{ formatCurrency(item.currentPrice) }}</span>
              <span :class="item.profitLoss >= 0 ? 'text-positive' : 'text-negative'">{{ formatCurrency(item.profitLoss) }}</span>
              <div class="performance-bar-wrap">
                <div class="performance-bar-bg"><div :class="['performance-bar-fill', item.profitLoss >= 0 ? 'profit-fill' : 'loss-fill']" :style="{ width: Math.min(Math.abs(item.profitLossPct), 100) + '%' }"></div></div>
                <span :class="item.profitLoss >= 0 ? 'text-positive' : 'text-negative'">{{ formatPercent(item.profitLossPct) }}</span>
              </div>
            </div>
          </div>
        </section>

        <div class="dashboard-grid">
          <section class="market-section">
            <div class="section-header">
              <div class="header-text-group"><h2>Mercado</h2><span class="live-badge">Ao Vivo</span></div>
              <div class="search-wrapper">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <input type="text" v-model="searchQuery" placeholder="Buscar criptomoeda..." class="market-search" />
              </div>
            </div>
            <div class="asset-grid">
              <div v-for="coin in filteredMarket" :key="coin.id" class="asset-card">
                <div class="asset-info">
                  <img :src="coin.image" :alt="coin.name" class="coin-logo" />
                  <div class="asset-title"><h3>{{ coin.symbol }}</h3><span class="asset-name">{{ coin.name }}</span></div>
                </div>
                <div class="asset-price-box">
                  <p class="asset-price">{{ formatCurrency(coin.price) }}</p>
                  <p :class="['asset-change', coin.change >= 0 ? 'text-positive' : 'text-negative']">{{ coin.change >= 0 ? '▲' : '▼' }} {{ formatPercent(coin.change) }}</p>
                </div>
                <button @click="openTradeModal('buy', coin)" class="btn-trade btn-buy">Comprar</button>
              </div>
            </div>
            <div v-if="filteredMarket.length === 0" class="empty-market"><p>Nenhuma criptomoeda encontrada.</p></div>
          </section>

          <section class="wallet-section">
            <div class="section-header"><h2>Sua Carteira</h2></div>
            <div class="my-coins-list">
              <div v-if="myCoinsList.length === 0" class="empty-wallet">Não possui criptomoedas.</div>
              <div v-for="coin in myCoinsList" :key="'my-'+coin.id" class="my-coin-card">
                <div class="my-coin-left">
                  <img :src="coin.image" class="my-coin-logo" />
                  <div class="my-coin-details"><span class="my-coin-symbol">{{ coin.symbol }}</span><span class="my-coin-amount">{{ formatCrypto(myCrypto[coin.id].amount, '') }}</span></div>
                </div>
                <div class="my-coin-value">
                  <span class="fiat-value">{{ formatCurrency(myCrypto[coin.id].amount * coin.price) }}</span>
                  <button @click="openTradeModal('sell', coin)" class="btn-trade-small btn-sell">Vender</button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>

      <div v-if="activeTab === 'traditional'">
        <div class="portfolio-overview" style="margin-bottom: 25px;">
          <div class="overview-card primary-card">
            <h3>Saldo Patrimonial</h3>
            <span class="amount-huge text-white">{{ formatCurrency(totalTradCurrent) }}</span>
            <p class="subtitle">Valor total atualizado</p>
          </div>
          <div class="overview-card secondary-card">
            <h3>Total Investido</h3>
            <span class="amount-medium">{{ formatCurrency(totalTradInvested) }}</span>
            <p class="subtitle">Aportes realizados</p>
          </div>
          <div class="overview-card secondary-card" style="border-color: transparent;" :style="{ background: totalTradProfit >= 0 ? 'var(--positive-bg)' : 'var(--negative-bg)' }">
            <h3 :class="totalTradProfit >= 0 ? 'text-positive' : 'text-negative'">Rentabilidade</h3>
            <span :class="['amount-medium', totalTradProfit >= 0 ? 'text-positive' : 'text-negative']">
              {{ totalTradProfit >= 0 ? '+' : '' }}{{ formatCurrency(totalTradProfit) }}
            </span>
            <p class="subtitle" :class="totalTradProfit >= 0 ? 'text-positive' : 'text-negative'">{{ formatPercent(tradProfitPct) }} de variação</p>
          </div>
        </div>

        <div v-if="traditionalInvestments.length === 0" class="empty-state-container">
          <div class="empty-icon">📈</div>
          <h3>Nenhum ativo registado</h3>
          <p>Comece a adicionar as suas ações, FIIs ou fundos para acompanhar a evolução.</p>
        </div>

        <div v-else class="investments-container">
          <table class="transaction-table">
            <thead>
              <tr>
                <th>Ativo</th>
                <th>Tipo</th>
                <th class="align-right">Posição</th>
                <th class="align-right">Investido / Atual</th>
                <th class="align-right">Rentabilidade</th>
                <th class="align-right">Dividendos Est.</th>
                <th class="align-center">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in traditionalInvestments" :key="item.id">
                <td>
                  <div class="asset-info">
                    <span class="fw-700 td-desc">{{ item.name }}</span>
                    <span class="td-date">{{ item.purchase_date.split('-').reverse().join('/') }}</span>
                  </div>
                </td>
                <td><span class="category-tag">{{ item.type }}</span></td>
                <td class="align-right">
                  <div class="fw-700 text-primary">{{ item.quantity }} cotas</div>
                  <div class="text-secondary" style="font-size: 0.8rem">PM: {{ formatCurrency(item.amount_invested / item.quantity) }}</div>
                </td>
                <td class="align-right">
                  <div class="fw-800 text-primary">{{ formatCurrency(item.current_value) }}</div>
                  <div class="text-secondary" style="font-size: 0.8rem">Investido: {{ formatCurrency(item.amount_invested) }}</div>
                </td>
                <td class="align-right">
                  <span :class="['profit-badge', (item.current_value - item.amount_invested) >= 0 ? 'badge-positive' : 'badge-negative']">
                    {{ (item.current_value - item.amount_invested) >= 0 ? '+' : '' }}{{ formatCurrency(item.current_value - item.amount_invested) }}
                    ({{ formatPercent(((item.current_value - item.amount_invested) / item.amount_invested) * 100) }})
                  </span>
                </td>
                <td class="align-right">
                  <span v-if="item.dividend_per_share > 0" class="profit-badge badge-positive" style="background: transparent; padding: 0;">
                    {{ formatCurrency(item.quantity * item.dividend_per_share) }}<br>
                    <span style="font-size: 0.75rem; color: var(--text-secondary); font-weight: 500;">/ {{ item.payment_frequency }}</span>
                  </span>
                  <span v-else class="text-secondary">-</span>
                </td>
                <td class="align-center actions-cell">
                  <button class="action-icon" title="Editar" @click="openTradModal(item)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                  </button>
                  <button class="action-icon icon-danger" title="Excluir" @click="confirmTradDelete(item.id)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <FooterComp />

    <div v-if="showTradeModal" class="modal-overlay" @click.self="closeTradeModal">
      <div class="modal-container">
        <div class="modal-header">
          <div class="modal-header-title">
            <img :src="selectedCoin?.image" class="modal-coin-logo" />
            <h2>{{ tradeType === 'buy' ? 'Comprar' : 'Vender' }} {{ selectedCoin?.symbol }}</h2>
          </div>
          <button class="close-btn" @click="closeTradeModal">&times;</button>
        </div>
        <form @submit.prevent="executeTrade" class="modal-form">
          <div class="trade-info-box">
            <div class="trade-price-row"><span>Cotação atual:</span><span class="fw-700 text-primary">{{ formatCurrency(selectedCoin?.price || 0) }}</span></div>
            <div class="trade-balance-row"><span>Disponível:</span><span class="fw-700 text-primary">{{ tradeType === 'buy' ? formatCurrency(userData.balance) : formatCrypto(myCrypto[selectedCoin?.id]?.amount || 0, selectedCoin?.symbol || '') }}</span></div>
          </div>
          <div class="form-group">
            <div class="label-with-action"><label>{{ tradeType === 'buy' ? 'Valor do investimento (R$)' : `Quantidade para venda` }}</label><button type="button" class="btn-sell-all" v-if="tradeType === 'sell'" @click="setSellAll">Vender Tudo</button></div>
            <input v-model="tradeAmountStr" type="number" step="any" min="0.000001" :placeholder="tradeType === 'buy' ? 'R$ 0,00' : '0.0000'" required />
          </div>
          <div class="conversion-result" v-if="tradeAmountStr && parseFloat(tradeAmountStr) > 0">
            <p>Irá receber:</p><h3>{{ tradeType === 'buy' ? formatCrypto(calculatedTradeValue, selectedCoin?.symbol || '') : formatCurrency(calculatedTradeValue) }}</h3>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeTradeModal">Cancelar</button>
            <button type="submit" :class="['btn-save', tradeType === 'buy' ? 'bg-positive' : 'bg-negative']">Confirmar {{ tradeType === 'buy' ? 'Compra' : 'Venda' }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showTradModal" class="modal-overlay" @click.self="closeTradModal">
      <div class="modal-container">
        <div class="modal-header">
          <h2>{{ tradEditingId ? 'Atualizar Ativo' : 'Novo Ativo' }}</h2>
          <button class="close-btn" @click="closeTradModal">&times;</button>
        </div>
        <form @submit.prevent="saveTradInvestment" class="modal-form">
          <div class="form-row">
            <div class="form-group" style="flex: 2;"><label>Ativo</label><input v-model="tradForm.name" type="text" placeholder="Ex: AAPL, HGLG11..." required /></div>
            <div class="form-group" style="flex: 1;"><label>Tipo</label><select v-model="tradForm.type" required><option value="" disabled>Selecione...</option><option v-for="t in investmentTypes" :key="t" :value="t">{{ t }}</option></select></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Investido (R$)</label><input v-model="tradForm.amount_invested" type="number" step="0.01" min="0" required /></div>
            <div class="form-group"><label>Atual (R$)</label><input v-model="tradForm.current_value" type="number" step="0.01" min="0" required /></div>
            <div class="form-group"><label>Quantidade</label><input v-model="tradForm.quantity" type="number" step="0.0001" min="0.0001" required /></div>
          </div>
          <div class="form-row" v-if="['Ações', 'Fundos Imobiliários (FIIs)', 'BDRs'].includes(tradForm.type)">
            <div class="form-group"><label>Frequência Dividendos</label><select v-model="tradForm.payment_frequency"><option v-for="f in paymentFrequencies" :key="f" :value="f">{{ f }}</option></select></div>
            <div class="form-group"><label>Valor por Cota (R$)</label><input v-model="tradForm.dividend_per_share" type="number" step="0.0001" min="0" /></div>
          </div>
          <div class="form-group full-width"><label>Data de Aplicação</label><input v-model="tradForm.purchase_date" type="date" required /></div>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeTradModal">Cancelar</button>
            <button type="submit" class="btn-save btn-primary">Salvar</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showTradDeleteModal" class="modal-overlay" @click.self="closeTradDeleteModal">
      <div class="modal-container small-modal">
        <div class="modal-header">
          <h2 class="text-negative">Excluir Ativo</h2>
          <button class="close-btn" @click="closeTradDeleteModal">&times;</button>
        </div>
        <div class="modal-body"><p>Tem certeza que deseja excluir? A ação não pode ser desfeita.</p></div>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="closeTradDeleteModal">Cancelar</button>
          <button type="button" class="btn-save bg-negative" @click="executeTradDelete">Excluir</button>
        </div>
      </div>
    </div>

  </SideLayout>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.header-titles h1 { color: var(--text-primary); font-size: 2rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.5px; transition: color 0.3s; }
.header-titles p { color: var(--text-secondary); margin: 0; font-size: 1.05rem; transition: color 0.3s; }

.tabs-container { display: flex; gap: 15px; margin-bottom: 25px; border-bottom: 2px solid var(--border-color); padding-bottom: 15px; transition: border-color 0.3s; }
.tab-btn { background: transparent; border: none; color: var(--text-secondary); font-size: 1.05rem; font-weight: 700; padding: 12px 24px; cursor: pointer; transition: all 0.3s; border-radius: 12px; }
.tab-btn.active { background: var(--bg-card); color: var(--text-primary); box-shadow: var(--shadow-sm); border: 1px solid var(--border-color); }
.tab-btn:hover:not(.active) { color: var(--text-primary); background: var(--input-bg); }

.action-btn { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 14px 24px; border-radius: 14px; font-weight: 700; font-size: 1rem; cursor: pointer; border: none; transition: all 0.3s; color: white; }
.btn-primary { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.3); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 15px 25px -5px rgba(15, 23, 42, 0.4); }
.btn-icon { font-size: 1.3rem; font-weight: 900; line-height: 1; }

.btn-refresh { display: flex; align-items: center; gap: 8px; background-color: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-input); padding: 12px 20px; border-radius: 12px; cursor: pointer; font-weight: 700; font-size: 0.95rem; transition: all 0.2s; box-shadow: var(--shadow-sm); }
.btn-refresh:hover { background-color: var(--bg-main); border-color: var(--text-secondary); transform: translateY(-2px); }

.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 80px 0; color: var(--text-secondary); font-weight: 600; font-size: 1.1rem; }
.loader-spinner { width: 40px; height: 40px; border: 4px solid var(--border-color); border-bottom-color: #f7b500; border-radius: 50%; margin-bottom: 20px; animation: rotation 1s linear infinite; }
@keyframes rotation { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.portfolio-overview { display: flex; gap: 25px; margin-bottom: 35px; }
.overview-card { flex: 1; padding: 35px 30px; border-radius: 24px; box-shadow: var(--shadow-lg); transition: background-color 0.3s, border-color 0.3s; }
.primary-card { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; }
.secondary-card { background: var(--bg-card); border: 1px solid var(--border-color); }
.overview-card h3 { font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 10px 0; }
.primary-card h3 { color: #94a3b8; }
.secondary-card h3 { color: var(--text-secondary); transition: color 0.3s; }

.amount-huge { font-size: 2.8rem; font-weight: 900; margin: 0 0 5px 0; letter-spacing: -1px; }
.primary-card .amount-huge { color: #f7b500; }
.secondary-card .amount-huge { color: var(--text-primary); transition: color 0.3s; }
.amount-medium { font-size: 2.2rem; font-weight: 800; margin: 0 0 5px 0; letter-spacing: -0.5px; color: var(--text-primary); transition: color 0.3s; }

.subtitle { margin: 0; font-size: 0.9rem; }
.primary-card .subtitle { color: #cbd5e1; }
.secondary-card .subtitle { color: var(--text-secondary); transition: color 0.3s; }

.dashboard-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 30px; margin-bottom: 40px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 25px; flex-wrap: wrap; gap: 15px; }
.header-text-group { display: flex; align-items: center; gap: 15px; }
.section-header h2 { color: var(--text-primary); font-size: 1.4rem; font-weight: 800; margin: 0; transition: color 0.3s; }
.live-badge { background-color: var(--positive-bg); color: #059669; padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }

.search-wrapper { position: relative; width: 260px; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-secondary); }
.market-search { width: 100%; padding: 10px 15px 10px 40px; border: 1px solid var(--border-input); border-radius: 12px; font-size: 0.95rem; outline: none; transition: all 0.3s; background-color: var(--input-bg); color: var(--text-primary); }
.market-search:focus { border-color: #f7b500; background-color: var(--bg-card); box-shadow: 0 0 0 3px rgba(247, 181, 0, 0.1); }

.asset-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; max-height: 800px; overflow-y: auto; padding-right: 10px; }
.asset-grid::-webkit-scrollbar { width: 6px; }
.asset-grid::-webkit-scrollbar-thumb { background-color: var(--border-input); border-radius: 4px; }
.asset-card { background: var(--bg-card); border-radius: 20px; padding: 22px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); display: flex; flex-direction: column; transition: all 0.3s; }
.asset-card:hover { transform: translateY(-5px); box-shadow: var(--shadow-lg); }
.asset-info { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.coin-logo { width: 36px; height: 36px; border-radius: 50%; }
.asset-title h3 { margin: 0 0 2px 0; font-size: 1.2rem; color: var(--text-primary); font-weight: 900; transition: color 0.3s; }
.asset-name { color: var(--text-secondary); font-size: 0.85rem; font-weight: 500; transition: color 0.3s; }
.asset-price-box { margin-bottom: 25px; }
.asset-price { font-size: 1.5rem; font-weight: 800; color: var(--text-primary); margin: 0 0 5px 0; transition: color 0.3s; }
.asset-change { margin: 0; font-size: 0.9rem; font-weight: 700; }

.text-positive { color: #059669 !important; }
.text-negative { color: #dc2626 !important; }
.text-primary { color: var(--text-primary); }
.text-secondary-sub { margin: 2px 0 0 0; color: var(--text-secondary); font-size: 0.84rem; }
.text-white { color: white !important; }

.btn-trade { width: 100%; padding: 12px; border: none; border-radius: 12px; font-weight: 800; font-size: 1rem; cursor: pointer; transition: all 0.2s; }
.btn-buy { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2); }
.btn-buy:hover { transform: translateY(-2px); box-shadow: 0 8px 15px rgba(16, 185, 129, 0.3); }

.empty-market, .empty-wallet { text-align: center; padding: 40px; color: var(--text-secondary); font-weight: 500; background: var(--bg-card); border-radius: 20px; border: 1px solid var(--border-color); transition: all 0.3s; }
.empty-state-container { text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: 20px; border: 1px dashed var(--border-color); margin-top: 20px; }
.empty-icon { font-size: 3rem; margin-bottom: 15px; }
.empty-state-container h3 { color: var(--text-primary); font-size: 1.4rem; margin: 0 0 10px 0; }
.empty-state-container p { color: var(--text-secondary); margin: 0; font-size: 1rem; }

.my-coins-list { display: flex; flex-direction: column; gap: 15px; }
.my-coin-card { background: var(--bg-card); padding: 20px; border-radius: 16px; border: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; transition: all 0.3s; }
.my-coin-card:hover { box-shadow: var(--shadow-md); }
.my-coin-left { display: flex; align-items: center; gap: 12px; }
.my-coin-logo { width: 32px; height: 32px; border-radius: 50%; }
.my-coin-details { display: flex; flex-direction: column; gap: 2px; }
.my-coin-symbol { font-weight: 800; color: var(--text-primary); font-size: 1rem; transition: color 0.3s; }
.my-coin-amount { color: var(--text-secondary); font-size: 0.85rem; font-weight: 500; transition: color 0.3s; }
.my-coin-value { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
.fiat-value { font-weight: 800; color: var(--text-primary); font-size: 1.05rem; transition: color 0.3s; }

.btn-trade-small { padding: 6px 16px; border: none; border-radius: 8px; font-weight: 700; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; }
.btn-sell { background-color: var(--negative-bg); color: #dc2626; }
.btn-sell:hover:not(:disabled) { opacity: 0.8; }

.performance-section { margin-bottom: 35px; }
.performance-card { background: var(--bg-card); border-radius: 20px; padding: 24px; border: 1px solid var(--border-color); box-shadow: var(--shadow-md); transition: all 0.3s; }
.performance-table-head, .performance-row { display: grid; grid-template-columns: 1.4fr 1fr 1fr 1fr 1.4fr; gap: 16px; align-items: center; }
.performance-table-head { padding-bottom: 14px; margin-bottom: 10px; border-bottom: 1px solid var(--border-input); color: var(--text-secondary); font-size: 0.82rem; font-weight: 700; text-transform: uppercase; transition: all 0.3s; }
.performance-row { padding: 16px 0; border-bottom: 1px solid var(--border-color); transition: all 0.3s; }
.performance-row:last-child { border-bottom: none; }
.coin-cell { display: flex; align-items: center; gap: 12px; }
.mini-coin-logo { width: 28px; height: 28px; border-radius: 50%; }
.performance-bar-wrap { display: flex; align-items: center; gap: 10px; }
.performance-bar-bg { flex: 1; height: 10px; background: var(--border-color); border-radius: 999px; overflow: hidden; transition: background-color 0.3s; }
.performance-bar-fill { height: 100%; border-radius: 999px; }
.profit-fill { background: linear-gradient(90deg, #34d399 0%, #10b981 100%); }
.loss-fill { background: linear-gradient(90deg, #f87171 0%, #ef4444 100%); }

.investments-container { background: var(--bg-card); border-radius: 20px; padding: 10px 25px 25px 25px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); overflow-x: auto; transition: all 0.3s; }
.transaction-table { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 800px; }
.transaction-table th, .transaction-table td { padding: 18px 15px; text-align: left; border-bottom: 1px solid var(--border-color); transition: border-color 0.3s; }
.transaction-table th { color: var(--text-secondary); font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; padding-top: 25px; transition: color 0.3s; }
.transaction-table td { color: var(--text-primary); font-size: 1rem; transition: color 0.3s; }
.transaction-table tr:last-child td { border-bottom: none; }
.transaction-table tr:hover td { background-color: var(--bg-main); }
.asset-info { display: flex; flex-direction: column; gap: 4px; }
.td-date { color: var(--text-secondary); font-size: 0.85rem; font-weight: 500; transition: color 0.3s; }
.td-desc { color: var(--text-primary); font-size: 1.05rem; transition: color 0.3s; }
.category-tag { background-color: var(--neutral-bg); color: var(--text-secondary); padding: 6px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; }
.profit-badge { padding: 6px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 700; display: inline-block; }
.badge-positive { background-color: var(--positive-bg); color: #059669; }
.badge-negative { background-color: var(--negative-bg); color: #dc2626; }
.action-icon { background: var(--bg-card); border: 1px solid var(--border-input); border-radius: 8px; color: var(--text-secondary); cursor: pointer; padding: 8px; margin: 0 4px; display: inline-flex; align-items: center; justify-content: center; transition: all 0.2s; }
.action-icon:hover { background: var(--bg-main); color: var(--text-primary); border-color: var(--text-secondary); transform: translateY(-2px); }
.icon-danger:hover { background: var(--negative-bg); color: #dc2626; border-color: #fecaca; }

.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-container { background: var(--bg-card); width: 100%; max-width: 520px; border-radius: 24px; box-shadow: var(--shadow-lg); border: 1px solid var(--border-color); padding: 35px; animation: modalSlideIn 0.3s ease-out; transition: all 0.3s; }
.small-modal { max-width: 400px; }
@keyframes modalSlideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.modal-header-title { display: flex; align-items: center; gap: 12px; }
.modal-coin-logo { width: 28px; height: 28px; border-radius: 50%; }
.modal-header h2 { margin: 0; color: var(--text-primary); font-size: 1.4rem; font-weight: 800; transition: color 0.3s; }
.close-btn { background: var(--bg-main); border: none; width: 36px; height: 36px; border-radius: 50%; font-size: 1.5rem; color: var(--text-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center; line-height: 1; transition: all 0.2s; }
.close-btn:hover { background: var(--border-color); color: var(--text-primary); }

.trade-info-box { background-color: var(--neutral-bg); padding: 15px 20px; border-radius: 12px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 8px; font-size: 0.95rem; color: var(--text-secondary); transition: all 0.3s; }
.trade-price-row, .trade-balance-row { display: flex; justify-content: space-between; }
.fw-700 { font-weight: 700; color: var(--text-primary); transition: color 0.3s; }

.modal-form { display: flex; flex-direction: column; gap: 20px; }
.form-row { display: flex; gap: 20px; }
.form-group { display: flex; flex-direction: column; gap: 10px; flex: 1; min-width: 0; }
.full-width { width: 100%; }
.label-with-action { display: flex; justify-content: space-between; align-items: center; }
.form-group label { font-size: 0.95rem; font-weight: 600; color: var(--text-secondary); transition: color 0.3s; }
.btn-sell-all { background: none; border: none; color: #059669; font-weight: 700; font-size: 0.85rem; cursor: pointer; padding: 0; }
.btn-sell-all:hover { text-decoration: underline; }
.form-group input, .form-group select { width: 100%; box-sizing: border-box; padding: 16px; border: 1px solid var(--border-input); border-radius: 12px; font-size: 1rem; font-family: 'Inter', sans-serif; outline: none; background-color: var(--input-bg); color: var(--text-primary); transition: all 0.3s; }
.form-group input:focus, .form-group select:focus { border-color: #f7b500; background-color: var(--bg-card); box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1); }
.conversion-result { text-align: center; padding: 15px; background-color: var(--neutral-bg); border-radius: 12px; border: 1px dashed var(--border-input); transition: all 0.3s; }
.conversion-result p { margin: 0 0 5px 0; color: var(--text-secondary); font-size: 0.9rem; transition: color 0.3s; }
.conversion-result h3 { margin: 0; color: var(--text-primary); font-size: 1.3rem; font-weight: 800; transition: color 0.3s; }

.modal-actions { display: flex; gap: 15px; margin-top: 10px; }
.btn-cancel { flex: 1; padding: 16px; background-color: var(--bg-main); color: var(--text-secondary); border: 1px solid var(--border-color); border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: all 0.2s; }
.btn-cancel:hover { background-color: var(--border-color); color: var(--text-primary); }
.btn-save { flex: 1; padding: 16px; color: white; border: none; border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.2s; }
.btn-save:hover { transform: translateY(-2px); }
.bg-positive { background: linear-gradient(135deg, #10b981 0%, #059669 100%); box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3); }
.bg-negative { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3); }
.modal-body p { color: var(--text-secondary); font-size: 1.05rem; line-height: 1.5; margin-bottom: 25px; }

@media (max-width: 1024px) {
  .dashboard-grid { grid-template-columns: 1fr; }
  .performance-table-head, .performance-row { grid-template-columns: 1fr; }
  .performance-table-head { display: none; }
  .performance-row { gap: 8px; padding: 18px 0; }
  .portfolio-overview { flex-direction: column; }
}

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 15px; }
  .btn-refresh { width: 100%; justify-content: center; }
  .tabs-container { flex-direction: column; gap: 10px; border-bottom: none; }
  .tab-btn { width: 100%; text-align: center; }
  .search-wrapper { width: 100%; }
  .form-row { flex-direction: column; }
}
</style>