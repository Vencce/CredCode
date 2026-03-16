<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue'

const router = useRouter()
const isAuthorized = ref(false)
const isLoading = ref(true)

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

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
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

const loadBalance = async (token) => {
  try {
    let baseBalance = 0
    const profileRes = await fetch('http://localhost:8000/api/finances/profile/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    if (profileRes.ok) {
      const data = await profileRes.json()
      if (data.account_balance !== undefined && data.account_balance !== null) {
        baseBalance = parseFloat(data.account_balance) || 0
      }
    }

    const walletRes = await fetch('http://localhost:8000/api/finances/wallets/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    if (walletRes.ok) {
      const wallets = await walletRes.json()
      if (wallets.length > 0) {
        defaultWalletId.value = wallets[0].id
        if (baseBalance === 0 && wallets[0].balance !== undefined && wallets[0].balance !== null) {
          baseBalance = parseFloat(wallets[0].balance) || 0
        }
      }
    }

    const expensesRes = await fetch('http://localhost:8000/api/finances/expenses/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })

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

const loadLocalCryptoWallet = () => {
  const saved = localStorage.getItem('crypto_wallet')
  if (saved) {
    const parsed = JSON.parse(saved)
    Object.keys(parsed).forEach(key => {
      myCrypto[key] = parsed[key]
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
    setTimeout(() => {
      router.push('/')
    }, 1500)
  } else {
    isAuthorized.value = true
    loadLocalCryptoWallet()
    await fetchMarketData()
    await loadBalance(token)
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
  if (!searchQuery.value) {
    return cryptoMarket.value.slice(0, 12)
  }
  const query = searchQuery.value.toLowerCase()
  return cryptoMarket.value.filter(c => 
    c.name.toLowerCase().includes(query) || 
    c.symbol.toLowerCase().includes(query)
  )
})

const myCoinsList = computed(() => {
  return cryptoMarket.value.filter(c => myCrypto[c.id] > 0)
})

const totalCryptoPortfolioBRL = computed(() => {
  let total = 0
  myCoinsList.value.forEach(coin => {
    total += (myCrypto[coin.id] || 0) * coin.price
  })
  return total
})

const calculatedTradeValue = computed(() => {
  if (!selectedCoin.value || !tradeAmountStr.value) return 0
  const amount = parseFloat(tradeAmountStr.value) || 0

  if (tradeType.value === 'buy') {
    return amount / selectedCoin.value.price
  } else {
    return amount * selectedCoin.value.price
  }
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
    tradeAmountStr.value = myCrypto[selectedCoin.value.id].toString()
  }
}

const executeTrade = async () => {
  let amount = parseFloat(tradeAmountStr.value)
  if (!amount || amount <= 0) {
    showToast('Insira um valor válido maior que zero.', 'error')
    return
  }

  if (!defaultWalletId.value) {
    showToast('Sua carteira BRL principal não foi encontrada.', 'error')
    return
  }

  let brlImpact = 0
  let cryptoImpact = 0

  if (tradeType.value === 'buy') {
    if (amount > userData.balance) {
      showToast('Saldo insuficiente em BRL.', 'error')
      return
    }
    brlImpact = -Math.abs(amount)
    cryptoImpact = amount / selectedCoin.value.price
  } else {
    if (Math.abs(amount - myCrypto[selectedCoin.value.id]) < 0.000001) {
      amount = myCrypto[selectedCoin.value.id]
    }
    if (amount > myCrypto[selectedCoin.value.id]) {
      showToast(`Saldo insuficiente de ${selectedCoin.value.symbol}.`, 'error')
      return
    }
    brlImpact = Math.abs(amount * selectedCoin.value.price)
    cryptoImpact = -Math.abs(amount)
  }

  const token = localStorage.getItem('access_token')
  const description = tradeType.value === 'buy' 
    ? `[Investimentos] Compra de ${selectedCoin.value.symbol}`
    : `[Investimentos] Venda de ${selectedCoin.value.symbol}`

  const payload = {
    wallet: defaultWalletId.value,
    description: description,
    amount: brlImpact,
    date: new Date().toISOString().split('T')[0],
    category: 'Investimentos'
  }

  try {
    const response = await fetch('http://localhost:8000/api/finances/expenses/', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (response.ok) {
      if (!myCrypto[selectedCoin.value.id]) {
        myCrypto[selectedCoin.value.id] = 0
      }
      myCrypto[selectedCoin.value.id] += cryptoImpact
      
      if (myCrypto[selectedCoin.value.id] < 0.000001) {
        myCrypto[selectedCoin.value.id] = 0
      }
      
      saveLocalCryptoWallet()
      await loadBalance(token)
      showToast('Ordem executada com sucesso!', 'success')
      closeTradeModal()
    } else {
      showToast('Erro ao processar transação no banco.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  }
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  
  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Home Broker</h1>
        <p>Negocie criptomoedas em tempo real</p>
      </div>
      <button @click="fetchMarketData" class="btn-refresh">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><polyline points="3 3 3 8 8 8"></polyline></svg>
        Sincronizar
      </button>
    </div>

    <div v-if="isLoading" class="loading-state">
      <div class="loader-spinner"></div>
      <p>Conectando ao mercado...</p>
    </div>

    <div v-else>
      <div class="portfolio-overview">
        <div class="overview-card primary-card">
          <h3>Seu Portfólio Cripto</h3>
          <p class="amount-huge">{{ formatCurrency(totalCryptoPortfolioBRL) }}</p>
          <p class="subtitle">Valor total estimado em conta</p>
        </div>
        <div class="overview-card secondary-card">
          <h3>Poder de Compra</h3>
          <p class="amount-medium">{{ formatCurrency(userData.balance) }}</p>
          <p class="subtitle">Saldo disponível em R$</p>
        </div>
      </div>

      <div class="dashboard-grid">
        <section class="market-section">
          <div class="section-header">
            <div class="header-text-group">
              <h2>Mercado</h2>
              <span class="live-badge">Ao Vivo</span>
            </div>
            <div class="search-wrapper">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="search-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <input type="text" v-model="searchQuery" placeholder="Buscar criptomoeda..." class="market-search" />
            </div>
          </div>
          
          <div class="asset-grid">
            <div v-for="coin in filteredMarket" :key="coin.id" class="asset-card">
              <div class="asset-info">
                <img :src="coin.image" :alt="coin.name" class="coin-logo" />
                <div class="asset-title">
                  <h3>{{ coin.symbol }}</h3>
                  <span class="asset-name">{{ coin.name }}</span>
                </div>
              </div>
              <div class="asset-price-box">
                <p class="asset-price">{{ formatCurrency(coin.price) }}</p>
                <p :class="['asset-change', coin.change >= 0 ? 'text-positive' : 'text-negative']">
                  {{ coin.change >= 0 ? '▲' : '▼' }} {{ formatPercent(coin.change) }}
                </p>
              </div>
              <button @click="openTradeModal('buy', coin)" class="btn-trade btn-buy">Comprar</button>
            </div>
          </div>
          
          <div v-if="filteredMarket.length === 0" class="empty-market">
            <p>Nenhuma criptomoeda encontrada.</p>
          </div>
        </section>

        <section class="wallet-section">
          <div class="section-header">
            <h2>Sua Carteira</h2>
          </div>
          
          <div class="my-coins-list">
            <div v-if="myCoinsList.length === 0" class="empty-wallet">
              Você ainda não possui criptomoedas.
            </div>
            <div v-for="coin in myCoinsList" :key="'my-'+coin.id" class="my-coin-card">
              <div class="my-coin-left">
                <img :src="coin.image" class="my-coin-logo" />
                <div class="my-coin-details">
                  <span class="my-coin-symbol">{{ coin.symbol }}</span>
                  <span class="my-coin-amount">{{ formatCrypto(myCrypto[coin.id], '') }}</span>
                </div>
              </div>
              <div class="my-coin-value">
                <span class="fiat-value">{{ formatCurrency(myCrypto[coin.id] * coin.price) }}</span>
                <button 
                  @click="openTradeModal('sell', coin)" 
                  class="btn-trade-small btn-sell"
                >Vender</button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <FooterComp />

    <div v-if="showTradeModal" class="modal-overlay" @click.self="closeTradeModal">
      <div class="modal-container">
        <div class="modal-header">
          <div class="modal-header-title">
            <img :src="selectedCoin.image" class="modal-coin-logo" />
            <h2>{{ tradeType === 'buy' ? 'Comprar' : 'Vender' }} {{ selectedCoin.symbol }}</h2>
          </div>
          <button class="close-btn" @click="closeTradeModal">&times;</button>
        </div>
        
        <form @submit.prevent="executeTrade" class="modal-form">
          
          <div class="trade-info-box">
            <div class="trade-price-row">
              <span>Cotação atual:</span>
              <span class="fw-700">{{ formatCurrency(selectedCoin.price) }}</span>
            </div>
            <div class="trade-balance-row">
              <span>Disponível:</span>
              <span class="fw-700">
                {{ tradeType === 'buy' 
                  ? formatCurrency(userData.balance) 
                  : formatCrypto(myCrypto[selectedCoin.id], selectedCoin.symbol) 
                }}
              </span>
            </div>
          </div>

          <div class="form-group">
            <div class="label-with-action">
              <label>{{ tradeType === 'buy' ? 'Valor do investimento (R$)' : `Quantidade de ${selectedCoin.symbol} para venda` }}</label>
              <button type="button" class="btn-sell-all" v-if="tradeType === 'sell'" @click="setSellAll">Vender Tudo</button>
            </div>
            <input 
              v-model="tradeAmountStr" 
              type="number" 
              step="any" 
              min="0.000001" 
              :placeholder="tradeType === 'buy' ? 'R$ 0,00' : '0.0000'" 
              required 
            />
          </div>

          <div class="conversion-result" v-if="tradeAmountStr && parseFloat(tradeAmountStr) > 0">
            <p>Você irá {{ tradeType === 'buy' ? 'receber' : 'receber' }}:</p>
            <h3>
              {{ tradeType === 'buy' 
                ? formatCrypto(calculatedTradeValue, selectedCoin.symbol) 
                : formatCurrency(calculatedTradeValue) 
              }}
            </h3>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeTradeModal">Cancelar</button>
            <button type="submit" :class="['btn-save', tradeType === 'buy' ? 'bg-positive' : 'bg-negative']">
              Confirmar {{ tradeType === 'buy' ? 'Compra' : 'Venda' }}
            </button>
          </div>
        </form>
      </div>
    </div>
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

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: white;
  color: #0f172a;
  border: 1px solid #cbd5e1;
  padding: 12px 20px;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.95rem;
  transition: all 0.2s;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.btn-refresh:hover {
  background-color: #f8fafc;
  border-color: #94a3b8;
  transform: translateY(-2px);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #64748b;
  font-weight: 600;
  font-size: 1.1rem;
}

.loader-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-bottom-color: #f7b500;
  border-radius: 50%;
  margin-bottom: 20px;
  animation: rotation 1s linear infinite;
}

@keyframes rotation {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.portfolio-overview {
  display: flex;
  gap: 25px;
  margin-bottom: 35px;
}

.overview-card {
  flex: 1;
  padding: 35px 30px;
  border-radius: 24px;
  box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.05);
}

.primary-card {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: white;
}

.secondary-card {
  background: white;
  border: 1px solid #f1f5f9;
}

.overview-card h3 {
  font-size: 1rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 10px 0;
}

.primary-card h3 { color: #94a3b8; }
.secondary-card h3 { color: #64748b; }

.amount-huge {
  font-size: 2.8rem;
  font-weight: 900;
  margin: 0 0 5px 0;
  letter-spacing: -1px;
}

.primary-card .amount-huge { color: #f7b500; }
.secondary-card .amount-huge { color: #0f172a; }

.amount-medium {
  font-size: 2.2rem;
  font-weight: 800;
  margin: 0 0 5px 0;
  letter-spacing: -0.5px;
  color: #0f172a;
}

.subtitle {
  margin: 0;
  font-size: 0.9rem;
}

.primary-card .subtitle { color: #cbd5e1; }
.secondary-card .subtitle { color: #94a3b8; }

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 30px;
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 25px;
  flex-wrap: wrap;
  gap: 15px;
}

.header-text-group {
  display: flex;
  align-items: center;
  gap: 15px;
}

.section-header h2 {
  color: #0f172a;
  font-size: 1.4rem;
  font-weight: 800;
  margin: 0;
}

.live-badge {
  background-color: #ecfdf5;
  color: #059669;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.search-wrapper {
  position: relative;
  width: 260px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
}

.market-search {
  width: 100%;
  padding: 10px 15px 10px 40px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  font-size: 0.95rem;
  outline: none;
  font-family: 'Inter', sans-serif;
  transition: all 0.3s;
  background-color: #f8fafc;
}

.market-search:focus {
  border-color: #f7b500;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(247, 181, 0, 0.1);
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
  max-height: 800px;
  overflow-y: auto;
  padding-right: 10px;
}

.asset-grid::-webkit-scrollbar {
  width: 6px;
}

.asset-grid::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 4px;
}

.asset-card {
  background: white;
  border-radius: 20px;
  padding: 22px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.02);
  border: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s, box-shadow 0.2s;
}

.asset-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05);
}

.asset-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.coin-logo {
  width: 36px;
  height: 36px;
  border-radius: 50%;
}

.asset-title h3 {
  margin: 0 0 2px 0;
  font-size: 1.2rem;
  color: #0f172a;
  font-weight: 900;
}

.asset-name {
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 500;
}

.asset-price-box {
  margin-bottom: 25px;
}

.asset-price {
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 5px 0;
}

.asset-change {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
}

.text-positive { color: #059669; }
.text-negative { color: #dc2626; }

.btn-trade {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 12px;
  font-weight: 800;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-buy {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
}

.btn-buy:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 15px rgba(16, 185, 129, 0.3);
}

.empty-market, .empty-wallet {
  text-align: center;
  padding: 40px;
  color: #94a3b8;
  font-weight: 500;
  background: white;
  border-radius: 20px;
  border: 1px solid #f1f5f9;
}

.my-coins-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.my-coin-card {
  background: white;
  padding: 20px;
  border-radius: 16px;
  border: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: box-shadow 0.2s;
}

.my-coin-card:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.03);
}

.my-coin-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.my-coin-logo {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.my-coin-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.my-coin-symbol {
  font-weight: 800;
  color: #0f172a;
  font-size: 1rem;
}

.my-coin-amount {
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 500;
}

.my-coin-value {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.fiat-value {
  font-weight: 800;
  color: #0f172a;
  font-size: 1.05rem;
}

.btn-trade-small {
  padding: 6px 16px;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-sell {
  background-color: #fef2f2;
  color: #dc2626;
}

.btn-sell:hover:not(:disabled) {
  background-color: #fee2e2;
}

.btn-sell:disabled {
  background-color: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
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
  max-width: 450px;
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  padding: 35px;
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.modal-header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-coin-logo {
  width: 28px;
  height: 28px;
  border-radius: 50%;
}

.modal-header h2 {
  margin: 0;
  color: #0f172a;
  font-size: 1.4rem;
  font-weight: 800;
}

.close-btn {
  background: #f1f5f9;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 1.5rem;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  line-height: 1;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.trade-info-box {
  background-color: #f8fafc;
  padding: 15px 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 0.95rem;
  color: #475569;
}

.trade-price-row, .trade-balance-row {
  display: flex;
  justify-content: space-between;
}

.fw-700 { font-weight: 700; color: #0f172a; }

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.label-with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-group label {
  font-size: 0.95rem;
  font-weight: 600;
  color: #475569;
}

.btn-sell-all {
  background: none;
  border: none;
  color: #059669;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0;
}

.btn-sell-all:hover {
  text-decoration: underline;
}

.form-group input {
  padding: 16px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  font-size: 1.1rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  background-color: white;
  color: #0f172a;
  transition: all 0.3s;
}

.form-group input:focus {
  border-color: #f7b500;
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.conversion-result {
  text-align: center;
  padding: 15px;
  background-color: #f8fafc;
  border-radius: 12px;
  border: 1px dashed #cbd5e1;
}

.conversion-result p {
  margin: 0 0 5px 0;
  color: #64748b;
  font-size: 0.9rem;
}

.conversion-result h3 {
  margin: 0;
  color: #0f172a;
  font-size: 1.3rem;
  font-weight: 800;
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

.btn-cancel:hover { background-color: #e2e8f0; }

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

.btn-save:hover { transform: translateY(-2px); }

.bg-positive { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
.bg-negative { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }

@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .btn-refresh { width: 100%; justify-content: center; }
  
  .portfolio-overview {
    flex-direction: column;
  }

  .search-wrapper {
    width: 100%;
  }
}
</style>