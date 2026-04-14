<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue'

const router = useRouter()
const isAuthorized = ref(true)
const activeTab = ref('search')

const searchQuery = ref('')
const filterSupertype = ref('')
const filterRarity = ref('')
const cards = ref([])
const isLoading = ref(false)
const hasSearched = ref(false)

const collection = ref([])
const usdRate = ref(5.00)

const toast = reactive({
  show: false,
  message: '',
  type: 'error'
})

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

const fetchExchangeRate = async () => {
  try {
    const res = await fetch('https://economia.awesomeapi.com.br/last/USD-BRL')
    if (res.ok) {
      const data = await res.json()
      usdRate.value = parseFloat(data.USDBRL.ask)
    }
  } catch (e) {
    showToast('Erro ao buscar cotação do Dólar. Usando valor base de R$ 5,00.', 'error')
  }
}

const loadCollection = () => {
  const saved = localStorage.getItem('pokemon_collection')
  if (saved) {
    collection.value = JSON.parse(saved)
  }
}

const saveCollection = () => {
  localStorage.setItem('pokemon_collection', JSON.stringify(collection.value))
}

onMounted(() => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    router.push('/')
    return
  }
  fetchExchangeRate()
  loadCollection()
})

const formatPriceBRL = (priceUSD) => {
  if (!priceUSD) return 'Indisponível'
  const priceBRL = priceUSD * usdRate.value
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(priceBRL)
}

const getLowestPriceUSD = (card) => {
  if (!card.tcgplayer || !card.tcgplayer.prices) return 0
  const prices = card.tcgplayer.prices
  
  if (prices.normal && prices.normal.low) return prices.normal.low
  if (prices.holofoil && prices.holofoil.low) return prices.holofoil.low
  if (prices.reverseHolofoil && prices.reverseHolofoil.low) return prices.reverseHolofoil.low
  if (prices['1stEditionHolofoil'] && prices['1stEditionHolofoil'].low) return prices['1stEditionHolofoil'].low
  if (prices.unlimitedHolofoil && prices.unlimitedHolofoil.low) return prices.unlimitedHolofoil.low
  
  return 0
}

const searchCards = async () => {
  if (!searchQuery.value.trim() && !filterSupertype.value && !filterRarity.value) {
    showToast('Preencha pelo menos um filtro de pesquisa', 'error')
    return
  }
  
  isLoading.value = true
  hasSearched.value = true
  cards.value = []
  
  try {
    let queryArgs = []
    if (searchQuery.value.trim()) queryArgs.push(`name:"*${searchQuery.value.trim()}*"`)
    if (filterSupertype.value) queryArgs.push(`supertype:"${filterSupertype.value}"`)
    if (filterRarity.value) queryArgs.push(`rarity:"${filterRarity.value}"`)
    
    const finalQuery = queryArgs.join(' ')
    const res = await fetch(`https://api.pokemontcg.io/v2/cards?q=${encodeURIComponent(finalQuery)}&orderBy=-set.releaseDate&pageSize=50`)
    
    if (res.ok) {
      const data = await res.json()
      cards.value = data.data
      
      if (cards.value.length === 0) {
        showToast('Nenhuma carta encontrada.', 'error')
      }
    } else {
      showToast('Erro ao buscar cartas na API.', 'error')
    }
  } catch (e) {
    showToast('Erro de conexão com a API do TCG.', 'error')
  } finally {
    isLoading.value = false
  }
}

const isInCollection = (cardId) => {
  return collection.value.some(c => c.id === cardId)
}

const toggleCollection = (card) => {
  const index = collection.value.findIndex(c => c.id === card.id)
  if (index !== -1) {
    collection.value.splice(index, 1)
    showToast('Carta removida da coleção!', 'success')
  } else {
    const cardToSave = {
      id: card.id,
      name: card.name,
      images: card.images,
      set: card.set,
      tcgplayer: card.tcgplayer,
      rarity: card.rarity
    }
    collection.value.push(cardToSave)
    showToast('Carta adicionada à coleção!', 'success')
  }
  saveCollection()
}

const collectionTotalBRL = computed(() => {
  return collection.value.reduce((total, card) => {
    const priceUSD = getLowestPriceUSD(card)
    const priceBRL = priceUSD * usdRate.value
    return total + priceBRL
  }, 0)
})

const collectionTotalUSD = computed(() => {
  return collection.value.reduce((total, card) => {
    return total + getLowestPriceUSD(card)
  }, 0)
})

const formatRawUSD = (val) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  
  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Pokémon TCG</h1>
        <p>Gerencie sua coleção e consulte preços em tempo real</p>
      </div>
      <div class="exchange-badge">
        <span class="badge-label">Cotação USD</span>
        <span class="badge-value">R$ {{ usdRate.toFixed(2).replace('.', ',') }}</span>
      </div>
    </div>

    <div class="tabs-container">
      <button :class="['tab-btn', { active: activeTab === 'search' }]" @click="activeTab = 'search'">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        Pesquisar Cartas
      </button>
      <button :class="['tab-btn', { active: activeTab === 'collection' }]" @click="activeTab = 'collection'">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>
        Minha Coleção ({{ collection.length }})
      </button>
    </div>

    <div v-if="activeTab === 'search'" class="tab-content">
      <div class="search-section">
        <form @submit.prevent="searchCards" class="search-form">
          <div class="search-row">
            <div class="search-input-wrapper">
              <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              <input v-model="searchQuery" type="text" placeholder="Nome (Ex: Charizard, Mewtwo)..." class="search-input" />
            </div>
            
            <div class="filter-group">
              <select v-model="filterSupertype" class="search-select">
                <option value="">Qualquer Tipo</option>
                <option value="Pokémon">Pokémon</option>
                <option value="Trainer">Treinador</option>
                <option value="Energy">Energia</option>
              </select>
            </div>

            <div class="filter-group">
              <select v-model="filterRarity" class="search-select">
                <option value="">Qualquer Raridade</option>
                <option value="Common">Comum</option>
                <option value="Uncommon">Incomum</option>
                <option value="Rare">Rara</option>
                <option value="Rare Holo">Holo Rara</option>
                <option value="Rare Ultra">Ultra Rara</option>
                <option value="Rare Secret">Secreta Rara</option>
                <option value="Promo">Promo</option>
              </select>
            </div>

            <button type="submit" class="btn-search" :disabled="isLoading">
              <span v-if="!isLoading">Buscar</span>
              <span v-else class="spinner"></span>
            </button>
          </div>
        </form>
      </div>

      <div v-if="!isLoading && hasSearched && cards.length === 0" class="empty-state">
        <p>Nenhuma carta encontrada com esses filtros.</p>
      </div>

      <div v-if="cards.length > 0" class="cards-grid">
        <div v-for="card in cards" :key="card.id" class="tcg-card">
          <div class="tcg-image-container">
            <img :src="card.images.small" :alt="card.name" class="tcg-image" loading="lazy" />
          </div>
          <div class="tcg-info">
            <h3 class="tcg-name">{{ card.name }}</h3>
            <span class="tcg-set">{{ card.set.name }}</span>
            <span class="tcg-rarity" v-if="card.rarity">{{ card.rarity }}</span>
            
            <div class="tcg-price-box">
              <span class="price-label">Preço Base (BRL)</span>
              <span class="price-value">{{ formatPriceBRL(getLowestPriceUSD(card)) }}</span>
              <span class="price-usd">Ref: {{ formatRawUSD(getLowestPriceUSD(card)) }}</span>
            </div>

            <button 
              @click="toggleCollection(card)" 
              :class="['btn-collect', isInCollection(card.id) ? 'collected' : '']"
            >
              {{ isInCollection(card.id) ? 'Remover da Coleção' : 'Adicionar à Coleção' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'collection'" class="tab-content">
      <div class="collection-summary">
        <div class="summary-info">
          <h3>Valor Estimado da Coleção</h3>
          <p class="summary-total">{{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(collectionTotalBRL) }}</p>
          <span class="summary-usd">Aprox. {{ formatRawUSD(collectionTotalUSD) }}</span>
        </div>
        <div class="summary-stats">
          <div class="stat-box">
            <span class="stat-val">{{ collection.length }}</span>
            <span class="stat-label">Cartas Totais</span>
          </div>
        </div>
      </div>

      <div v-if="collection.length === 0" class="empty-state">
        <p>A sua coleção está vazia. Pesquise e adicione cartas!</p>
      </div>

      <div v-else class="cards-grid">
        <div v-for="card in collection" :key="card.id" class="tcg-card collected-card">
          <div class="tcg-image-container">
            <img :src="card.images.small" :alt="card.name" class="tcg-image" loading="lazy" />
          </div>
          <div class="tcg-info">
            <h3 class="tcg-name">{{ card.name }}</h3>
            <span class="tcg-set">{{ card.set.name }}</span>
            
            <div class="tcg-price-box">
              <span class="price-label">Valor (BRL)</span>
              <span class="price-value">{{ formatPriceBRL(getLowestPriceUSD(card)) }}</span>
            </div>

            <button @click="toggleCollection(card)" class="btn-collect collected">
              Remover da Coleção
            </button>
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

.exchange-badge {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  padding: 10px 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  box-shadow: var(--shadow-sm);
}

.badge-label {
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.badge-value {
  color: #f7b500;
  font-size: 1.2rem;
  font-weight: 900;
}

.tabs-container {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 15px;
}

.tab-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 1.05rem;
  font-weight: 700;
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-btn.active {
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.tab-btn:hover:not(.active) {
  color: var(--text-primary);
  background: var(--input-bg);
}

.search-section {
  background: var(--bg-card);
  padding: 25px;
  border-radius: 20px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  margin-bottom: 35px;
}

.search-row {
  display: flex;
  gap: 15px;
  width: 100%;
}

.search-input-wrapper {
  flex: 2;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 16px;
  color: var(--text-secondary);
}

.search-input {
  width: 100%;
  padding: 16px 20px 16px 45px;
  border: 1px solid var(--border-input);
  border-radius: 14px;
  font-size: 1rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  background-color: var(--input-bg);
  color: var(--text-primary);
  transition: all 0.3s;
}

.search-input:focus {
  border-color: #f7b500;
  background-color: var(--bg-card);
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.filter-group {
  flex: 1;
}

.search-select {
  width: 100%;
  padding: 16px;
  border: 1px solid var(--border-input);
  border-radius: 14px;
  font-size: 1rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  background-color: var(--input-bg);
  color: var(--text-primary);
  transition: all 0.3s;
  cursor: pointer;
}

.search-select:focus {
  border-color: #f7b500;
  background-color: var(--bg-card);
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.btn-search {
  padding: 0 30px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 14px;
  font-weight: 800;
  font-size: 1.05rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
}

.btn-search:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 15px 25px -5px rgba(16, 185, 129, 0.4);
}

.btn-search:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinner {
  width: 22px;
  height: 22px;
  border: 3px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 50px 20px;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 1.1rem;
  background: var(--input-bg);
  border-radius: 20px;
  border: 1px dashed var(--border-input);
  margin-bottom: 40px;
}

.collection-summary {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border-radius: 24px;
  padding: 35px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 35px;
  box-shadow: var(--shadow-lg);
  color: white;
}

.summary-info h3 {
  color: #94a3b8;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 10px 0;
  font-weight: 700;
}

.summary-total {
  font-size: 3rem;
  font-weight: 900;
  margin: 0;
  color: #f7b500;
  letter-spacing: -1px;
  text-shadow: 0 2px 10px rgba(247, 181, 0, 0.2);
}

.summary-usd {
  font-size: 0.9rem;
  color: #cbd5e1;
  font-weight: 600;
  margin-top: 5px;
  display: block;
}

.stat-box {
  background: rgba(255, 255, 255, 0.1);
  padding: 15px 25px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.stat-val {
  font-size: 1.8rem;
  font-weight: 800;
  color: white;
}

.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

.tcg-card {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 20px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.3s;
}

.tcg-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-input);
}

.collected-card {
  border-color: #10b981;
}

.tcg-image-container {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
}

.tcg-image {
  width: 100%;
  max-width: 200px;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 8px 16px rgba(0,0,0,0.15);
  transition: transform 0.3s;
}

.tcg-card:hover .tcg-image {
  transform: scale(1.03);
}

.tcg-info {
  width: 100%;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.tcg-name {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text-primary);
}

.tcg-set {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-secondary);
}

.tcg-rarity {
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--input-bg);
  padding: 2px 10px;
  border-radius: 12px;
  display: inline-block;
  margin: 0 auto;
  color: var(--text-primary);
}

.tcg-price-box {
  margin-top: auto;
  background: var(--input-bg);
  padding: 12px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 15px;
  border: 1px solid var(--border-input);
}

.price-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  font-weight: 800;
  color: var(--text-secondary);
}

.price-value {
  font-size: 1.3rem;
  font-weight: 900;
  color: #10b981;
}

.price-usd {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.btn-collect {
  width: 100%;
  padding: 12px;
  background: var(--bg-main);
  color: var(--text-primary);
  border: 1px solid var(--border-input);
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-collect:hover {
  background: var(--input-bg);
  border-color: #f7b500;
}

.btn-collect.collected {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.2);
}

.btn-collect.collected:hover {
  background: #ef4444;
  color: white;
}

@media (max-width: 1024px) {
  .search-row { flex-wrap: wrap; }
  .search-input-wrapper { flex: 1 1 100%; }
  .filter-group { flex: 1 1 45%; }
  .btn-search { flex: 1 1 100%; padding: 16px; }
}

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 15px; }
  .exchange-badge { align-self: stretch; align-items: center; flex-direction: row; justify-content: space-between; }
  
  .tabs-container { flex-direction: column; gap: 10px; border-bottom: none; }
  .tab-btn { width: 100%; justify-content: center; }
  
  .collection-summary { flex-direction: column; text-align: center; gap: 20px; padding: 25px; }
  .summary-total { font-size: 2.2rem; }
  
  .filter-group { flex: 1 1 100%; }
  
  .cards-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; }
  .tcg-image { max-width: 140px; }
  .tcg-price-box { padding: 8px; }
  .price-value { font-size: 1.1rem; }
}
</style>