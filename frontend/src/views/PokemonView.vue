<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue'

const router = useRouter()
const isAuthorized = ref(true)

const searchQuery = ref('')
const cards = ref([])
const isLoading = ref(false)
const hasSearched = ref(false)

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

const formatPrice = (price) => {
  if (!price) return 'Indisponível'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price)
}

const getLowestPrice = (card) => {
  if (!card.tcgplayer || !card.tcgplayer.prices) return null
  const prices = card.tcgplayer.prices
  
  if (prices.normal && prices.normal.low) return prices.normal.low
  if (prices.holofoil && prices.holofoil.low) return prices.holofoil.low
  if (prices.reverseHolofoil && prices.reverseHolofoil.low) return prices.reverseHolofoil.low
  if (prices['1stEditionHolofoil'] && prices['1stEditionHolofoil'].low) return prices['1stEditionHolofoil'].low
  if (prices.unlimitedHolofoil && prices.unlimitedHolofoil.low) return prices.unlimitedHolofoil.low
  
  return null
}

const searchCards = async () => {
  if (!searchQuery.value.trim()) {
    showToast('Digite o nome de um Pokémon', 'error')
    return
  }
  
  isLoading.value = true
  hasSearched.value = true
  cards.value = []
  
  try {
    const res = await fetch(`https://api.pokemontcg.io/v2/cards?q=name:"${searchQuery.value}"`)
    
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
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  
  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Mercado Pokémon TCG</h1>
        <p>Consulte o preço base de cartas em Dólares (USD)</p>
      </div>
    </div>

    <div class="search-section">
      <form @submit.prevent="searchCards" class="search-form">
        <div class="search-input-wrapper">
          <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="Ex: Charizard, Pikachu, Mewtwo..." 
            class="search-input"
          />
        </div>
        <button type="submit" class="btn-search" :disabled="isLoading">
          <span v-if="!isLoading">Pesquisar</span>
          <span v-else class="spinner"></span>
        </button>
      </form>
    </div>

    <div v-if="!isLoading && hasSearched && cards.length === 0" class="empty-state">
      <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--border-input); margin-bottom: 20px;">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <p>Não encontramos nenhuma carta com esse nome.</p>
    </div>

    <div v-if="cards.length > 0" class="cards-grid">
      <div v-for="card in cards" :key="card.id" class="tcg-card">
        <div class="tcg-image-container">
          <img :src="card.images.small" :alt="card.name" class="tcg-image" loading="lazy" />
        </div>
        <div class="tcg-info">
          <h3 class="tcg-name">{{ card.name }}</h3>
          <span class="tcg-set">{{ card.set.name }}</span>
          
          <div class="tcg-price-box">
            <span class="price-label">Menor Preço TCGPlayer</span>
            <span class="price-value">{{ formatPrice(getLowestPrice(card)) }}</span>
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

.search-section {
  background: var(--bg-card);
  padding: 30px;
  border-radius: 20px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  margin-bottom: 40px;
  transition: all 0.3s;
}

.search-form {
  display: flex;
  gap: 15px;
  width: 100%;
}

.search-input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 20px;
  color: var(--text-secondary);
}

.search-input {
  width: 100%;
  padding: 18px 20px 18px 55px;
  border: 1px solid var(--border-input);
  border-radius: 16px;
  font-size: 1.1rem;
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

.btn-search {
  padding: 0 40px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: white;
  border: none;
  border-radius: 16px;
  font-weight: 800;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 160px;
}

.btn-search:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.2);
}

.btn-search:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinner {
  width: 24px;
  height: 24px;
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
  padding: 60px 20px;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 1.2rem;
  background: var(--bg-card);
  border-radius: 20px;
  border: 1px dashed var(--border-input);
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 30px;
  margin-bottom: 40px;
}

.tcg-card {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.3s;
}

.tcg-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-lg);
  border-color: #f7b500;
}

.tcg-image-container {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.tcg-image {
  width: 100%;
  max-width: 220px;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 8px 16px rgba(0,0,0,0.15);
  transition: transform 0.3s;
}

.tcg-card:hover .tcg-image {
  transform: scale(1.05);
}

.tcg-info {
  width: 100%;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tcg-name {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--text-primary);
}

.tcg-set {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--input-bg);
  padding: 4px 12px;
  border-radius: 20px;
  display: inline-block;
  margin: 0 auto;
}

.tcg-price-box {
  margin-top: 15px;
  background: var(--positive-bg);
  padding: 15px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.price-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 800;
  color: #059669;
  letter-spacing: 0.5px;
}

.price-value {
  font-size: 1.5rem;
  font-weight: 900;
  color: #059669;
}

@media (max-width: 768px) {
  .search-form {
    flex-direction: column;
  }
  
  .btn-search {
    padding: 18px;
    width: 100%;
  }
  
  .cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 20px;
  }
}
</style>