<script setup>
import { RouterLink } from 'vue-router'
import { reactive } from 'vue'

const form = reactive({
  email: '',
  password: '',
  remember: false,
})

const handleLogin = () => {
  console.log(form)
}
</script>

<template>
  <div class="page-wrapper">
    <div class="left-side">
      <div class="overlay-content">
        <img src="../components/imagens/logo.png" alt="CREDCODE Logo" class="hero-logo" />
        <h1 class="quote">SEJA JUSTO;<br />NÃO TENHA DOIS PESOS<br />E DUAS MEDIDAS!</h1>
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
      <div class="login-box">
        <div class="form-header">
          <h2 class="main-logo">CRED<span>CODE</span></h2>
        </div>

        <h3 class="login-title">Acesse o Terminal</h3>

        <form @submit.prevent="handleLogin">
          <div class="input-group">
            <input
              v-model="form.email"
              type="email"
              placeholder="seu.email@credcode.com"
              required
            />
          </div>

          <div class="input-group">
            <input
              v-model="form.password"
              type="password"
              placeholder="Senha do Terminal"
              required
            />
          </div>

          <div class="form-options">
            <a href="#" class="forgot-pass">Recuperar acesso</a>
            <label class="remember-me">
              <input type="checkbox" v-model="form.remember" />
              <span>Lembrar terminal</span>
            </label>
          </div>

          <RouterLink to="/formulario" class="btn-login" @click="handleLogin">
            <button type="submit" class="btn-login">ENTRAR</button>
          </RouterLink>
          <RouterLink to="/home" class="btn-login" @click="handleLogin">
            <button type="submit" class="btn-login">HOME - Verificar</button>
          </RouterLink>
        </form>

        <p class="register-link">Ainda não tem acesso? <a href="#">Cadastre-se</a></p>
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
  background: linear-gradient(135deg, #0a2a43 0%, hwb(205 8% 64%) 100%);
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

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  font-size: 0.85rem;
}

.forgot-pass {
  color: #0a2a43;
  text-decoration: none;
  font-weight: 600;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  cursor: pointer;
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
