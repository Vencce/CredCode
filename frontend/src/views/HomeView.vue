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
  name: 'Usuário',
  balance: 0,
  income: 0,
  expenses: 0
})

const recentTransactions = ref([])
const defaultWalletId = ref(null)

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

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

const loadData = async (token) => {
  try {
    let baseBalance = 0
    
    const profileRes = await fetch('http://localhost:8000/api/finances/profile/', {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    if (profileRes.ok) {
      const data = await profileRes.json()
      if (data.full_name) userData.name = data.full_name
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
      } else {
        const createWalletRes = await fetch('http://localhost:8000/api/finances/wallets/', {
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name: 'Carteira Principal', balance: baseBalance })
        })
        if (createWalletRes.ok) {
          const newWallet = await createWalletRes.json()
          defaultWalletId.value = newWallet.id
        }
      }
    }

    userData.balance = baseBalance

    const expensesRes = await fetch('http://localhost:8000/api/finances/expenses/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })

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

        return {
          id: item.id,
          description: item.description || item.title || item.name || 'Sem descrição',
          amount: val,
          type: val >= 0 ? 'income' : 'expense',
          date: formattedDate
        }
      }).reverse()

      userData.income = totalInc
      userData.expenses = totalExp
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

const handleLogout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('has_profile')
  router.push('/')
}

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
      loadData(token)
    } else {
      showToast('Erro ao salvar os dados da transação.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  }
}

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}

const currentCategories = computed(() => {
  return modalType.value === 'income' ? predefinedCategories.income : predefinedCategories.expense
})
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
        <p class="amount">{{ formatCurrency(userData.balance + userData.income - userData.expenses) }}</p>
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
      <button @click="openModal('income')" class="action-btn btn-income">
        <span class="btn-icon">+</span> Nova Entrada
      </button>
      <button @click="openModal('expense')" class="action-btn btn-expense">
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
            <tr v-if="recentTransactions.length === 0">
              <td colspan="4" class="empty-state">Nenhuma transação registrada.</td>
            </tr>
            <tr v-for="item in recentTransactions" :key="item.id">
              <td>{{ item.date }}</td>
              <td class="fw-600">{{ item.description }}</td>
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
    </section>

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
  overflow-x: auto;
}

.transaction-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px;
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

.transaction-table th:first-child { border-top-left-radius: 8px; border-bottom-left-radius: 8px; }
.transaction-table th:last-child { border-top-right-radius: 8px; border-bottom-right-radius: 8px; }

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
  padding: 30px !important;
  color: #94a3b8 !important;
}

.align-right { text-align: right !important; }
.fw-600 { font-weight: 600; }
.fw-700 { font-weight: 700; }
.text-positive { color: #10b981 !important; }
.text-negative { color: #ef4444 !important; }

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

.form-group input, .form-group select {
  padding: 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  transition: border-color 0.3s;
}

.form-group input:focus, .form-group select:focus {
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

.bg-positive { background-color: #10b981; }
.bg-negative { background-color: #ef4444; }

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
  
  .form-row {
    flex-direction: column;
  }
}
</style>