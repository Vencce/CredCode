<script setup>
import { RouterLink, useRouter } from 'vue-router'
import { reactive } from 'vue'

const router = useRouter()
const form = reactive({
  username: '',
  name: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const handleRegister = async () => {
  if (form.password !== form.confirmPassword) {
    alert("As senhas não conferem!")
    return
  }

  try {
    const response = await fetch('http://localhost:8000/api/auth/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: form.username,
        email: form.email,
        first_name: form.name,
        password: form.password
      })
    })

    if (response.ok) {
      alert('Cadastro realizado! Vamos configurar seu terminal.')
      router.push('/formulario')
    } else {
      const data = await response.json()
      alert('Erro no cadastro: ' + JSON.stringify(data))
    }
  } catch (error) {
    alert('Erro ao conectar com o servidor.')
  }
}
</script>

<template>
  <div class="page-wrapper">
    <div class="left-side">
      <div class="overlay-content">
        <img src="../components/imagens/logo_cortada.png" alt="CREDCODE Logo" class="hero-logo" />
        <h1 class="quote">INVISTA COM LÓGICA;<br />CRIE O SEU FUTURO<br />NO TERMINAL!</h1>
        <h2 class="welcome-text">CADASTRE-SE AGORA</h2>
      </div>
      <div class="footer-logos">
        <div class="divider-line"></div>
        <div class="logos-container">
          <p class="footer-tagline">TERMINAL FINANCEIRO: O CAMINHO DA LÓGICA</p>
        </div>
      </div>
    </div>

    <div class="right-side">
      <div class="login-box">
        <div class="form-header">
          <h2 class="main-logo">CRED<span>CODE</span></h2>
        </div>

        <h3 class="login-title">Criar Nova Conta</h3>

        <form @submit.prevent="handleRegister">
          <div class="input-group">
            <input v-model="form.username" type="text" placeholder="Nome de utilizador" required />
          </div>
          <div class="input-group">
            <input v-model="form.name" type="text" placeholder="Nome completo" required />
          </div>
          <div class="input-group">
            <input v-model="form.email" type="email" placeholder="seu.email@credcode.com" required />
          </div>
          <div class="input-group">
            <input v-model="form.password" type="password" placeholder="Senha do Terminal" required />
          </div>
          <div class="input-group">
            <input v-model="form.confirmPassword" type="password" placeholder="Confirme sua senha" required />
          </div>

          <button type="submit" class="btn-login">CADASTRAR</button>
        </form>

        <p class="register-link">Já possui conta? <RouterLink to="/">Acesse aqui</RouterLink></p>
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
  background-color: #ffffff;
}

.left-side {
  flex: 1.2;
  background: linear-gradient(135deg, #0a2a43 0%, #153e5c 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
  padding: 40px;
  color: white;
}

.hero-logo {
  max-width: 280px;
  margin-bottom: 40px;
}

.overlay-content {
  text-align: center;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.quote {
  font-size: 2.8rem;
  font-weight: 900;
  text-transform: uppercase;
  line-height: 1.1;
  letter-spacing: 1px;
  margin-bottom: 30px;
  color: #ffffff;
}

.welcome-text {
  font-size: 2rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #f7b500;
}

.footer-logos {
  width: 80%;
  margin-bottom: 40px;
}

.divider-line {
  height: 2px;
  background: #f7b500;
  width: 100%;
  margin-bottom: 20px;
}

.footer-tagline {
  font-size: 0.9rem;
  letter-spacing: 2px;
  font-weight: 600;
  text-align: center;
}

.right-side {
  flex: 0.8;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.login-box {
  width: 100%;
  max-width: 380px;
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.main-logo {
  font-size: 3.2rem;
  margin: 0;
  font-weight: 900;
  color: #0a2a43;
  letter-spacing: -1px;
}

.main-logo span {
  color: #f7b500;
}

.login-title {
  font-size: 1.1rem;
  margin-bottom: 25px;
  color: #0a2a43;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-left: 4px solid #f7b500;
  padding-left: 10px;
}

.input-group {
  margin-bottom: 15px;
}

.input-group input {
  width: 100%;
  padding: 16px;
  border: 1px solid #e0e6ed;
  background-color: #f8fafc;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s;
}

.input-group input:focus {
  border-color: #0a2a43;
  background-color: #ffffff;
  box-shadow: 0 0 0 3px rgba(10, 42, 67, 0.1);
}

.btn-login {
  width: 100%;
  padding: 16px;
  background-color: #f7b500;
  color: #0a2a43;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 800;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 14px rgba(247, 181, 0, 0.3);
  margin-top: 10px;
}

.btn-login:hover {
  background-color: #e6a800;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(247, 181, 0, 0.4);
}

.register-link {
  text-align: center;
  margin-top: 30px;
  font-size: 0.9rem;
  color: #64748b;
}

.register-link a {
  color: #0a2a43;
  font-weight: 700;
  text-decoration: none;
}

@media (max-width: 1024px) {
  .left-side {
    display: none;
  }
}
</style>