<script setup>
import { ref, onMounted, reactive } from 'vue'
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

const userData = reactive({
  name: 'Usuário',
  balance: 0,
  income: 0,
  expenses: 0
})

const recentTransactions = ref([
  { id: 1, description: 'Salário', amount: 5000, type: 'income', date: '05/03/2026' },
  { id: 2, description: 'Aluguel', amount: -1500, type: 'expense', date: '06/03/2026' },
  { id: 3, description: 'Mercado', amount: -450, type: 'expense', date: '08/03/2026' }
])

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

const loadUserProfile = async (token) => {
  try {
    const response = await fetch('http://localhost:8000/api/finances/profile/', {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.full_name) userData.name = data.full_name
      if (data.account_balance !== undefined) userData.balance = data.account_balance
    }
  } catch (error) {
    showToast('Erro ao carregar dados do perfil.', 'error')
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
    loadUserProfile(token)
  }
})

const handleLogout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('has_profile')
  router.push('/')
}

const handleAddIncome = () => {
  showToast('Módulo de entrada em desenvolvimento', 'success')
}

const handleAddExpense = () => {
  showToast('Módulo de gastos em desenvolvimento', 'error')
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  
  <SideLayout v-if="isAuthorized">
    <div class="dashboard-header">
      <div class="header-greeting">
        <h1>Olá, {{ userData.name }}</h1>
        <p>Bem-vindo ao seu Terminal Financeiro</p>
      </div>
      <button @click="handleLogout" class="btn-logout">Sair do Terminal</button>
    </div>
    
    <section class="summary-cards">
      <div class="card balance-card">
        <h3>Saldo Atual</h3>
        <p class="amount">{{ formatCurrency(userData.balance) }}</p>
      </div>
      <div class="card income-card">
        <h3>Entradas do Mês</h3>
        <p class="amount positive">{{ formatCurrency(userData.income) }}</p>
      </div>
      <div class="card expense-card">
        <h3>Saídas do Mês</h3>
        <p class="amount negative">{{ formatCurrency(userData.expenses) }}</p>
      </div>
    </section>

    <section class="action-panel">
      <button @click="handleAddIncome" class="action-btn btn-income">
        <span class="btn-icon">+</span> Nova Entrada
      </button>
      <button @click="handleAddExpense" class="action-btn btn-expense">
        <span class="btn-icon">-</span> Novo Gasto
      </button>
    </section>

    <section class="recent-transactions">
      <h2>Transações Recentes</h2>
      <div class="table-container">
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
            <tr v-for="item in recentTransactions" :key="item.id">
              <td>{{ item.date }}</td>
              <td>{{ item.description }}</td>
              <td>
                <span :class="['type-badge', item.type]">
                  {{ item.type === 'income' ? 'Entrada' : 'Saída' }}
                </span>
              </td>
              <td :class="['align-right', item.type === 'income' ? 'text-positive' : 'text-negative']">
                {{ formatCurrency(item.amount) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <footer class="app-footer">
      <p>&copy; 2026 CREDCODE. O Caminho da Lógica. Todos os direitos reservados.</p>
    </footer>
  </SideLayout>
</template>

<style scoped>
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.header-greeting h1 {
  color: #0a2a43;
  font-size: 1.8rem;
  font-weight: 800;
  margin: 0 0 5px 0;
}

.header-greeting p {
  color: #64748b;
  margin: 0;
  font-size: 1rem;
}

.btn-logout {
  background-color: #f8fafc;
  color: #0a2a43;
  border: 1px solid #e2e8f0;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-logout:hover {
  background-color: #fee2e2;
  color: #ef4444;
  border-color: #fca5a5;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

.card {
  background: white;
  padding: 25px;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
  border: 1px solid #f1f5f9;
}

.card h3 {
  color: #64748b;
  font-size: 0.95rem;
  font-weight: 600;
  text-transform: uppercase;
  margin: 0 0 15px 0;
}

.amount {
  font-size: 2rem;
  font-weight: 800;
  color: #0a2a43;
  margin: 0;
}

.positive {
  color: #10b981;
}

.negative {
  color: #ef4444;
}

.action-panel {
  display: flex;
  gap: 20px;
  margin-bottom: 40px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 30px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  border: none;
  transition: transform 0.2s, box-shadow 0.2s;
  flex: 1;
  max-width: 250px;
}

.action-btn:hover {
  transform: translateY(-2px);
}

.btn-income {
  background-color: #10b981;
  color: white;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
}

.btn-income:hover {
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.btn-expense {
  background-color: #ef4444;
  color: white;
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3);
}

.btn-expense:hover {
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

.btn-icon {
  font-size: 1.4rem;
  font-weight: 900;
}

.recent-transactions h2 {
  color: #0a2a43;
  font-size: 1.2rem;
  font-weight: 800;
  margin-bottom: 20px;
}

.table-container {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
  border: 1px solid #f1f5f9;
}

.transaction-table {
  width: 100%;
  border-collapse: collapse;
}

.transaction-table th, .transaction-table td {
  padding: 15px;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
}

.transaction-table th {
  color: #64748b;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.transaction-table td {
  color: #334155;
  font-weight: 500;
}

.transaction-table tr:last-child td {
  border-bottom: none;
}

.align-right {
  text-align: right !important;
}

.text-positive {
  color: #10b981;
  font-weight: 700 !important;
}

.text-negative {
  color: #ef4444;
  font-weight: 700 !important;
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

.app-footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
  text-align: center;
  color: #64748b;
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .action-panel {
    flex-direction: column;
  }
  
  .action-btn {
    max-width: 100%;
  }
}
</style>