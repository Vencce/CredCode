<script setup>
// O ano é gerado dinamicamente, assim vocês nunca precisam atualizar o rodapé no réveillon!
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
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
  border: 1px solid #f1f5f9;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
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
  color: #0a2a43;
  margin: 0;
  letter-spacing: -0.5px;
}

/* O 'CODE' em dourado/amarelo seguindo a sua identidade visual */
.footer-logo span {
  color: #f7b500; 
}

.slogan {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
  font-weight: 500;
}

.credits-section {
  padding-top: 15px;
  border-top: 1px dashed #e2e8f0;
  width: 100%;
}

.copyright {
  font-size: 0.8rem;
  color: #94a3b8;
  margin: 0 0 5px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.team {
  font-size: 0.9rem;
  color: #475569;
  margin: 0;
  line-height: 1.6;
}

/* Destaca os nomes de vocês quando o usuário passa o mouse por cima */
.highlight {
  font-weight: 700;
  color: #0a2a43;
  white-space: nowrap;
  transition: color 0.3s ease;
  cursor: default;
}

.highlight:hover {
  color: #10b981; /* Fica verde (sucesso) ao passar o mouse */
}

/* A barrinha colorida no fundo */
.footer-bottom-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, #0a2a43, #10b981, #f7b500);
}

/* Layout responsivo: Fica lado a lado em telas maiores */
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