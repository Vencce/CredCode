<script setup>
import { ref, reactive, computed } from 'vue';

const currentStep = ref(1);
const totalSteps = 3;

const userData = reactive({
  name: '',
  occupation: '',
  wealth: null
});

const progressPercentage = computed(() => {
  return (currentStep.value / totalSteps) * 100;
});

const isStepValid = computed(() => {
  if (currentStep.value === 1) return userData.name.length > 3;
  if (currentStep.value === 2) return userData.occupation !== '';
  if (currentStep.value === 3) return userData.wealth !== null && userData.wealth >= 0;
  return false;
});

const next = () => {
  if (currentStep.value < totalSteps) currentStep.value++;
};

const prev = () => {
  if (currentStep.value > 1) currentStep.value--;
};

const finish = () => {
  console.log('Dados salvos no CREDCODE:', userData);
  alert('Terminal configurado com sucesso!');
};
</script>

<template>
  <div class="onboarding-page">
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
          <div :key="currentStep" class="step-content">
            
            <div v-if="currentStep === 1">
              <h2 class="step-title">Vamos começar pelo seu nome</h2>
              <p class="step-description">Como gostaria de ser chamado no terminal?</p>
              <div class="input-group">
                <input 
                  v-model="userData.name" 
                  type="text" 
                  placeholder="Nome completo"
                  @keyup.enter="next"
                >
              </div>
            </div>

            <div v-if="currentStep === 2">
              <h2 class="step-title">Qual sua ocupação atual?</h2>
              <p class="step-description">Isso nos ajuda a entender seu perfil financeiro.</p>
              <div class="input-group">
                <select v-model="userData.occupation">
                  <option value="" disabled>Selecione uma opção</option>
                  <option value="clt">CLT / Privado</option>
                  <option value="publico">Servidor Público</option>
                  <option value="autonomo">Autônomo / Freelancer</option>
                  <option value="empresario">Empresário</option>
                </select>
              </div>
            </div>

            <div v-if="currentStep === 3">
              <h2 class="step-title">Patrimônio estimado</h2>
              <p class="step-description">Qual o valor total de seus ativos hoje?</p>
              <div class="input-group">
                <input 
                  v-model="userData.wealth" 
                  type="number" 
                  placeholder="R$ 0,00"
                  @keyup.enter="finish"
                >
              </div>
            </div>

          </div>
        </transition>

        <div class="action-footer">
          <button 
            v-if="currentStep > 1" 
            @click="prev" 
            class="btn-secondary"
          >
            VOLTAR
          </button>
          
          <button 
            v-if="currentStep < totalSteps" 
            @click="next" 
            class="btn-primary"
            :disabled="!isStepValid"
          >
            PRÓXIMO
          </button>

          <button 
            v-else 
            @click="finish" 
            class="btn-primary"
            :disabled="!isStepValid"
          >
            FINALIZAR CONFIGURAÇÃO
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.onboarding-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f4f7f9;
  font-family: 'Inter', sans-serif;
  padding: 20px;
}

.onboarding-container {
  width: 100%;
  max-width: 550px;
}

.progress-wrapper {
  margin-bottom: 30px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #0a2a43;
  font-weight: 700;
  margin-bottom: 10px;
  text-transform: uppercase;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e6ed;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #f7b500;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.content-box {
  background: white;
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(10, 42, 67, 0.05);
}

.step-title {
  color: #0a2a43;
  font-size: 1.8rem;
  font-weight: 800;
  margin-bottom: 8px;
}

.step-description {
  color: #64748b;
  font-size: 1rem;
  margin-bottom: 30px;
}

.input-group input, .input-group select {
  width: 100%;
  padding: 18px;
  border: 2px solid #e0e6ed;
  border-radius: 12px;
  font-size: 1.1rem;
  color: #0a2a43;
  outline: none;
  transition: border-color 0.3s;
}

.input-group input:focus, .input-group select:focus {
  border-color: #f7b500;
}

.action-footer {
  display: flex;
  gap: 15px;
  margin-top: 40px;
}

.btn-primary {
  flex: 2;
  padding: 18px;
  background-color: #f7b500;
  color: #0a2a43;
  border: none;
  border-radius: 12px;
  font-weight: 800;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary:hover:not(:disabled) {
  background-color: #e6a800;
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  flex: 1;
  padding: 18px;
  background: none;
  border: 2px solid #e0e6ed;
  border-radius: 12px;
  color: #64748b;
  font-weight: 700;
  cursor: pointer;
}

.fade-slide-enter-active, .fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>