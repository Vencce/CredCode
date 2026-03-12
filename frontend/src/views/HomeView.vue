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
        <h1>Dashboard Financeiro</h1>
        <p>Acompanhe e gerencie seu patrimônio</p>
      </div>
    </div>

    <div class="main-balance-container">
      <div class="balance-card-primary">
        <div class="balance-info">
          <h3>Saldo Atual</h3>
          <p class="amount-huge">{{ formatCurrency(userData.balance + userData.income - userData.expenses) }}</p>
        </div>
        <div class="balance-decoration">
          <div class="circle circle-1"></div>
          <div class="circle circle-2"></div>
        </div>
      </div>
    </div>
    
    <section class="summary-cards">
      <div class="card income-card">
        <div class="card-icon-wrapper positive-bg">
          <span class="card-icon">↗</span>
        </div>
        <div class="card-data">
          <h3>Entradas do Mês</h3>
          <p class="amount positive">{{ formatCurrency(userData.income) }}</p>
        </div>
      </div>
      <div class="card expense-card">
        <div class="card-icon-wrapper negative-bg">
          <span class="card-icon">↘</span>
        </div>
        <div class="card-data">
          <h3>Saídas do Mês</h3>
          <p class="amount negative">{{ formatCurrency(userData.expenses) }}</p>
        </div>
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
      <div class="section-title-wrapper">
        <h2>Transações Recentes</h2>
      </div>
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
              <td class="td-date">{{ item.date }}</td>
              <td class="fw-600 td-desc">{{ item.description }}</td>
              <td>
                <span :class="['type-badge', item.type]">
                  {{ item.type === 'income' ? 'Entrada' : 'Saída' }}
                </span>
              </td>
              <td :class="['align-right fw-700', item.type === 'income' ? 'text-positive' : 'text-negative']">
                {{ item.type === 'income' ? '+' : '-' }} {{ formatCurrency(Math.abs(item.amount)) }}
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
  margin-bottom: 25px;
}

.header-greeting h1 {
  color: #0f172a;
  font-size: 2rem;
  font-weight: 800;
  margin: 0 0 4px 0;
  letter-spacing: -0.5px;
}

.header-greeting p {
  color: #64748b;
  margin: 0;
  font-size: 1.05rem;
}

.main-balance-container {
  margin-bottom: 30px;
}

.balance-card-primary {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: white;
  padding: 45px 40px;
  border-radius: 24px;
  box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.2), 0 8px 10px -6px rgba(15, 23, 42, 0.1);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.balance-info {
  position: relative;
  z-index: 2;
}

.balance-card-primary h3 {
  color: #94a3b8;
  font-size: 1.1rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 12px 0;
}

.amount-huge {
  font-size: 3.5rem;
  font-weight: 900;
  margin: 0;
  color: #f7b500;
  letter-spacing: -1.5px;
  text-shadow: 0 2px 10px rgba(247, 181, 0, 0.2);
}

.balance-decoration {
  position: absolute;
  right: 0;
  top: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  right: -50px;
}

.circle-2 {
  width: 200px;
  height: 200px;
  bottom: -80px;
  right: 150px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 25px;
  margin-bottom: 35px;
}

.card {
  background: white;
  padding: 25px 30px;
  border-radius: 20px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04), 0 4px 6px -4px rgba(0, 0, 0, 0.02);
  border: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
}

.card-icon-wrapper {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.positive-bg {
  background-color: #ecfdf5;
  color: #10b981;
}

.negative-bg {
  background-color: #fef2f2;
  color: #ef4444;
}

.card-icon {
  font-size: 1.8rem;
  font-weight: 900;
}

.card-data h3 {
  color: #64748b;
  font-size: 0.95rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 8px 0;
}

.amount {
  font-size: 1.8rem;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.5px;
}

.positive {
  color: #059669;
}

.negative {
  color: #dc2626;
}

.action-panel {
  display: flex;
  gap: 20px;
  margin-bottom: 45px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 18px 35px;
  border-radius: 16px;
  font-weight: 700;
  font-size: 1.05rem;
  cursor: pointer;
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex: 1;
  max-width: 280px;
}

.btn-income {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
}

.btn-income:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 25px -5px rgba(16, 185, 129, 0.4);
}

.btn-expense {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3);
}

.btn-expense:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 25px -5px rgba(239, 68, 68, 0.4);
}

.btn-icon {
  font-size: 1.4rem;
  font-weight: 900;
}

.section-title-wrapper {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f1f5f9;
}

.recent-transactions h2 {
  color: #0f172a;
  font-size: 1.4rem;
  font-weight: 800;
  margin: 0;
}

.table-container {
  background: white;
  border-radius: 20px;
  padding: 10px 25px 25px 25px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.02), 0 4px 6px -4px rgba(0, 0, 0, 0.01);
  border: 1px solid #f1f5f9;
  overflow-x: auto;
}

.transaction-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 700px;
}

.transaction-table th, .transaction-table td {
  padding: 18px 15px;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
}

.transaction-table th {
  color: #64748b;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-top: 25px;
}

.transaction-table td {
  color: #334155;
  font-size: 1rem;
}

.transaction-table tr:last-child td {
  border-bottom: none;
}

.transaction-table tr {
  transition: background-color 0.2s;
}

.transaction-table tr:hover td {
  background-color: #f8fafc;
}

.td-date {
  color: #64748b !important;
  font-size: 0.95rem !important;
}

.td-desc {
  color: #0f172a !important;
}

.empty-state {
  text-align: center !important;
  padding: 50px !important;
  color: #94a3b8 !important;
  font-weight: 500;
}

.align-right { text-align: right !important; }
.fw-600 { font-weight: 600; }
.fw-700 { font-weight: 700; }
.text-positive { color: #059669 !important; }
.text-negative { color: #dc2626 !important; }

.type-badge {
  padding: 8px 14px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.type-badge.income {
  background-color: #ecfdf5;
  color: #059669;
}

.type-badge.expense {
  background-color: #fef2f2;
  color: #dc2626;
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
  max-width: 480px;
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  padding: 35px;
  transform: translateY(0);
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
  margin-bottom: 30px;
}

.modal-header h2 {
  margin: 0;
  color: #0f172a;
  font-size: 1.5rem;
  font-weight: 800;
}

.close-btn {
  background: #f1f5f9;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 1.2rem;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: flex;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.form-group label {
  font-size: 0.95rem;
  font-weight: 600;
  color: #475569;
}

.form-group input, .form-group select {
  padding: 16px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  font-size: 1rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
  background-color: #f8fafc;
  color: #0f172a;
}

.form-group input:focus, .form-group select:focus {
  border-color: #f7b500;
  background-color: white;
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.modal-actions {
  display: flex;
  gap: 15px;
  margin-top: 25px;
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

.btn-cancel:hover {
  background-color: #e2e8f0;
}

.btn-save {
  flex: 1;
  padding: 16px;
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-save:hover {
  transform: translateY(-2px);
}

.bg-positive { 
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
}
.bg-negative { 
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3);
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .balance-card-primary {
    padding: 35px 25px;
  }

  .amount-huge {
    font-size: 2.5rem;
  }
  
  .action-panel {
    flex-direction: column;
  }
  
  .action-btn {
    max-width: 100%;
  }
  
  .form-row {
    flex-direction: column;
    gap: 20px;
  }
}
</style>