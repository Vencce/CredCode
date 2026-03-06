<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'

const router = useRouter()
const isAuthorized = ref(false)

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

//* Dados de exemplo para transações - em um cenário real, esses dados viriam da API
const transactions = ref([
  { id: 1, description: 'Salário Mensal', amount: 5000, type: 'income', date: '05/03/2026', category: 'Salário' },
  { id: 2, description: 'Aluguel', amount: -1500, type: 'expense', date: '06/03/2026', category: 'Moradia' },
  { id: 3, description: 'Supermercado', amount: -450, type: 'expense', date: '08/03/2026', category: 'Alimentação' },
  { id: 4, description: 'Internet', amount: -120, type: 'expense', date: '10/03/2026', category: 'Contas' },
  { id: 5, description: 'Venda de Notebook', amount: 2500, type: 'income', date: '12/03/2026', category: 'Vendas' },
  { id: 6, description: 'Gasolina', amount: -200, type: 'expense', date: '15/03/2026', category: 'Transporte' },
  { id: 7, description: 'Jantar fora', amount: -180, type: 'expense', date: '18/03/2026', category: 'Lazer' },
  { id: 8, description: 'Rendimento Investimentos', amount: 350, type: 'income', date: '20/03/2026', category: 'Investimentos' }
])

const filters = reactive({
  search: '',
  type: 'all'
})

const filteredTransactions = computed(() => {
  return transactions.value.filter(t => {
    const matchesSearch = t.description.toLowerCase().includes(filters.search.toLowerCase()) || 
                          t.category.toLowerCase().includes(filters.search.toLowerCase())
    const matchesType = filters.type === 'all' || t.type === filters.type
    return matchesSearch && matchesType
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

onMounted(() => {
  const token = localStorage.getItem('access_token')
  
  if (!token) {
    showToast('Acesso negado. Por favor, faça login no terminal.', 'error')
    setTimeout(() => {
      router.push('/')
    }, 1500)
  } else {
    isAuthorized.value = true
  }
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

const handleAddIncome = () => {
  showToast('Módulo de entrada em desenvolvimento', 'success')
}

const handleAddExpense = () => {
  showToast('Módulo de gastos em desenvolvimento', 'error')
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
        <button @click="handleAddIncome" class="btn-action btn-income">+ Entrada</button>
        <button @click="handleAddExpense" class="btn-action btn-expense">- Saída</button>
      </div>
    </div>

    <div class="filters-section">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input 
          type="text" 
          v-model="filters.search" 
          placeholder="Buscar por descrição ou categoria..."
        >
      </div>
      <div class="filter-type">
        <select v-model="filters.type">
          <option value="all">Todas as transações</option>
          <option value="income">Apenas Entradas</option>
          <option value="expense">Apenas Saídas</option>
        </select>
      </div>
    </div>

    <div class="summary-bar">
      <div class="summary-item">
        <span class="summary-label">Entradas no período</span>
        <span class="summary-value text-positive">{{ formatCurrency(totalIncome) }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">Saídas no período</span>
        <span class="summary-value text-negative">{{ formatCurrency(totalExpense) }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">Balanço</span>
        <span :class="['summary-value', (totalIncome - totalExpense) >= 0 ? 'text-positive' : 'text-negative']">
          {{ formatCurrency(totalIncome - totalExpense) }}
        </span>
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
            <td>{{ item.date }}</td>
            <td class="fw-600">{{ item.description }}</td>
            <td>
              <span class="category-tag">{{ item.category }}</span>
            </td>
            <td>
              <span :class="['type-badge', item.type]">
                {{ item.type === 'income' ? 'Entrada' : 'Saída' }}
              </span>
            </td>
            <td :class="['align-right fw-700', item.type === 'income' ? 'text-positive' : 'text-negative']">
              {{ formatCurrency(item.amount) }}
            </td>
            <td class="align-center">
              <button class="btn-icon" title="Editar">✏️</button>
              <button class="btn-icon text-negative" title="Excluir">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
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

.header-actions {
  display: flex;
  gap: 15px;
}

.btn-action {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  border: none;
  transition: transform 0.2s, box-shadow 0.2s;
  color: white;
}

.btn-action:hover {
  transform: translateY(-2px);
}

.btn-income {
  background-color: #10b981;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
}

.btn-income:hover {
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.btn-expense {
  background-color: #ef4444;
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3);
}

.btn-expense:hover {
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

.filters-section {
  display: flex;
  gap: 20px;
  margin-bottom: 25px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
  border: 1px solid #f1f5f9;
}

.search-box {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 15px;
  color: #94a3b8;
}

.search-box input {
  width: 100%;
  padding: 12px 15px 12px 45px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.3s;
  font-family: 'Inter', sans-serif;
}

.search-box input:focus {
  border-color: #f7b500;
}

.filter-type select {
  padding: 12px 20px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  outline: none;
  background-color: white;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  color: #334155;
  min-width: 200px;
}

.filter-type select:focus {
  border-color: #f7b500;
}

.summary-bar {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.summary-item {
  flex: 1;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
  border: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.summary-label {
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: #0a2a43;
}

.transactions-container {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
  border: 1px solid #f1f5f9;
  overflow-x: auto;
}

.transaction-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.transaction-table th, .transaction-table td {
  padding: 16px 15px;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
}

.transaction-table th {
  color: #64748b;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
  background-color: #f8fafc;
}

.transaction-table th:first-child {
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
}

.transaction-table th:last-child {
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
}

.transaction-table td {
  color: #334155;
  font-size: 0.95rem;
}

.transaction-table tr:last-child td {
  border-bottom: none;
}

.transaction-table tr:hover td {
  background-color: #f8fafc;
}

.empty-state {
  text-align: center !important;
  padding: 40px !important;
  color: #94a3b8 !important;
  font-weight: 500;
}

.align-right {
  text-align: right !important;
}

.align-center {
  text-align: center !important;
}

.fw-600 { font-weight: 600; }
.fw-700 { font-weight: 700; }

.text-positive { color: #10b981 !important; }
.text-negative { color: #ef4444 !important; }

.category-tag {
  background-color: #f1f5f9;
  color: #475569;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
}

.type-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.type-badge.income {
  background-color: #d1fae5;
  color: #065f46;
}

.type-badge.expense {
  background-color: #fee2e2;
  color: #991b1b;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  font-size: 1.1rem;
  opacity: 0.6;
  transition: opacity 0.2s, transform 0.2s;
  margin: 0 5px;
}

.btn-icon:hover {
  opacity: 1;
  transform: scale(1.1);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .header-actions {
    width: 100%;
  }
  
  .btn-action {
    flex: 1;
  }
  
  .filters-section {
    flex-direction: column;
  }
  
  .summary-bar {
    flex-direction: column;
  }
}
</style>