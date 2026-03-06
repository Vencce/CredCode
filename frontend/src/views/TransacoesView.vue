<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue' // Adicionado o Footer igual na Home

const router = useRouter()
const isAuthorized = ref(false)

const toast = reactive({
  show: false,
  message: '',
  type: 'error'
})

const transactions = ref([])
const defaultWalletId = ref(null)

// Controle dos Modais (Mesma lógica da Home)
const showModal = ref(false)
const modalType = ref('expense')

const predefinedCategories = {
  income: ['Salário', 'Investimentos', 'Vendas', 'Serviços', 'Outros'],
  expense: ['Alimentação', 'Transporte', 'Moradia', 'Contas', 'Saúde', 'Lazer', 'Outros']
}

const form = reactive({
  description: '',
  amount: '',
  date: new Date().toISOString().split('T')[0],
  category: ''
})

const filters = reactive({
  search: '',
  type: 'all'
})

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

// 🚀 BUSCA OS DADOS REAIS DO BACKEND
const loadData = async (token) => {
  try {
    // 1. Pegar a carteira para sabermos onde salvar novos gastos
    const walletRes = await fetch('http://localhost:8000/api/finances/wallets/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (walletRes.ok) {
      const wallets = await walletRes.json()
      if (wallets.length > 0) defaultWalletId.value = wallets[0].id
    }

    // 2. Pegar todas as transações (Expenses)
    const expensesRes = await fetch('http://localhost:8000/api/finances/expenses/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (expensesRes.ok) {
      const expenses = await expensesRes.json()

      transactions.value = expenses.map(item => {
        const val = parseFloat(item.amount || item.value || 0)
        const dateVal = item.date || item.created_at || ''
        const dateParts = dateVal.split('-')
        const formattedDate = dateParts.length === 3 ? `${dateParts[2].substring(0, 2)}/${dateParts[1]}/${dateParts[0]}` : dateVal

        // Truque Mágico: Extrair a categoria se estiver no formato "[Categoria] Descrição" da Home
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
          date: formattedDate
        }
      }).reverse() // O .reverse() mostra os mais recentes primeiro
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
    loadData(token)
  }
})

// ==========================================
// 🧠 LÓGICA DE CÁLCULO E FILTROS
// ==========================================
const filteredTransactions = computed(() => {
  return transactions.value.filter(t => {
    const searchString = filters.search.toLowerCase()
    const matchesSearch = t.description.toLowerCase().includes(searchString) ||
      t.category.toLowerCase().includes(searchString)
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

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}

// ==========================================
// ➕ LÓGICA DO MODAL PARA ADICIONAR
// ==========================================
const currentCategories = computed(() => {
  return modalType.value === 'income' ? predefinedCategories.income : predefinedCategories.expense
})

const openModal = (type) => {
  modalType.value = type
  form.description = ''
  form.amount = ''
  form.category = ''
  form.date = new Date().toISOString().split('T')[0]
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

  if (!defaultWalletId.value) {
    showToast('Carteira não encontrada. Recarregue a página.', 'error')
    return
  }

  const token = localStorage.getItem('access_token')
  let finalAmount = parseFloat(form.amount)

  if (modalType.value === 'expense') {
    finalAmount = -Math.abs(finalAmount)
  } else {
    finalAmount = Math.abs(finalAmount)
  }

  const payload = {
    wallet: defaultWalletId.value,
    description: `[${form.category}] ${form.description}`,
    amount: finalAmount,
    date: form.date
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
      showToast('Transação registrada com sucesso!', 'success')
      closeModal()
      loadData(token) // Atualiza a tabela com o novo dado
    } else {
      showToast('Erro ao salvar os dados da transação.', 'error')
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
        <h1>Transações</h1>
        <p>Acompanhe e filtre todas as suas movimentações</p>
      </div>
      <div class="header-actions">
        <button @click="openModal('income')" class="btn-action btn-income">+ Entrada</button>
        <button @click="openModal('expense')" class="btn-action btn-expense">- Saída</button>
      </div>
    </div>

    <div class="filters-section">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" v-model="filters.search" placeholder="Buscar por descrição ou categoria...">
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
        <span class="summary-label">Balanço (Filtro)</span>
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
          </tr>
        </thead>
        <tbody>
          <tr v-if="filteredTransactions.length === 0">
            <td colspan="5" class="empty-state">Nenhuma transação encontrada com os filtros atuais.</td>
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
              {{ formatCurrency(Math.abs(item.amount)) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <FooterComp />

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <div class="modal-header">
          <h2>{{ modalType === 'income' ? 'Nova Entrada' : 'Novo Gasto' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
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

          <div class="form-group">
            <label>Categoria</label>
            <select v-model="form.category" required>
              <option value="" disabled>Selecione uma categoria</option>
              <option v-for="cat in currentCategories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
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

.transaction-table th,
.transaction-table td {
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

.fw-600 {
  font-weight: 600;
}

.fw-700 {
  font-weight: 700;
}

.text-positive {
  color: #10b981 !important;
}

.text-negative {
  color: #ef4444 !important;
}

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

  page-header {
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

  .transaction-table th,
  .transaction-table td {
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

  .fw-600 {
    font-weight: 600;
  }

  .fw-700 {
    font-weight: 700;
  }

  .text-positive {
    color: #10b981 !important;
  }

  .text-negative {
    color: #ef4444 !important;
  }

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

  /* MODAL STYLES */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(10, 42, 67, 0.6);
    backdrop-filter: blur(3px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .modal-container {
    background: white;
    width: 100%;
    max-width: 450px;
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
    padding: 30px;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 25px;
  }

  .modal-header h2 {
    margin: 0;
    color: #0a2a43;
    font-size: 1.4rem;
    font-weight: 800;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.8rem;
    color: #64748b;
    cursor: pointer;
    line-height: 1;
    transition: color 0.2s;
  }

  .close-btn:hover {
    color: #ef4444;
  }

  .modal-form {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }

  .form-row {
    display: flex;
    gap: 15px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
  }

  .form-group label {
    font-size: 0.9rem;
    font-weight: 600;
    color: #334155;
  }

  .form-group input,
  .form-group select {
    padding: 14px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.95rem;
    font-family: 'Inter', sans-serif;
    outline: none;
    transition: border-color 0.3s;
  }

  .form-group input:focus,
  .form-group select:focus {
    border-color: #f7b500;
  }

  .modal-actions {
    display: flex;
    gap: 15px;
    margin-top: 20px;
  }

  .btn-cancel {
    flex: 1;
    padding: 14px;
    background-color: #f1f5f9;
    color: #64748b;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .btn-cancel:hover {
    background-color: #e2e8f0;
  }

  .btn-save {
    flex: 1;
    padding: 14px;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.2s, opacity 0.2s;
  }

  .btn-save:hover {
    transform: translateY(-2px);
    opacity: 0.9;
  }

  .bg-positive {
    background-color: #10b981;
  }

  .bg-negative {
    background-color: #ef4444;
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

    .form-row {
      flex-direction: column;
    }
  }
}
</style>