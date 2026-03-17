<script setup>
const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="creative-footer">
    <div class="footer-content">
      <div class="brand-section">
        <h3 class="footer-logo">CRED<span>CODE</span></h3>
        <p class="slogan">Transformando lógica em inteligência financeira.</p>
      </div>
      
      <div class="credits-section">
        <p class="copyright">
          &copy; {{ currentYear }} Todos os direitos reservados.
        </p>
        <p class="team">
          Desenvolvido por: 
          <span class="highlight">Hugo Lopes</span>, 
          <span class="highlight">Kelvin Lopes</span>, 
          <span class="highlight">Thiago Monteiro</span> & 
          <span class="highlight">Vitor Ferreira</span>.
        </p>
      </div>
    </div>
    
    <div class="footer-bottom-bar"></div>
  </footer>
</template>

<style scoped>
.creative-footer {
  margin-top: 40px;
  padding: 30px 40px;
  background: var(--bg-card);
  border-radius: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  position: relative;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
  transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
}

.footer-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 20px;
}

.brand-section {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.footer-logo {
  font-size: 1.5rem;
  font-weight: 900;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.5px;
  transition: color 0.3s;
}

.footer-logo span {
  color: #f7b500; 
}

.slogan {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0;
  font-weight: 500;
  transition: color 0.3s;
}

.credits-section {
  padding-top: 15px;
  border-top: 1px dashed var(--border-color);
  width: 100%;
  transition: border-color 0.3s;
}

.copyright {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0 0 5px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: color 0.3s;
}

.team {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
  transition: color 0.3s;
}

.highlight {
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  transition: color 0.3s ease;
  cursor: default;
}

.highlight:hover {
  color: #10b981;
}

.footer-bottom-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, var(--text-primary), #10b981, #f7b500);
  opacity: 0.8;
}

@media (min-width: 768px) {
  .footer-content {
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
    align-items: flex-end;
  }
  
  .credits-section {
    padding-top: 0;
    border-top: none;
    width: auto;
    text-align: right;
  }
}
</style>