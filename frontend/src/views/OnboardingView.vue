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
      <div class="brand-header">
        <h2 class="main-logo">CRED<span>CODE</span></h2>
      </div>

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
            <div v-if="currentStep === 1" class="step-content">
              <h2 class="step-title">Confirme seu nome</h2>
              <p class="step-description">Identificamos você, mas pode ajustar se preferir.</p>
              <div class="input-group">
                <input v-model="userData.name" type="text" placeholder="Nome completo" @keyup.enter="isStepValid ? next() : null">
              </div>
            </div>

            <div v-if="currentStep === 2" class="step-content">
              <h2 class="step-title">Qual sua renda mensal?</h2>
              <p class="step-description">Quanto você costuma receber por mês (líquido)?</p>
              <div class="input-group">
                <input v-model="userData.monthly_income" type="number" placeholder="R$ 0,00" @keyup.enter="isStepValid ? next() : null">
              </div>
            </div>

            <div v-if="currentStep === 3" class="step-content">
              <h2 class="step-title">Valor em Conta</h2>
              <p class="step-description">Qual o saldo disponível em sua conta hoje?</p>
              <div class="input-group">
                <input v-model="userData.account_balance" type="number" placeholder="R$ 0,00" @keyup.enter="isStepValid ? finish() : null">
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
    <div class="loader-spinner"></div>
    <p>Preparando seu terminal...</p>
  </div>
</template>

<style scoped>
.onboarding-page { 
  width: 100%; 
  min-height: 100vh; 
  display: flex; 
  justify-content: center; 
  align-items: center; 
  background-color: #f8fafc; 
  font-family: 'Inter', sans-serif; 
  padding: 20px;
}

.onboarding-container { 
  width: 100%; 
  max-width: 580px; 
}

.brand-header {
  text-align: center;
  margin-bottom: 30px;
}

.main-logo {
  font-size: 2.4rem;
  margin: 0;
  font-weight: 900;
  color: #0f172a;
  letter-spacing: -1.5px;
}

.main-logo span {
  color: #f7b500;
}

.progress-wrapper {
  margin-bottom: 25px;
}

.progress-info { 
  display: flex; 
  justify-content: space-between; 
  font-size: 0.85rem; 
  color: #64748b; 
  font-weight: 700; 
  margin-bottom: 12px; 
  text-transform: uppercase; 
  letter-spacing: 1px;
}

.progress-bar { 
  width: 100%; 
  height: 8px; 
  background: #e2e8f0; 
  border-radius: 8px; 
  overflow: hidden; 
}

.progress-fill { 
  height: 100%; 
  background: linear-gradient(90deg, #f7b500 0%, #e6a800 100%); 
  border-radius: 8px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1); 
  box-shadow: 0 0 10px rgba(247, 181, 0, 0.4);
}

.content-box { 
  background: white; 
  padding: 50px 45px; 
  border-radius: 24px; 
  box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.05), 0 8px 10px -6px rgba(15, 23, 42, 0.02); 
  border: 1px solid #f1f5f9; 
}

.step-content {
  min-height: 180px;
}

.step-title { 
  color: #0f172a; 
  font-size: 2rem; 
  font-weight: 800; 
  margin: 0 0 10px 0; 
  letter-spacing: -1px;
}

.step-description { 
  color: #64748b; 
  margin-bottom: 35px; 
  font-size: 1.05rem; 
  line-height: 1.5;
}

.input-group input { 
  width: 100%; 
  padding: 18px; 
  border: 1px solid #cbd5e1; 
  background-color: #f8fafc;
  border-radius: 12px; 
  font-size: 1.1rem; 
  font-family: 'Inter', sans-serif;
  outline: none; 
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
  color: #0f172a;
}

.input-group input::placeholder {
  color: #94a3b8;
  font-weight: 500;
}

.input-group input:focus { 
  border-color: #f7b500; 
  background-color: white;
  box-shadow: 0 0 0 4px rgba(247, 181, 0, 0.1);
}

.action-footer { 
  display: flex; 
  gap: 15px; 
  margin-top: 20px; 
}

.btn-primary { 
  flex: 2; 
  padding: 18px; 
  background: linear-gradient(135deg, #f7b500 0%, #e6a800 100%); 
  color: #0f172a; 
  border: none; 
  border-radius: 12px; 
  font-weight: 800; 
  font-size: 1.05rem; 
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer; 
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
  box-shadow: 0 10px 15px -3px rgba(247, 181, 0, 0.3);
}

.btn-primary:hover:not(:disabled) { 
  transform: translateY(-3px); 
  box-shadow: 0 15px 25px -5px rgba(247, 181, 0, 0.4);
}

.btn-primary:disabled { 
  background: #e2e8f0;
  color: #94a3b8;
  box-shadow: none;
  cursor: not-allowed; 
}

.btn-secondary { 
  flex: 1; 
  padding: 18px; 
  background-color: #f1f5f9; 
  color: #475569; 
  border: none;
  border-radius: 12px; 
  font-weight: 700; 
  font-size: 1rem;
  cursor: pointer; 
  transition: background-color 0.2s;
}

.btn-secondary:hover {
  background-color: #e2e8f0;
  color: #0f172a;
}

.fade-slide-enter-active, .fade-slide-leave-active { 
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
}
.fade-slide-enter-from { 
  opacity: 0; 
  transform: translateX(30px); 
}
.fade-slide-leave-to { 
  opacity: 0; 
  transform: translateX(-30px); 
}

.loading-screen { 
  display: flex; 
  flex-direction: column;
  justify-content: center; 
  align-items: center; 
  height: 100vh; 
  font-family: 'Inter', sans-serif; 
  color: #0f172a; 
  background-color: #f8fafc;
}

.loading-screen p {
  margin-top: 20px;
  font-weight: 700;
  font-size: 1.1rem;
  color: #64748b;
}

.loader-spinner {
  width: 48px;
  height: 48px;
  border: 5px solid #e2e8f0;
  border-bottom-color: #f7b500;
  border-radius: 50%;
  display: inline-block;
  box-sizing: border-box;
  animation: rotation 1s linear infinite;
}

@keyframes rotation {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 600px) {
  .content-box {
    padding: 40px 25px;
  }
  .step-title {
    font-size: 1.6rem;
  }
}
</style>