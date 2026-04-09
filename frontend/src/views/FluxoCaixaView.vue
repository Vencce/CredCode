<script setup>
import { ref, onMounted, reactive, shallowRef } from 'vue'
import * as echarts from 'echarts'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue'

const isLoading = ref(true)
const flowData = ref(null)
const chartRef = ref(null)
const chartInstance = shallowRef(null)

const fetchWithAuth = async (url) => {
  let token = localStorage.getItem('access_token')
  return await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
}

const initChart = (timeline) => {
  if (!chartRef.value) return
  if (chartInstance.value) chartInstance.value.dispose()
  
  chartInstance.value = echarts.init(chartRef.value)
  
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'

  const option = {
    tooltip: { 
      trigger: 'axis',
      formatter: '{b}: R$ {c}'
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: timeline.map(t => t.date),
      axisLabel: { color: isDark ? '#94a3b8' : '#64748b' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: isDark ? '#94a3b8' : '#64748b' },
      splitLine: { lineStyle: { color: isDark ? '#1e293b' : '#f1f5f9' } }
    },
    series: [{
      data: timeline.map(t => t.balance),
      type: 'line',
      smooth: true,
      symbolSize: 8,
      lineStyle: { width: 4, color: '#f7b500' },
      itemStyle: { color: '#f7b500' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(247, 181, 0, 0.3)' },
          { offset: 1, color: 'rgba(247, 181, 0, 0)' }
        ])
      }
    }]
  }
  chartInstance.value.setOption(option)
}

const loadData = async () => {
  try {
    const res = await fetchWithAuth('https://credcode-backend.onrender.com/api/finances/cash-flow/')
    if (res.ok) {
      const result = await res.json()
      flowData.value = result
      isLoading.value = false
      // Pequeno delay para garantir que o DOM renderizou o canvas do gráfico
      setTimeout(() => initChart(result.timeline), 200)
    }
  } catch (error) {
    console.error("Erro ao carregar fluxo de caixa:", error)
  }
}

onMounted(loadData)
const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0)
</script>

<template>
  <SideLayout>
    <div class="page-header">
      <h1>Fluxo de Caixa</h1>
      <p>Previsão do seu saldo para os próximos 30 dias</p>
    </div>

    <div v-if="!isLoading" class="flow-grid">
      <div class="summary-cards">
        <div class="flow-card">
          <span class="label">Saldo Hoje</span>
          <h2 class="val">{{ formatCurrency(flowData.current_balance) }}</h2>
        </div>
        <div class="flow-card highlight">
          <span class="label">Saldo Projetado (30 dias)</span>
          <h2 class="val">{{ formatCurrency(flowData.projected_balance_30d) }}</h2>
        </div>
      </div>

      <div class="chart-container">
        <h3>Evolução Patrimonial Estimada</h3>
        <div ref="chartRef" class="chart-box"></div>
      </div>
    </div>
    
    <div v-else class="loading-container">
       <div class="spinner"></div>
       <p>Calculando projeções baseadas nos seus empréstimos e gastos...</p>
    </div>
    <FooterComp />
  </SideLayout>
</template>

<style scoped>
.page-header { margin-bottom: 30px; }
.page-header h1 { color: var(--text-primary); font-size: 2rem; font-weight: 800; margin-bottom: 5px; }
.page-header p { color: var(--text-secondary); }

.flow-grid { display: flex; flex-direction: column; gap: 25px; }
.summary-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }

.flow-card { 
  background: var(--bg-card); 
  padding: 35px; 
  border-radius: 24px; 
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
}

.flow-card.highlight { 
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
  color: white; 
  border: none;
}

.flow-card.highlight .val { color: #f7b500; }
.flow-card .label { font-size: 0.85rem; text-transform: uppercase; font-weight: 700; opacity: 0.8; letter-spacing: 1px; }
.flow-card .val { font-size: 2.5rem; margin: 15px 0 0 0; font-weight: 900; letter-spacing: -1px; }

.chart-container { 
  background: var(--bg-card); 
  padding: 30px; 
  border-radius: 24px; 
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
}

.chart-container h3 { color: var(--text-primary); margin-bottom: 20px; font-weight: 700; }
.chart-box { width: 100%; height: 400px; }

.loading-container { padding: 100px; text-align: center; color: var(--text-secondary); display: flex; flex-direction: column; align-items: center; gap: 20px; }
.spinner { width: 40px; height: 40px; border: 4px solid var(--border-color); border-top-color: #f7b500; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .summary-cards { grid-template-columns: 1fr; }
}
</style>