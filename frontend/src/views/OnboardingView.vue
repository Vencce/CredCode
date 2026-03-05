<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import ToastMessage from '../components/ToastMessage.vue';

const router = useRouter();
const isLoading = ref(true);

const currentStep = ref(1);
const totalSteps = 3;

const userData = reactive({
  name: '',
  monthly_income: null,
  account_balance: null
});

const toast = reactive({
  show: false,
  message: '',
  type: 'error'
});

const showToast = (message, type = 'error') => {
  toast.message = message;
  toast.type = type;
  toast.show = true;
};

const progressPercentage = computed(() => {
  return (currentStep.value / totalSteps) * 100;
});

const isStepValid = computed(() => {
  if (currentStep.value === 1) return userData.name.trim() !== '';
  if (currentStep.value === 2) return userData.monthly_income !== null && userData.monthly_income !== '';
  if (currentStep.value === 3) return userData.account_balance !== null && userData.account_balance !== '';
  return false;
});

onMounted(async () => {
  const token = localStorage.getItem('access_token');
  if (!token) {
    router.push('/');
    return;
  }

  try {
    const response = await fetch('http://localhost:8000/api/finances/profile/', {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.ok) {
      const data = await response.json();
      if (data.has_profile) {
        router.push('/home');
        return;
      }
    }
    
    const savedName = localStorage.getItem('temp_name');
    if (savedName) userData.name = savedName;
    isLoading.value = false;
  } catch (error) {
    isLoading.value = false;
  }
});

const next = () => { if (currentStep.value < totalSteps) currentStep.value++; };
const prev = () => { if (currentStep.value > 1) currentStep.value--; };

const finish = async () => {
  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch('http://localhost:8000/api/finances/profile/', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        full_name: userData.name,
        monthly_income: userData.monthly_income,
        account_balance: userData.account_balance
      })
    });

    if (response.ok) {
      localStorage.removeItem('temp_name');
      showToast('Terminal configurado com sucesso!', 'success');
      setTimeout(() => {
        router.push('/home');
      }, 1500);
    } else {
      showToast('Erro ao salvar os dados.', 'error');
    }
  } catch (error) {
    showToast('Erro de conexão com o servidor.', 'error');
  }
};
</script>

<template>
  <div v-if="!isLoading" class="onboarding-page">
    <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
    
    <div class="onboarding-container">
      <div class="progress-wrapper">
        <div class="progress-info">
          <span>Passo {{ currentStep }} de {{ totalSteps }}</span>
          <span>{{ Math.round(progressPercentage) }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
        </div>
      </div>

      <div class="content-box">
        <transition name="fade-slide" mode="out-in">
          <div :key="currentStep">
            <div v-if="currentStep === 1">
              <h2 class="step-title">Confirme seu nome</h2>
              <p class="step-description">Identificamos você, mas pode ajustar se preferir.</p>
              <div class="input-group">
                <input v-model="userData.name" type="text" placeholder="Nome completo">
              </div>
            </div>

            <div v-if="currentStep === 2">
              <h2 class="step-title">Qual sua renda mensal?</h2>
              <p class="step-description">Quanto você costuma receber por mês (líquido)?</p>
              <div class="input-group">
                <input v-model="userData.monthly_income" type="number" placeholder="R$ 0,00">
              </div>
            </div>

            <div v-if="currentStep === 3">
              <h2 class="step-title">Valor em Conta</h2>
              <p class="step-description">Qual o saldo disponível em sua conta hoje?</p>
              <div class="input-group">
                <input v-model="userData.account_balance" type="number" placeholder="R$ 0,00" @keyup.enter="finish">
              </div>
            </div>
          </div>
        </transition>

        <div class="action-footer">
          <button v-if="currentStep > 1" @click="prev" class="btn-secondary">VOLTAR</button>
          <button v-if="currentStep < totalSteps" @click="next" class="btn-primary" :disabled="!isStepValid">PRÓXIMO</button>
          <button v-else @click="finish" class="btn-primary" :disabled="!isStepValid">FINALIZAR</button>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="loading-screen">
    <p>Verificando terminal...</p>
  </div>
</template>

<style scoped>
.onboarding-page { width: 100%; min-height: 100vh; display: flex; justify-content: center; align-items: center; background-color: #f4f7f9; font-family: 'Inter', sans-serif; }
.onboarding-container { width: 100%; max-width: 550px; padding: 20px; }
.progress-info { display: flex; justify-content: space-between; font-size: 0.85rem; color: #0a2a43; font-weight: 700; margin-bottom: 10px; text-transform: uppercase; }
.progress-bar { width: 100%; height: 8px; background: #e0e6ed; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: #f7b500; transition: width 0.4s ease; }
.content-box { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(10, 42, 67, 0.05); }
.step-title { color: #0a2a43; font-size: 1.8rem; font-weight: 800; margin-bottom: 8px; }
.step-description { color: #64748b; margin-bottom: 30px; font-size: 1rem; }
.input-group input { width: 100%; padding: 18px; border: 2px solid #e0e6ed; border-radius: 12px; font-size: 1.1rem; outline: none; transition: border-color 0.3s; }
.input-group input:focus { border-color: #f7b500; }
.action-footer { display: flex; gap: 15px; margin-top: 40px; }
.btn-primary { flex: 2; padding: 18px; background-color: #f7b500; color: #0a2a43; border: none; border-radius: 12px; font-weight: 800; font-size: 1rem; cursor: pointer; transition: all 0.3s; }
.btn-primary:hover:not(:disabled) { background-color: #e6a800; transform: translateY(-2px); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { flex: 1; padding: 18px; border: 2px solid #e0e6ed; border-radius: 12px; background: none; color: #64748b; font-weight: 700; cursor: pointer; }
.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.3s ease; }
.fade-slide-enter-from { opacity: 0; transform: translateX(20px); }
.fade-slide-leave-to { opacity: 0; transform: translateX(-20px); }
.loading-screen { display: flex; justify-content: center; align-items: center; height: 100vh; font-family: 'Inter', sans-serif; color: #0a2a43; font-weight: bold; }
</style>