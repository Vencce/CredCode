<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue'

const router = useRouter()
const isAuthorized = ref(false)
const activeTab = ref('profile')
const isGenerating = ref(false)

const toast = reactive({
  show: false,
  message: '',
  type: 'error'
})

const profileForm = reactive({
  fullName: ''
})

const categories = ref([])
const newCategoryForm = reactive({
  name: '',
  type: 'expense'
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
    const profRes = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/profile/')
    if (profRes.ok) {
      const data = await profRes.json()
      profileForm.fullName = data.full_name
    }

    const catRes = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/categories/')
    if (catRes.ok) {
      categories.value = await catRes.json()
    }
  } catch (e) {
    showToast('Erro ao carregar dados.', 'error')
  }
}

onMounted(() => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    router.push('/')
  } else {
    isAuthorized.value = true
    loadData()
  }
})

const saveProfile = async () => {
  if (!profileForm.fullName) {
    showToast('O nome não pode estar vazio.', 'error')
    return
  }
  
  try {
    const res = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/profile/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: profileForm.fullName })
    })
    
    if (res.ok) {
      showToast('Perfil atualizado com sucesso!', 'success')
      setTimeout(() => {
        window.location.reload()
      }, 1000)
    } else {
      showToast('Erro ao atualizar perfil.', 'error')
    }
  } catch (e) {
    showToast('Erro de conexão.', 'error')
  }
}

const addCategory = async () => {
  if (!newCategoryForm.name || !newCategoryForm.type) {
    showToast('Preencha os campos da categoria.', 'error')
    return
  }

  try {
    const res = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/categories/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newCategoryForm.name,
        type: newCategoryForm.type
      })
    })

    if (res.ok) {
      showToast('Categoria adicionada!', 'success')
      newCategoryForm.name = ''
      loadData()
    } else {
      showToast('Erro ao adicionar categoria ou categoria já existe.', 'error')
    }
  } catch (e) {
    showToast('Erro de conexão.', 'error')
  }
}

const generateEssentialCategories = async () => {
  isGenerating.value = true
  const essentials = [
    { name: 'Alimentação', type: 'expense' },
    { name: 'Moradia', type: 'expense' },
    { name: 'Transporte', type: 'expense' },
    { name: 'Saúde', type: 'expense' },
    { name: 'Despesas Fixas', type: 'expense' },
    { name: 'Lazer', type: 'expense' },
    { name: 'Educação', type: 'expense' },
    { name: 'Outros', type: 'expense' },
    { name: 'Salário', type: 'income' },
    { name: 'Transferência', type: 'income' }
  ]

  let addedCount = 0

  for (const cat of essentials) {
    const exists = categories.value.find(c => c.name.toLowerCase() === cat.name.toLowerCase() && c.type === cat.type)
    if (!exists) {
      try {
        const res = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/categories/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cat)
        })
        if (res.ok) {
          addedCount++
        }
      } catch (e) {
      }
    }
  }

  if (addedCount > 0) {
    showToast(`${addedCount} categorias essenciais adicionadas!`, 'success')
    await loadData()
  } else {
    showToast('As categorias essenciais já estão configuradas.', 'success')
  }
  isGenerating.value = false
}

const deleteCategory = async (id) => {
  try {
    const res = await fetchWithAuth(`https://credcode-backend.onrender.com/api/finances/categories/${id}/`, {
      method: 'DELETE'
    })

    if (res.ok) {
      showToast('Categoria removida!', 'success')
      loadData()
    } else {
      showToast('Erro ao remover categoria.', 'error')
    }
  } catch (e) {
    showToast('Erro de conexão.', 'error')
  }
}
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
  
  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Configurações</h1>
        <p>Gerencie o seu perfil e as suas preferências de sistema</p>
      </div>
    </div>

    <div class="tabs-container">
      <button :class="['tab-btn', { active: activeTab === 'profile' }]" @click="activeTab = 'profile'">
        Perfil do Utilizador
      </button>
      <button :class="['tab-btn', { active: activeTab === 'categories' }]" @click="activeTab = 'categories'">
        Categorias Personalizadas
      </button>
    </div>

    <div v-if="activeTab === 'profile'" class="settings-card">
      <form @submit.prevent="saveProfile" class="settings-form">
        <div class="form-group">
          <label>Nome Completo</label>
          <input v-model="profileForm.fullName" type="text" placeholder="Como queres ser chamado?" required />
        </div>
        <button type="submit" class="btn-save">Salvar Alterações</button>
      </form>
    </div>

    <div v-if="activeTab === 'categories'" class="settings-card">
      <form @submit.prevent="addCategory" class="add-category-row">
        <div class="form-group" style="flex: 2; margin: 0;">
          <label>Nome da Categoria</label>
          <input v-model="newCategoryForm.name" type="text" placeholder="Ex: Viagens, Pets, Educação..." required />
        </div>
        <div class="form-group" style="flex: 1; margin: 0;">
          <label>Tipo</label>
          <select v-model="newCategoryForm.type" required>
            <option value="expense">Saída</option>
            <option value="income">Entrada</option>
          </select>
        </div>
        <button type="submit" class="btn-save">Adicionar</button>
      </form>

      <div class="categories-header-row">
        <h3>Categorias Cadastradas</h3>
        <button type="button" class="btn-generate" @click="generateEssentialCategories" :disabled="isGenerating">
          ✨ Gerar Essenciais
        </button>
      </div>

      <div v-if="categories.length === 0" class="empty-state">
        Nenhuma categoria personalizada criada ainda.
      </div>

      <div class="categories-grid" v-else>
        <div v-for="cat in categories" :key="cat.id" class="category-item">
          <div class="cat-info">
            <span class="cat-name">{{ cat.name }}</span>
            <span :class="['cat-type', cat.type === 'income' ? 'type-income' : 'type-expense']">
              {{ cat.type === 'income' ? 'Entrada' : 'Saída' }}
            </span>
          </div>
          <button type="button" class="btn-delete" @click="deleteCategory(cat.id)" title="Excluir Categoria">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
          </button>
        </div>
      </div>
    </div>

    <FooterComp />
  </SideLayout>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.header-titles h1 { color: var(--text-primary); font-size: 2rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.5px; transition: color 0.3s; }
.header-titles p { color: var(--text-secondary); margin: 0; font-size: 1.05rem; transition: color 0.3s; }

.tabs-container { display: flex; gap: 15px; margin-bottom: 25px; border-bottom: 2px solid var(--border-color); padding-bottom: 15px; transition: border-color 0.3s; }
.tab-btn { background: transparent; border: none; color: var(--text-secondary); font-size: 1.05rem; font-weight: 700; padding: 12px 24px; cursor: pointer; transition: all 0.3s; border-radius: 12px; }
.tab-btn.active { background: var(--bg-card); color: var(--text-primary); box-shadow: var(--shadow-sm); border: 1px solid var(--border-color); }
.tab-btn:hover:not(.active) { color: var(--text-primary); background: var(--input-bg); }

.settings-card { background: var(--bg-card); border-radius: 20px; padding: 35px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); transition: background-color 0.3s, border-color 0.3s; }
.settings-form { max-width: 500px; display: flex; flex-direction: column; gap: 25px; }

.form-group { display: flex; flex-direction: column; gap: 10px; }
.form-group label { font-size: 0.95rem; font-weight: 600; color: var(--text-secondary); transition: color 0.3s; }
.form-group input, .form-group select { width: 100%; box-sizing: border-box; padding: 16px; border: 1px solid var(--border-input); border-radius: 12px; font-size: 1rem; background-color: var(--input-bg); color: var(--text-primary); outline: none; transition: all 0.3s; font-family: 'Inter', sans-serif; }
.form-group input:focus, .form-group select:focus { border-color: #f7b500; box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1); background-color: var(--bg-card); }

.btn-save { padding: 16px 24px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 12px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3); height: 53px; }
.btn-save:hover { transform: translateY(-2px); box-shadow: 0 15px 25px -5px rgba(16, 185, 129, 0.4); }

.add-category-row { display: flex; gap: 15px; align-items: flex-end; margin-bottom: 35px; padding-bottom: 35px; border-bottom: 1px solid var(--border-color); }

.categories-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.categories-header-row h3 { color: var(--text-primary); font-size: 1.2rem; font-weight: 800; margin: 0; }

.btn-generate { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f7b500; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 700; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px; }
.btn-generate:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.btn-generate:disabled { opacity: 0.7; cursor: not-allowed; }
[data-theme="dark"] .btn-generate { background: linear-gradient(135deg, #f7b500 0%, #e6a800 100%); color: #0f172a; }

.empty-state { text-align: center; padding: 40px; color: var(--text-secondary); font-weight: 500; background: var(--input-bg); border-radius: 12px; border: 1px dashed var(--border-input); transition: all 0.3s; }

.categories-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }
.category-item { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: var(--input-bg); border-radius: 12px; border: 1px solid var(--border-input); transition: all 0.3s; }
.category-item:hover { background: var(--bg-card); border-color: var(--border-color); box-shadow: var(--shadow-sm); transform: translateY(-2px); }

.cat-info { display: flex; flex-direction: column; gap: 6px; }
.cat-name { font-weight: 700; color: var(--text-primary); font-size: 1.05rem; transition: color 0.3s; }
.cat-type { font-size: 0.75rem; font-weight: 700; padding: 4px 10px; border-radius: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.type-income { background: var(--positive-bg); color: #059669; }
.type-expense { background: var(--negative-bg); color: #dc2626; }

.btn-delete { background: var(--negative-bg); color: #dc2626; border: 1px solid transparent; width: 40px; height: 40px; border-radius: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.btn-delete:hover { background: #dc2626; color: white; transform: scale(1.05); }

@media (max-width: 768px) {
  .add-category-row { flex-direction: column; align-items: stretch; gap: 20px; }
  .btn-save { width: 100%; }
  .tabs-container { flex-direction: column; gap: 10px; border-bottom: none; }
  .tab-btn { width: 100%; text-align: center; }
  .categories-header-row { flex-direction: column; align-items: flex-start; gap: 15px; }
  .btn-generate { width: 100%; justify-content: center; }
}
</style>