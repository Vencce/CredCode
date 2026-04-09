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

const goals = ref([])

const showModal = ref(false)
const showAddFundsModal = ref(false)
const showDeleteModal = ref(false)
const editingId = ref(null)
const itemToDelete = ref(null)
const selectedGoal = ref(null)

const form = reactive({
  title: '',
  targetAmount: '',
  deadline: ''
})

const fundsForm = reactive({
  amount: ''
})

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

const fetchWithAuth = async (url, options = {}) => {
  let token = localStorage.getItem('access_token')
  let headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  }
  
  let response = await fetch(url, { ...options, headers })
  
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      try {
        const refreshResponse = await fetch('https://credcode-backend.onrender.com/api/auth/refresh/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: refreshToken })
        })
        
        if (refreshResponse.ok) {
          const data = await refreshResponse.json()
          localStorage.setItem('access_token', data.access)
          headers['Authorization'] = `Bearer ${data.access}`
          response = await fetch(url, { ...options, headers })
        } else {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('has_profile')
          router.push('/')
        }
      } catch (e) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('has_profile')
        router.push('/')
      }
    } else {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('has_profile')
      router.push('/')
    }
  }
  return response
}

const loadData = async () => {
  try {
    const goalsRes = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/goals/')
    if (goalsRes.ok) {
      const data = await goalsRes.json()
      goals.value = data.map(g => {
        const saved = parseFloat(g.saved_amount)
        const target = parseFloat(g.target_amount)
        let percentage = (saved / target) * 100
        if (percentage > 100) percentage = 100
        
        return {
          ...g,
          saved_amount: saved,
          target_amount: target,
          percentage: percentage
        }
      })
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
    loadData()
  }
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

const openModal = (item = null) => {
  if (item) {
    editingId.value = item.id
    form.title = item.title
    form.targetAmount = item.target_amount
    form.deadline = item.deadline ? item.deadline : ''
  } else {
    editingId.value = null
    form.title = ''
    form.targetAmount = ''
    form.deadline = ''
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingId.value = null
}

const openAddFundsModal = (item) => {
  selectedGoal.value = item
  fundsForm.amount = ''
  showAddFundsModal.value = true
}

const closeAddFundsModal = () => {
  showAddFundsModal.value = false
  selectedGoal.value = null
}

const saveGoal = async () => {
  if (!form.title || !form.targetAmount) {
    showToast('Preencha os campos obrigatórios.', 'error')
    return
  }

  const payload = {
    title: form.title,
    target_amount: parseFloat(form.targetAmount),
    deadline: form.deadline ? form.deadline : null
  }

  if (!editingId.value) {
    payload.saved_amount = 0
  }

  try {
    const url = editingId.value 
      ? `https://credcode-backend.onrender.com/api/finances/goals/${editingId.value}/`
      : 'https://credcode-backend.onrender.com/api/finances/goals/'
      
    const method = editingId.value ? 'PATCH' : 'POST'

    const response = await fetchWithAuth(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (response.ok) {
      showToast(editingId.value ? 'Meta atualizada!' : 'Meta criada com sucesso!', 'success')
      closeModal()
      loadData()
    } else {
      showToast('Erro ao salvar a meta.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  }
}

const addFunds = async () => {
  if (!fundsForm.amount || parseFloat(fundsForm.amount) <= 0) {
    showToast('Insira um valor válido.', 'error')
    return
  }

  const newSavedAmount = selectedGoal.value.saved_amount + parseFloat(fundsForm.amount)

  const payload = {
    saved_amount: newSavedAmount
  }

  try {
    const response = await fetchWithAuth(`https://credcode-backend.onrender.com/api/finances/goals/${selectedGoal.value.id}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (response.ok) {
      showToast('Depósito registado com sucesso!', 'success')
      closeAddFundsModal()
      loadData()
    } else {
      showToast('Erro ao adicionar fundos.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  }
}

const confirmDelete = (id) => {
  itemToDelete.value = id
  showDeleteModal.value = true
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  itemToDelete.value = null
}

const executeDelete = async () => {
  if (!itemToDelete.value) return

  try {
    const response = await fetchWithAuth(`https://credcode-backend.onrender.com/api/finances/goals/${itemToDelete.value}/`, {
      method: 'DELETE'
    })

    if (response.ok) {
      showToast('Meta excluída com sucesso!', 'success')
      loadData()
    } else {
      showToast('Erro ao excluir meta.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  } finally {
    closeDeleteModal()
  }
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />

  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Metas de Poupança</h1>
        <p>Acompanhe os seus objetivos e sonhos financeiros</p>
      </div>
      <div class="header-actions">
        <button @click="openModal()" class="action-btn btn-primary">
          <span class="btn-icon">+</span> Nova Meta
        </button>
      </div>
    </div>

    <div v-if="goals.length === 0" class="empty-state-container">
      <div class="empty-icon">🎯</div>
      <h3>Sem metas definidas</h3>
      <p>Cria a tua primeira meta de poupança para começar a planear o teu futuro.</p>
    </div>

    <div v-else class="goals-grid">
      <div v-for="goal in goals" :key="goal.id" class="goal-card">
        <div class="goal-header">
          <div>
            <h3 class="goal-title">{{ goal.title }}</h3>
            <span v-if="goal.deadline" class="goal-deadline">Data limite: {{ goal.deadline.split('-').reverse().join('/') }}</span>
          </div>
          <div class="goal-actions">
            <button @click="openModal(goal)" class="action-icon" title="Editar">✏️</button>
            <button @click="confirmDelete(goal.id)" class="action-icon delete-icon" title="Excluir">🗑️</button>
          </div>
        </div>

        <div class="goal-values">
          <div class="value-block">
            <span class="label">Guardado</span>
            <span class="amount text-positive">{{ formatCurrency(goal.saved_amount) }}</span>
          </div>
          <div class="value-block align-right">
            <span class="label">Objetivo</span>
            <span class="amount">{{ formatCurrency(goal.target_amount) }}</span>
          </div>
        </div>

        <div class="progress-container">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill fill-success" :style="{ width: goal.percentage + '%' }"></div>
          </div>
          <div class="progress-labels">
            <span class="percentage-text">{{ goal.percentage.toFixed(1) }}% concluído</span>
            <span class="remaining-text">Falta: {{ formatCurrency(goal.target_amount - goal.saved_amount > 0 ? goal.target_amount - goal.saved_amount : 0) }}</span>
          </div>
        </div>

        <div class="goal-footer">
          <button @click="openAddFundsModal(goal)" class="btn-add-funds" :disabled="goal.percentage >= 100">
            <span v-if="goal.percentage < 100">💰 Guardar Dinheiro</span>
            <span v-else>🎉 Meta Concluída!</span>
          </button>
        </div>
      </div>
    </div>

    <FooterComp />

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <div class="modal-header">
          <h2>{{ editingId ? 'Editar Meta' : 'Nova Meta' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        
        <form @submit.prevent="saveGoal" class="modal-form">
          <div class="form-group full-width">
            <label>Nome do Objetivo</label>
            <input v-model="form.title" type="text" placeholder="Ex: Viagem à Europa" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Valor Alvo (R$)</label>
              <input v-model="form.targetAmount" type="number" step="0.01" min="1" placeholder="Ex: 5000.00" required />
            </div>
            <div class="form-group">
              <label>Data Limite (Opcional)</label>
              <input v-model="form.deadline" type="date" />
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeModal">Cancelar</button>
            <button type="submit" class="btn-save btn-primary">Salvar</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showAddFundsModal" class="modal-overlay" @click.self="closeAddFundsModal">
      <div class="modal-container small-modal">
        <div class="modal-header">
          <h2>Guardar Dinheiro</h2>
          <button class="close-btn" @click="closeAddFundsModal">&times;</button>
        </div>
        
        <form @submit.prevent="addFunds" class="modal-form">
          <div class="form-group full-width">
            <label>Valor a adicionar na meta "{{ selectedGoal?.title }}" (R$)</label>
            <input v-model="fundsForm.amount" type="number" step="0.01" min="0.01" placeholder="Ex: 100.00" required />
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeAddFundsModal">Cancelar</button>
            <button type="submit" class="btn-save bg-positive">Depositar</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
      <div class="modal-container small-modal">
        <div class="modal-header">
          <h2 class="text-negative">Excluir Meta</h2>
          <button class="close-btn" @click="closeDeleteModal">&times;</button>
        </div>
        <div class="modal-body">
          <p>Tens a certeza que desejas excluir esta meta de poupança? Todo o histórico de progresso será perdido.</p>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="closeDeleteModal">Cancelar</button>
          <button type="button" class="btn-save bg-negative" @click="executeDelete">Excluir</button>
        </div>
      </div>
    </div>
  </SideLayout>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.header-titles h1 { color: var(--text-primary); font-size: 2rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.5px; transition: color 0.3s; }
.header-titles p { color: var(--text-secondary); margin: 0; font-size: 1.05rem; transition: color 0.3s; }
.header-actions { display: flex; gap: 15px; }
.action-btn { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 14px 24px; border-radius: 14px; font-weight: 700; font-size: 1rem; cursor: pointer; border: none; transition: all 0.3s; color: white; }
.btn-primary { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.3); color: white; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 15px 25px -5px rgba(15, 23, 42, 0.4); }
.btn-icon { font-size: 1.3rem; font-weight: 900; line-height: 1; }

.empty-state-container { text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: 20px; border: 1px dashed var(--border-color); margin-top: 20px; }
.empty-icon { font-size: 3rem; margin-bottom: 15px; }
.empty-state-container h3 { color: var(--text-primary); font-size: 1.4rem; margin: 0 0 10px 0; }
.empty-state-container p { color: var(--text-secondary); margin: 0; font-size: 1rem; }

.goals-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; margin-bottom: 40px; }
.goal-card { background: var(--bg-card); border-radius: 20px; padding: 25px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; gap: 20px; }
.goal-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }

.goal-header { display: flex; justify-content: space-between; align-items: flex-start; }
.goal-title { font-size: 1.2rem; font-weight: 800; color: var(--text-primary); margin: 0 0 4px 0; }
.goal-deadline { font-size: 0.85rem; color: var(--text-secondary); font-weight: 500; }
.goal-actions { display: flex; gap: 8px; }
.action-icon { background: var(--input-bg); border: 1px solid var(--border-input); border-radius: 8px; padding: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; font-size: 0.9rem; }
.action-icon:hover { background: var(--border-color); transform: translateY(-2px); }
.delete-icon:hover { background: var(--negative-bg); border-color: #fecaca; }

.goal-values { display: flex; justify-content: space-between; align-items: flex-end; }
.value-block { display: flex; flex-direction: column; gap: 4px; }
.align-right { text-align: right; }
.label { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
.amount { font-size: 1.4rem; font-weight: 800; color: var(--text-primary); }
.text-positive { color: #10b981 !important; }

.progress-container { display: flex; flex-direction: column; gap: 8px; margin-top: 5px; }
.progress-bar-bg { width: 100%; height: 10px; background-color: var(--border-color); border-radius: 5px; overflow: hidden; }
.progress-bar-fill { height: 100%; border-radius: 5px; transition: width 0.5s ease; }
.fill-success { background: linear-gradient(90deg, #34d399 0%, #10b981 100%); }

.progress-labels { display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; }
.percentage-text { color: var(--text-secondary); }
.remaining-text { color: var(--text-primary); }

.goal-footer { margin-top: 10px; }
.btn-add-funds { width: 100%; padding: 12px; background: var(--input-bg); border: 1px solid var(--border-input); border-radius: 12px; font-weight: 700; font-size: 0.95rem; color: var(--text-primary); cursor: pointer; transition: all 0.2s; }
.btn-add-funds:hover:not(:disabled) { background: #f7b500; color: #0f172a; border-color: #f7b500; }
.btn-add-funds:disabled { opacity: 0.6; cursor: not-allowed; background: var(--positive-bg); color: #10b981; border-color: transparent; }

.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-container { background: var(--bg-card); width: 100%; max-width: 480px; border-radius: 24px; box-shadow: var(--shadow-lg); border: 1px solid var(--border-color); padding: 35px; animation: modalSlideIn 0.3s ease-out; transition: background-color 0.3s, border-color 0.3s; }
.small-modal { max-width: 400px; }
@keyframes modalSlideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.modal-header h2 { margin: 0; color: var(--text-primary); font-size: 1.5rem; font-weight: 800; }
.close-btn { background: var(--bg-main); border: none; width: 36px; height: 36px; border-radius: 50%; font-size: 1.5rem; color: var(--text-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.close-btn:hover { background: var(--border-color); color: var(--text-primary); }

.modal-form { display: flex; flex-direction: column; gap: 20px; }
.form-row { display: flex; gap: 20px; }
.form-group { display: flex; flex-direction: column; gap: 10px; flex: 1; }
.full-width { width: 100%; }
.form-group label { font-size: 0.95rem; font-weight: 600; color: var(--text-secondary); }
.form-group input { width: 100%; box-sizing: border-box; padding: 16px; border: 1px solid var(--border-input); border-radius: 12px; font-size: 1rem; outline: none; background-color: var(--input-bg); color: var(--text-primary); transition: all 0.3s; }
.form-group input:focus { border-color: #f7b500; background-color: var(--bg-card); box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1); }

.modal-actions { display: flex; gap: 15px; margin-top: 15px; }
.btn-cancel { flex: 1; padding: 16px; background-color: var(--bg-main); color: var(--text-secondary); border: 1px solid var(--border-color); border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: all 0.2s; }
.btn-cancel:hover { background: var(--border-color); color: var(--text-primary); }
.btn-save { flex: 1; padding: 16px; color: white; border: none; border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.2s; }
.btn-save:hover { transform: translateY(-2px); }
.bg-negative { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3); }
.bg-positive { background: linear-gradient(135deg, #10b981 0%, #059669 100%); box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3); }

.text-negative { color: #dc2626 !important; }
.modal-body p { color: var(--text-secondary); font-size: 1.05rem; line-height: 1.5; margin-bottom: 25px; }

@media (max-width: 768px) { .page-header { flex-direction: column; align-items: flex-start; gap: 15px; } .header-actions { width: 100%; } .action-btn { width: 100%; } .form-row { flex-direction: column; } }
</style>