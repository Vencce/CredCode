<script setup>
import { RouterLink, useRouter } from 'vue-router'
import { reactive, ref } from 'vue'
import ToastMessage from '../components/ToastMessage.vue'

const router = useRouter()

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const showPassword = ref(false)
const showConfirmPassword = ref(false)

const toast = reactive({
  show: false,
  message: '',
  type: 'error'
})

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

const handleRegister = async () => {
  if (form.password !== form.confirmPassword) {
    showToast('As senhas não coincidem', 'error')
    return
  }

  try {
    const response = await fetch('https://credcode-backend.onrender.com/api/auth/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: form.username,
        email: form.email,
        password: form.password
      })
    })

    if (response.ok) {
      showToast('Cadastro realizado com sucesso!', 'success')
      setTimeout(() => {
        router.push('/')
      }, 1500)
    } else {
      const data = await response.json()
      showToast(data.detail || 'Erro ao realizar o cadastro', 'error')
    }
  } catch (error) {
    showToast('Erro de conexão com o terminal.', 'error')
  }
}
</script>

<template>
  <div class="page-wrapper">
    <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />
    
    <div class="left-side">
      <div class="overlay-content">
        <img src="../components/imagens/logo_cortada.png" alt="CREDCODE Logo" class="hero-logo" />
        <h1 class="quote">SEJA JUSTO.<br />NÃO TENHA DOIS PESOS<br />E DUAS MEDIDAS!</h1>
        <h2 class="welcome-text">SEJA BEM VINDO!</h2>
      </div>
      <div class="footer-logos">
        <div class="divider-line"></div>
        <div class="logos-container">
          <p class="footer-tagline">TERMINAL FINANCEIRO: O CAMINHO DA LÓGICA</p>
        </div>
      </div>
    </div>

    <div class="right-side">
      <div class="login-card">
        <div class="form-header">
          <h2 class="main-logo">CRED<span>CODE</span></h2>
        </div>

        <div class="login-title-wrapper">
          <h3 class="login-title">Crie seu Acesso</h3>
        </div>

        <form @submit.prevent="handleRegister" class="login-form">
          <div class="input-group">
            <input
              v-model="form.username"
              type="text"
              placeholder="Nome de utilizador"
              required
            />
          </div>

          <div class="input-group">
            <input
              v-model="form.email"
              type="email"
              placeholder="E-mail"
              required
            />
          </div>

          <div class="input-group password-group">
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Senha"
              required
            />
            <button type="button" class="btn-eye" @click="showPassword = !showPassword">
              <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path>
                <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"></path>
                <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"></path>
                <line x1="2" y1="2" x2="22" y2="22"></line>
              </svg>
            </button>
          </div>

          <div class="input-group password-group">
            <input
              v-model="form.confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              placeholder="Confirme sua Senha"
              required
            />
            <button type="button" class="btn-eye" @click="showConfirmPassword = !showConfirmPassword">
              <svg v-if="!showConfirmPassword" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path>
                <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"></path>
                <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"></path>
                <line x1="2" y1="2" x2="22" y2="22"></line>
              </svg>
            </button>
          </div>

          <button type="submit" class="btn-login btn-register">CADASTRAR</button>
        </form>

        <p class="register-link">Já tem acesso? <RouterLink to="/">Entrar</RouterLink></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrapper {
  display: flex;
  width: 100%;
  min-height: 100vh;
  font-family: 'Inter', 'Segoe UI', sans-serif;
  background-color: #f8fafc;
}

.left-side {
  flex: 1.2;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
  padding: 40px;
  color: white;
  overflow: hidden;
}

.left-side::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 50% 50%, rgba(247, 181, 0, 0.05) 0%, transparent 50%);
  pointer-events: none;
}

.hero-logo {
  max-width: 280px;
  margin-bottom: 50px;
  z-index: 10;
}

.overlay-content {
  text-align: center;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.quote {
  font-size: 3rem;
  font-weight: 900;
  text-transform: uppercase;
  line-height: 1.1;
  letter-spacing: -1px;
  margin-bottom: 30px;
  color: #ffffff;
  text-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.welcome-text {
  font-size: 1.8rem;
  font-weight: 800;
  text-transform: uppercase;
  color: #f7b500;
  letter-spacing: 2px;
}

.footer-logos {
  width: 80%;
  margin-bottom: 20px;
  z-index: 10;
}

.divider-line {
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, #f7b500 50%, transparent 100%);
  width: 100%;
  margin-bottom: 20px;
  opacity: 0.5;
}

.footer-tagline {
  font-size: 0.85rem;
  letter-spacing: 3px;
  font-weight: 700;
  text-align: center;
  color: #94a3b8;
}

.right-side {
  flex: 0.8;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background-color: #f8fafc;
}

.login-card {
  width: 100%;
  max-width: 440px;
  background: white;
  padding: 50px 40px;
  border-radius: 24px;
  box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.05), 0 8px 10px -6px rgba(15, 23, 42, 0.02);
  border: 1px solid #f1f5f9;
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.main-logo {
  font-size: 2.8rem;
  margin: 0;
  font-weight: 900;
  color: #0f172a;
  letter-spacing: -1.5px;
}

.main-logo span {
  color: #f7b500;
}

.login-title-wrapper {
  margin-bottom: 30px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f1f5f9;
}

.login-title {
  font-size: 1.2rem;
  color: #0f172a;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-group input {
  width: 100%;
  padding: 16px;
  border: 1px solid #cbd5e1;
  background-color: #f8fafc;
  border-radius: 12px;
  font-size: 1rem;
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

.password-group {
  position: relative;
  display: flex;
  align-items: center;
}

.password-group input {
  padding-right: 50px;
}

.btn-eye {
  position: absolute;
  right: 15px;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: color 0.2s;
}

.btn-eye:hover {
  color: #0f172a;
}

.btn-login {
  width: 100%;
  padding: 18px;
  background: linear-gradient(135deg, #f7b500 0%, #e6a800 100%);
  color: #0f172a;
  border: none;
  border-radius: 12px;
  font-size: 1.05rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 15px -3px rgba(247, 181, 0, 0.3);
}

.btn-register {
  margin-top: 10px;
}

.btn-login:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 25px -5px rgba(247, 181, 0, 0.4);
}

.register-link {
  text-align: center;
  margin-top: 35px;
  font-size: 0.95rem;
  color: #64748b;
  font-weight: 500;
}

.register-link a {
  color: #0f172a;
  font-weight: 800;
  text-decoration: none;
  margin-left: 5px;
  position: relative;
}

.register-link a::after {
  content: '';
  position: absolute;
  width: 100%;
  transform: scaleX(0);
  height: 2px;
  bottom: -4px;
  left: 0;
  background-color: #f7b500;
  transform-origin: bottom right;
  transition: transform 0.25s ease-out;
}

.register-link a:hover::after {
  transform: scaleX(1);
  transform-origin: bottom left;
}

@media (max-width: 1024px) {
  .left-side {
    display: none;
  }
  .login-card {
    padding: 40px 25px;
  }
}
</style>