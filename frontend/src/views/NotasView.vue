<script setup>
import { ref, reactive, onMounted } from 'vue'
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

const notes = ref([])
const showModal = ref(false)
const showDeleteModal = ref(false)
const editingId = ref(null)
const itemToDelete = ref(null)

const form = reactive({
  title: '',
  content: ''
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

const loadNotes = async () => {
  try {
    const res = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/notes/')
    if (res.ok) {
      notes.value = await res.json()
    } else {
      showToast('Erro ao carregar as anotações.', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão.', 'error')
  }
}

onMounted(() => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    router.push('/')
  } else {
    isAuthorized.value = true
    loadNotes()
  }
})

const openModal = (note = null) => {
  if (note) {
    editingId.value = note.id
    form.title = note.title
    form.content = note.content
  } else {
    editingId.value = null
    form.title = ''
    form.content = ''
  }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingId.value = null
}

const saveNote = async () => {
  if (!form.title.trim()) {
    showToast('O título é obrigatório.', 'error')
    return
  }

  const payload = {
    title: form.title,
    content: form.content
  }

  const url = editingId.value 
    ? `https://credcode-backend.onrender.com/api/finances/notes/${editingId.value}/`
    : 'https://credcode-backend.onrender.com/api/finances/notes/'
    
  const method = editingId.value ? 'PUT' : 'POST'

  try {
    const res = await fetchWithAuth(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (res.ok) {
      showToast(editingId.value ? 'Nota atualizada!' : 'Nota criada!', 'success')
      closeModal()
      loadNotes()
    } else {
      showToast('Erro ao salvar a anotação.', 'error')
    }
  } catch (e) {
    showToast('Erro de conexão.', 'error')
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
    const res = await fetchWithAuth(`https://credcode-backend.onrender.com/api/finances/notes/${itemToDelete.value}/`, {
      method: 'DELETE'
    })

    if (res.ok) {
      showToast('Anotação excluída.', 'success')
      loadNotes()
    } else {
      showToast('Erro ao excluir anotação.', 'error')
    }
  } catch (e) {
    showToast('Erro de conexão.', 'error')
  } finally {
    closeDeleteModal()
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('pt-BR', { 
    day: '2-digit', 
    month: '2-digit', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  
  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Bloco de Notas</h1>
        <p>Suas ideias, estratégias e lembretes do sistema</p>
      </div>
      <div class="header-actions">
        <button @click="openModal()" class="action-btn btn-primary">
          <span class="btn-icon">+</span> Nova Nota
        </button>
      </div>
    </div>

    <div v-if="notes.length === 0" class="empty-state-container">
      <div class="empty-icon">📝</div>
      <h3>Sua mesa está limpa</h3>
      <p>Nenhuma anotação criada ainda. Comece a registrar suas ideias!</p>
    </div>

    <div v-else class="notes-grid">
      <div v-for="note in notes" :key="note.id" class="note-card">
        <div class="note-header">
          <h3 class="note-title">{{ note.title }}</h3>
          <div class="note-actions">
            <button @click="openModal(note)" class="icon-btn edit-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
            </button>
            <button @click="confirmDelete(note.id)" class="icon-btn delete-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>
        </div>
        <div class="note-body">
          <p class="note-content">{{ note.content }}</p>
        </div>
        <div class="note-footer">
          <span class="note-date">Atualizado em {{ formatDate(note.updated_at) }}</span>
        </div>
      </div>
    </div>

    <FooterComp />

    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container large-modal">
        <div class="modal-header">
          <h2>{{ editingId ? 'Editar Nota' : 'Nova Nota' }}</h2>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        
        <form @submit.prevent="saveNote" class="modal-form">
          <div class="form-group full-width">
            <label>Título</label>
            <input v-model="form.title" type="text" placeholder="Ex: Metas para 2027" required />
          </div>

          <div class="form-group full-width">
            <label>Anotação</label>
            <textarea v-model="form.content" placeholder="Escreva suas ideias aqui..." rows="10" class="note-textarea"></textarea>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeModal">Cancelar</button>
            <button type="submit" class="btn-save btn-primary">
              Salvar Nota
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
      <div class="modal-container delete-modal">
        <div class="modal-header">
          <h2 class="text-negative">Excluir Nota</h2>
          <button class="close-btn" @click="closeDeleteModal">&times;</button>
        </div>
        <div class="modal-body">
          <p>Tem certeza que deseja excluir esta anotação? Esta ação não pode ser desfeita.</p>
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
[data-theme="dark"] .btn-primary { background: linear-gradient(135deg, #f7b500 0%, #e6a800 100%); color: #0f172a; }
.btn-icon { font-size: 1.3rem; font-weight: 900; line-height: 1; }

.empty-state-container { text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: 20px; border: 1px dashed var(--border-color); margin-top: 20px; }
.empty-icon { font-size: 3rem; margin-bottom: 15px; }
.empty-state-container h3 { color: var(--text-primary); font-size: 1.4rem; margin: 0 0 10px 0; }
.empty-state-container p { color: var(--text-secondary); margin: 0; font-size: 1rem; }

.notes-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; margin-bottom: 40px; align-items: start; }

.note-card { background: var(--bg-card); border-radius: 16px; padding: 20px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s; position: relative; overflow: hidden; }
.note-card::before { content: ''; position: absolute; top: 0; left: 0; width: 6px; height: 100%; background: linear-gradient(180deg, #f7b500 0%, #e6a800 100%); }
.note-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }

.note-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; gap: 15px; }
.note-title { color: var(--text-primary); font-size: 1.15rem; font-weight: 800; margin: 0; line-height: 1.3; }

.note-actions { display: flex; gap: 8px; }
.icon-btn { background: var(--input-bg); border: 1px solid var(--border-input); border-radius: 8px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text-secondary); transition: all 0.2s; }
.edit-btn:hover { background: var(--bg-main); color: var(--text-primary); border-color: var(--text-primary); }
.delete-btn:hover { background: var(--negative-bg); color: #dc2626; border-color: #fecaca; }

.note-body { margin-bottom: 20px; }
.note-content { color: var(--text-secondary); font-size: 0.95rem; line-height: 1.6; margin: 0; white-space: pre-wrap; display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; }

.note-footer { display: flex; justify-content: flex-end; border-top: 1px solid var(--border-input); padding-top: 12px; }
.note-date { font-size: 0.75rem; color: var(--text-secondary); font-weight: 600; text-transform: uppercase; }

.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-container { background: var(--bg-card); width: 100%; max-width: 480px; border-radius: 24px; box-shadow: var(--shadow-lg); border: 1px solid var(--border-color); padding: 35px; animation: modalSlideIn 0.3s ease-out; transition: background-color 0.3s, border-color 0.3s; }
.large-modal { max-width: 600px; }
.delete-modal { max-width: 400px; }
@keyframes modalSlideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.modal-header h2 { margin: 0; color: var(--text-primary); font-size: 1.5rem; font-weight: 800; transition: color 0.3s; }
.text-negative { color: #dc2626 !important; }

.close-btn { background: var(--bg-main); border: none; width: 36px; height: 36px; border-radius: 50%; font-size: 1.5rem; color: var(--text-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center; line-height: 1; transition: all 0.2s; }
.close-btn:hover { background: var(--border-color); color: var(--text-primary); }

.modal-body { color: var(--text-secondary); font-size: 1.05rem; line-height: 1.5; margin-bottom: 25px; }
.modal-form { display: flex; flex-direction: column; gap: 20px; }
.form-group { display: flex; flex-direction: column; gap: 10px; width: 100%; }
.form-group label { font-size: 0.95rem; font-weight: 600; color: var(--text-secondary); }

.form-group input, .note-textarea { width: 100%; box-sizing: border-box; padding: 16px; border: 1px solid var(--border-input); border-radius: 12px; font-size: 1rem; font-family: 'Inter', sans-serif; outline: none; background-color: var(--input-bg); color: var(--text-primary); transition: all 0.3s; }
.note-textarea { resize: vertical; min-height: 150px; line-height: 1.5; }
.form-group input:focus, .note-textarea:focus { border-color: #f7b500; background-color: var(--bg-card); box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1); }

.modal-actions { display: flex; gap: 15px; margin-top: 15px; }
.btn-cancel { flex: 1; padding: 16px; background-color: var(--bg-main); color: var(--text-secondary); border: 1px solid var(--border-color); border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: all 0.2s; }
.btn-cancel:hover { background: var(--border-color); color: var(--text-primary); }
.btn-save { flex: 1; padding: 16px; color: white; border: none; border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.2s; }
.btn-save:hover { transform: translateY(-2px); }
.bg-negative { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3); }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 15px; }
  .header-actions { width: 100%; }
  .action-btn { width: 100%; }
  .modal-container { padding: 25px 20px; }
}
</style>