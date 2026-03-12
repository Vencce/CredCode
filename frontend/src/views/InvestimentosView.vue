<script setup>
import { ref, onMounted, reactive } from 'vue'
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

const cryptoData = ref([])
const fiiData = ref([])
const isLoading = ref(true)

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

const fetchCryptoData = async () => {
  try {
    const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=brl&include_24hr_change=true')
    if (response.ok) {
      const data = await response.json()
      cryptoData.value = [
        {
          id: 'btc',
          name: 'Bitcoin',
          symbol: 'BTC',
          price: data.bitcoin.brl,
          change: data.bitcoin.brl_24h_change
        },
        {
          id: 'eth',
          name: 'Ethereum',
          symbol: 'ETH',
          price: data.ethereum.brl,
          change: data.ethereum.brl_24h_change
        },
        {
          id: 'sol',
          name: 'Solana',
          symbol: 'SOL',
          price: data.solana.brl,
          change: data.solana.brl_24h_change
        }
      ]
    }
  } catch (error) {
    showToast('Erro ao carregar dados de criptomoedas', 'error')
  }
}

const fetchFiiData = () => {
  fiiData.value = [
    { id: 'mxrf11', name: 'Maxi Renda', symbol: 'MXRF11', price: 10.45, change: 0.15 },
    { id: 'hglg11', name: 'CSHG Logística', symbol: 'HGLG11', price: 162.30, change: -0.42 },
    { id: 'visc11', name: 'Vinci Shopping', symbol: 'VISC11', price: 118.50, change: 1.20 }
  ]
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
    await fetchCryptoData()
    fetchFiiData()
    isLoading.value = false
  }
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

const formatPercent = (value) => {
  return Number(value).toFixed(2) + '%'
}

const handleBuyAction = (symbol) => {
  showToast(`Módulo de compra para ${symbol} em desenvolvimento`, 'success')
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  
  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Cotações em Tempo Real</h1>
        <p>Acompanhe o mercado de Criptomoedas e Fundos Imobiliários</p>
      </div>
      <button @click="fetchCryptoData" class="btn-refresh">🔄 Atualizar Dados</button>
    </div>

    <div v-if="isLoading" class="loading-state">
      <p>Sincronizando com o mercado...</p>
    </div>

    <div v-else>
      <section class="market-section">
        <div class="section-header">
          <h2>Criptomoedas</h2>
          <span class="live-badge">Ao Vivo (CoinGecko)</span>
        </div>
        
        <div class="asset-grid">
          <div v-for="coin in cryptoData" :key="coin.id" class="asset-card">
            <div class="asset-info">
              <div class="asset-title">
                <h3>{{ coin.symbol }}</h3>
                <span class="asset-name">{{ coin.name }}</span>
              </div>
            </div>
            <div class="asset-price-box">
              <p class="asset-price">{{ formatCurrency(coin.price) }}</p>
              <p :class="['asset-change', coin.change >= 0 ? 'text-positive' : 'text-negative']">
                {{ coin.change >= 0 ? '▲' : '▼' }} {{ formatPercent(coin.change) }} (24h)
              </p>
            </div>
            <button @click="handleBuyAction(coin.symbol)" class="btn-trade">Operar {{ coin.symbol }}</button>
          </div>
        </div>
      </section>

      <section class="market-section">
        <div class="section-header">
          <h2>Fundos Imobiliários (FIIs)</h2>
          <span class="api-badge">B3</span>
        </div>
        
        <div class="asset-grid">
          <div v-for="fii in fiiData" :key="fii.id" class="asset-card">
            <div class="asset-info">
              <div class="asset-title">
                <h3>{{ fii.symbol }}</h3>
                <span class="asset-name">{{ fii.name }}</span>
              </div>
            </div>
            <div class="asset-price-box">
              <p class="asset-price">{{ formatCurrency(fii.price) }}</p>
              <p :class="['asset-change', fii.change >= 0 ? 'text-positive' : 'text-negative']">
                {{ fii.change >= 0 ? '▲' : '▼' }} {{ formatPercent(fii.change) }}
              </p>
            </div>
            <button @click="handleBuyAction(fii.symbol)" class="btn-trade fii-trade">Operar {{ fii.symbol }}</button>
          </div>
        </div>
      </section>
    </div>

    <FooterComp />
  </SideLayout>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
}

.header-titles h1 {
  color: #0a2a43;
  font-size: 1.8rem;
  font-weight: 800;
  margin: 0 0 5px 0;
}

.header-titles p {
  color: #64748b;
  margin: 0;
  font-size: 1rem;
}

.btn-refresh {
  background-color: white;
  color: #0a2a43;
  border: 1px solid #e2e8f0;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}

.btn-refresh:hover {
  background-color: #f8fafc;
  border-color: #cbd5e1;
  transform: translateY(-2px);
}

.loading-state {
  text-align: center;
  padding: 60px 0;
  color: #64748b;
  font-weight: 600;
  font-size: 1.1rem;
}

.market-section {
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.section-header h2 {
  color: #0a2a43;
  font-size: 1.3rem;
  font-weight: 800;
  margin: 0;
}

.live-badge {
  background-color: #dcfce7;
  color: #166534;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.api-badge {
  background-color: #f1f5f9;
  color: #475569;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.asset-card {
  background: white;
  border-radius: 16px;
  padding: 25px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
  border: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s, box-shadow 0.2s;
}

.asset-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06);
}

.asset-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.asset-title h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #0a2a43;
  font-weight: 800;
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
  font-size: 1.8rem;
  font-weight: 800;
  color: #0a2a43;
  margin: 0 0 5px 0;
}

.asset-change {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
}

.text-positive { color: #10b981; }
.text-negative { color: #ef4444; }

.btn-trade {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  background-color: #f7b500;
  color: #0a2a43;
  transition: background-color 0.2s;
}

.btn-trade:hover {
  background-color: #e6a800;
}

.fii-trade {
  background-color: #0a2a43;
  color: white;
}

.fii-trade:hover {
  background-color: #153e5c;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .btn-refresh {
    width: 100%;
  }
}
</style>