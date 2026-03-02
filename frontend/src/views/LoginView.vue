<template>
  <div class="login-container">
    <div class="header">
      <div class="logo-box">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h1>FinanceApp</h1>
      <p>Controle as suas finanças pessoais</p>
    </div>

    <div class="card">
      <h2>Entrar</h2>
      
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="email">E-mail</label>
          <input 
            v-model="form.email"
            type="email" 
            id="email" 
            placeholder="exemplo@email.com" 
            required
          >
        </div>

        <div class="form-group">
          <a href="#" class="forgot-link">Esqueceu-se?</a>
          <label for="password">Palavra-passe</label>
          <input 
            v-model="form.password"
            type="password" 
            id="password" 
            placeholder="••••••••" 
            required
          >
        </div>

        <button type="submit" class="btn-submit">
          Aceder à conta
        </button>
      </form>

      <div class="divider">
        <span>Ou entrar com</span>
      </div>

      <div class="social-buttons">
        <button class="btn-social" @click="socialLogin('Google')">
          <img src="https://www.svgrepo.com/show/355037/google.svg" alt="Google">
          Google
        </button>
        <button class="btn-social" @click="socialLogin('Apple')">
          <img src="https://www.svgrepo.com/show/448234/apple.svg" alt="Apple">
          Apple
        </button>
      </div>

      <p class="register-text">
        Novo por aqui? <a href="#">Criar conta</a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue';

// Estado reativo para os campos do formulário
const form = reactive({
  email: '',
  password: ''
});

// Função para lidar com o login
const handleLogin = () => {
  console.log('Dados de login:', form);
  alert(`Login tentado para: ${form.email}`);
};

// Função para login social
const socialLogin = (provider) => {
  console.log(`Login com ${provider}`);
};
</script>

<style scoped>
/* O "scoped" garante que o CSS abaixo afete apenas este componente */
:root {
  --primary-color: #4f46e5;
  --primary-hover: #4338ca;
  --bg-gradient: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%);
  --text-main: #1e293b;
  --text-muted: #64748b;
  --white: #ffffff;
  --border: #e2e8f0;
  --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
}

.login-container {
  width: 100%;
  max-width: 400px;
  margin: auto; /* Centraliza se estiver num container flex */
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.logo-box {
  background: var(--white);
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
  box-shadow: var(--shadow);
}

.logo-box svg {
  color: var(--primary-color);
  width: 40px;
  height: 40px;
}

.header h1 {
  color: var(--white);
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 5px;
}

.header p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.card {
  background: rgba(255, 255, 255, 0.98);
  padding: 40px;
  border-radius: 24px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
  color: var(--text-main);
}

.card h2 {
  font-size: 22px;
  margin-bottom: 25px;
  font-weight: 700;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  outline: none;
  transition: all 0.2s;
  font-size: 15px;
}

.form-group input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
}

.forgot-link {
  float: right;
  font-size: 12px;
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 500;
}

.btn-submit {
  width: 100%;
  background: var(--primary-color);
  color: var(--white);
  border: none;
  padding: 14px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  margin-top: 10px;
}

.btn-submit:hover {
  background: var(--primary-hover);
}

.btn-submit:active {
  transform: scale(0.98);
}

.divider {
  margin: 30px 0;
  text-align: center;
  position: relative;
}

.divider::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border);
  z-index: 1;
}

.divider span {
  background: var(--white);
  padding: 0 15px;
  font-size: 13px;
  color: var(--text-muted);
  position: relative;
  z-index: 2;
}

.social-buttons {
  display: grid;
  grid-template-cols: 1fr 1fr;
  gap: 15px;
}

.btn-social {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--white);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: background 0.2s;
}

.btn-social:hover {
  background: #f8fafc;
}

.btn-social img {
  width: 20px;
  height: 20px;
}

.register-text {
  text-align: center;
  margin-top: 30px;
  font-size: 14px;
  color: var(--text-muted);
}

.register-text a {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 700;
}
</style>