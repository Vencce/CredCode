<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue'

const router = useRouter()
const isAuthorized = ref(false)
const loans = ref([])

const toast = reactive({ show: false, message: '', type: 'error' })

const showModal = ref(false)
const showDeleteModal = ref(false)
const editingId = ref(null)
const itemToDelete = ref(null)

const form = reactive({
  debtor_name: '',
  amount: '',
  due_date: new Date().toISOString().split('T')[0],
  description: ''
})

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

const fetchWithAuth = async (url, options = {}) => {
  let token = localStorage.getItem('access_token')
  let headers = { ...options.headers, 'Authorization': `Bearer ${token}` }
  let response = await fetch(url, { ...options, headers })
  if (response.status === 401) { router.push('/') }
  return response
}

const loadData = async () => {
  try {
    const res = await fetchWithAuth('http://localhost:8000/api/finances/loans/')
    if (res.ok) {
      loans.value = await res.json()
    }
  } catch (error) { showToast('Erro ao carregar devedores.', 'error') }
}

onMounted(() => {
  const token = localStorage.getItem('access_token')
  if (!token) router.push('/'); else { isAuthorized.value = true; loadData() }
})

const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)

const totalToReceive = computed(() => {
  return loans.value.filter(l => !l.is_paid).reduce((acc, curr) => acc + parseFloat(curr.amount), 0)
})

const openModal = (item = null) => {
  if (item) {
    editingId.value = item.id
    form.debtor_name = item.debtor_name
    form.amount = item.amount
    form.due_date = item.due_date
    form.description = item.description
  } else {
    editingId.value = null
    form.debtor_name = ''; form.amount = ''; form.description = ''; form.due_date = new Date().toISOString().split('T')[0]
  }
  showModal.value = true
}

const saveLoan = async () => {
  const method = editingId.value ? 'PUT' : 'POST'
  const url = editingId.value ? `http://localhost:8000/api/finances/loans/${editingId.value}/` : 'http://localhost:8000/api/finances/loans/'
  
  const res = await fetchWithAuth(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form)
  })

  if (res.ok) {
    showToast('Registro salvo!', 'success')
    showModal.value = false
    loadData()
  }
}

const togglePaid = async (item) => {
  const res = await fetchWithAuth(`http://localhost:8000/api/finances/loans/${item.id}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_paid: !item.is_paid })
  })
  if (res.ok) loadData()
}

const executeDelete = async () => {
  const res = await fetchWithAuth(`http://localhost:8000/api/finances/loans/${itemToDelete.value}/`, { method: 'DELETE' })
  if (res.ok) { showToast('Removido!', 'success'); showDeleteModal.value = false; loadData() }
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Central de Cobrança</h1>
        <p>Controle quem te deve e os prazos de pagamento</p>
      </div>
      <button @click="openModal()" class="action-btn btn-primary">+ Novo Empréstimo</button>
    </div>

    <div class="summary-card">
      <div class="card-content">
        <h3>Total a Receber</h3>
        <p class="amount">{{ formatCurrency(totalToReceive) }}</p>
      </div>
      <div class="card-icon">💰</div>
    </div>

    <div class="loans-container">
      <div v-if="loans.length === 0" class="empty-state">Nenhum valor emprestado no momento.</div>
      <div v-else class="loans-grid">
        <div v-for="item in loans" :key="item.id" :class="['loan-card', { 'is-paid': item.is_paid }]">
          <div class="loan-header">
            <span class="debtor-name">{{ item.debtor_name }}</span>
            <span :class="['status-badge', item.is_paid ? 'paid' : 'pending']">
              {{ item.is_paid ? 'Pago' : 'Pendente' }}
            </span>
          </div>
          <div class="loan-body">
            <p class="loan-amount">{{ formatCurrency(item.amount) }}</p>
            <p class="loan-date">Vencimento: {{ item.due_date.split('-').reverse().join('/') }}</p>
            <p class="loan-desc" v-if="item.description">{{ item.description }}</p>
          </div>
          <div class="loan-actions">
            <button @click="togglePaid(item)" class="btn-check">
              {{ item.is_paid ? 'Reabrir' : 'Marcar como Pago' }}
            </button>
            <button @click="openModal(item)" class="btn-edit">✏️</button>
            <button @click="itemToDelete = item.id; showDeleteModal = true" class="btn-delete">🗑️</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-container">
        <h2>{{ editingId ? 'Editar' : 'Novo Registro' }}</h2>
        <form @submit.prevent="saveLoan" class="modal-form">
          <div class="form-group"><label>Nome do Devedor</label><input v-model="form.debtor_name" type="text" required /></div>
          <div class="form-group"><label>Valor</label><input v-model="form.amount" type="number" step="0.01" required /></div>
          <div class="form-group"><label>Data de Vencimento</label><input v-model="form.due_date" type="date" required /></div>
          <div class="form-group"><label>Observação</label><input v-model="form.description" type="text" /></div>
          <div class="modal-actions">
            <button type="button" @click="showModal = false" class="btn-cancel">Cancelar</button>
            <button type="submit" class="btn-save btn-primary">Salvar</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal-container small-modal">
        <h2>Excluir Registro?</h2>
        <div class="modal-actions">
          <button @click="showDeleteModal = false" class="btn-cancel">Não</button>
          <button @click="executeDelete" class="btn-save btn-danger">Sim, Excluir</button>
        </div>
      </div>
    </div>
    <FooterComp />
  </SideLayout>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.header-titles h1 { color: var(--text-primary); font-size: 2rem; font-weight: 800; }
.summary-card { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 30px; border-radius: 20px; color: white; display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.amount { font-size: 2.5rem; font-weight: 900; color: #f7b500; margin: 0; }
.loans-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.loan-card { background: var(--bg-card); padding: 20px; border-radius: 15px; border: 1px solid var(--border-color); transition: 0.3s; }
.loan-card.is-paid { opacity: 0.6; filter: grayscale(0.5); }
.loan-header { display: flex; justify-content: space-between; margin-bottom: 15px; }
.debtor-name { font-weight: 800; font-size: 1.1rem; color: var(--text-primary); }
.loan-amount { font-size: 1.5rem; font-weight: 800; color: #10b981; margin: 5px 0; }
.status-badge { padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
.pending { background: #fef3c7; color: #d97706; }
.paid { background: #d1fae5; color: #059669; }
.loan-actions { display: flex; gap: 10px; margin-top: 15px; }
.btn-check { flex: 1; background: var(--input-bg); border: 1px solid var(--border-input); padding: 8px; border-radius: 8px; font-weight: 700; cursor: pointer; color: var(--text-primary); }
.btn-check:hover { background: var(--border-color); }
.btn-edit, .btn-delete { background: var(--input-bg); border: 1px solid var(--border-input); padding: 8px; border-radius: 8px; cursor: pointer; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-container { background: var(--bg-card); padding: 30px; border-radius: 20px; width: 100%; max-width: 400px; }
.modal-form { display: flex; flex-direction: column; gap: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: 600; color: var(--text-secondary); }
.form-group input { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid var(--border-input); background: var(--input-bg); color: var(--text-primary); }
.modal-actions { display: flex; gap: 10px; margin-top: 20px; }
.btn-save { flex: 1; padding: 12px; border-radius: 10px; border: none; font-weight: 700; cursor: pointer; color: white; }
.btn-primary { background: #10b981; }
.btn-danger { background: #ef4444; }
.btn-cancel { flex: 1; padding: 12px; border-radius: 10px; border: 1px solid var(--border-color); background: var(--bg-main); color: var(--text-secondary); cursor: pointer; }
.action-btn { padding: 12px 20px; border-radius: 12px; border: none; font-weight: 700; cursor: pointer; color: white; background: #0f172a; }
</style>