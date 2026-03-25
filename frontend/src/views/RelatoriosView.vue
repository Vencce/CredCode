<script setup>
import { ref, onMounted, onUnmounted, reactive, nextTick, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import jsPDF from 'jspdf'
import 'jspdf-autotable'
import ToastMessage from '../components/ToastMessage.vue'
import SideLayout from '../components/SideLayout.vue'
import FooterComp from '../components/FooterComp.vue'

const router = useRouter()
const isAuthorized = ref(false)

const toast = reactive({
  show: false,
  message: '',
  type: 'error'
})

const barChartRef = ref(null)
const lineChartRef = ref(null)
const projectionChartRef = ref(null)

const barChartInstance = shallowRef(null)
const lineChartInstance = shallowRef(null)
const projectionChartInstance = shallowRef(null)

const summaryData = reactive({
  totalIncome: 0,
  totalExpense: 0,
  balanceEvolution: 0,
  projected30d: 0
})

const rawData = ref([])

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  toast.show = true
}

const fetchWithAuth = async (url, options = {}) => {
  let token = localStorage.getItem('access_token')
  let headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  }
  
  let response = await fetch(url, { ...options, headers })
  
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      try {
        const refreshResponse = await fetch('http://localhost:8000/api/auth/refresh/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: refreshToken })
        })
        
        if (refreshResponse.ok) {
          const data = await refreshResponse.json()
          localStorage.setItem('access_token', data.access)
          headers['Authorization'] = `Bearer ${data.access}`
          response = await fetch(url, { ...options, headers })
        } else {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('has_profile')
          router.push('/')
        }
      } catch (e) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('has_profile')
        router.push('/')
      }
    } else {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('has_profile')
      router.push('/')
    }
  }
  return response
}

const formatCurrency = (value) => {
  const numValue = parseFloat(value) || 0
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numValue)
}

const exportToPDF = () => {
  const doc = new jsPDF()
  const today = new Date().toLocaleDateString('pt-BR')

  doc.setFontSize(22)
  doc.setTextColor(15, 23, 42)
  doc.text('Relatório Financeiro - CredCode', 20, 20)
  
  doc.setFontSize(10)
  doc.setTextColor(100)
  doc.text(`Gerado em: ${today}`, 20, 28)

  doc.setDrawColor(241, 245, 249)
  doc.line(20, 35, 190, 35)

  doc.setFontSize(14)
  doc.setTextColor(15, 23, 42)
  doc.text('Resumo Patrimonial', 20, 45)

  const summaryRows = [
    ['Crescimento Patrimonial', formatCurrency(summaryData.balanceEvolution)],
    ['Previsão (30 dias)', formatCurrency(summaryData.projected30d)],
    ['Total Histórico Receitas', formatCurrency(summaryData.totalIncome)],
    ['Total Histórico Despesas', formatCurrency(summaryData.totalExpense)]
  ]

  doc.autoTable({
    startY: 50,
    head: [['Indicador', 'Valor']],
    body: summaryRows,
    theme: 'grid',
    headStyles: { fillColor: [15, 23, 42], textColor: [255, 255, 255] },
    margin: { left: 20, right: 20 }
  })

  doc.text('Últimas Transações Analisadas', 20, doc.lastAutoTable.finalY + 15)

  const transactionRows = rawData.value.slice(0, 15).map(t => [
    t.date.split('-').reverse().join('/'),
    t.description.replace(/\[.*?\]\s?/, ''),
    t.category,
    formatCurrency(t.amount)
  ])

  doc.autoTable({
    startY: doc.lastAutoTable.finalY + 20,
    head: [['Data', 'Descrição', 'Categoria', 'Valor']],
    body: transactionRows,
    theme: 'striped',
    headStyles: { fillColor: [247, 181, 0], textColor: [15, 23, 42] },
    margin: { left: 20, right: 20 }
  })

  doc.save(`CredCode_Relatorio_${today.replace(/\//g, '-')}.pdf`)
  showToast('PDF gerado com sucesso!', 'success')
}

const initCharts = (months, incomes, expenses, balances, projectionTimeline) => {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  const textColor = isDark ? '#94a3b8' : '#64748b'
  const gridColor = isDark ? '#1e293b' : '#f1f5f9'

  if (barChartRef.value) {
    barChartInstance.value = echarts.init(barChartRef.value)
    barChartInstance.value.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: ['Receitas', 'Despesas'], textStyle: { color: textColor }, bottom: 0 },
      grid: { left: '3%', right: '4%', bottom: '15%', top: '5%', containLabel: true },
      xAxis: { type: 'category', data: months, axisLabel: { color: textColor }, axisLine: { lineStyle: { color: gridColor } } },
      yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } },
      series: [
        { name: 'Receitas', type: 'bar', data: incomes, itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] } },
        { name: 'Despesas', type: 'bar', data: expenses, itemStyle: { color: '#ef4444', borderRadius: [4, 4, 0, 0] } }
      ]
    })
  }

  if (lineChartRef.value) {
    lineChartInstance.value = echarts.init(lineChartRef.value)
    lineChartInstance.value.setOption({
      tooltip: { trigger: 'axis', formatter: '{b}<br/>Saldo: R$ {c}' },
      grid: { left: '3%', right: '4%', bottom: '10%', top: '5%', containLabel: true },
      xAxis: { type: 'category', boundaryGap: false, data: months, axisLabel: { color: textColor }, axisLine: { lineStyle: { color: gridColor } } },
      yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } },
      series: [{ data: balances, type: 'line', smooth: true, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(247, 181, 0, 0.4)' }, { offset: 1, color: 'rgba(247, 181, 0, 0.05)' }]) }, itemStyle: { color: '#f7b500' }, lineStyle: { width: 3 } }]
    })
  }

  if (projectionChartRef.value) {
    projectionChartInstance.value = echarts.init(projectionChartRef.value)
    projectionChartInstance.value.setOption({
      tooltip: { trigger: 'axis', formatter: '{b}<br/>Projeção: R$ {c}' },
      grid: { left: '3%', right: '4%', bottom: '10%', top: '5%', containLabel: true },
      xAxis: { type: 'category', boundaryGap: false, data: projectionTimeline.map(t => t.date), axisLabel: { color: textColor }, axisLine: { lineStyle: { color: gridColor } } },
      yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } },
      series: [{
        data: projectionTimeline.map(t => t.balance),
        type: 'line', smooth: true,
        itemStyle: { color: '#10b981' },
        lineStyle: { width: 3 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(16, 185, 129, 0.3)' }, { offset: 1, color: 'rgba(16, 185, 129, 0)' }]) }
      }]
    })
  }
}

const handleResize = () => {
  barChartInstance.value?.resize()
  lineChartInstance.value?.resize()
  projectionChartInstance.value?.resize()
}

const handleThemeChange = () => {
  loadData()
}

const loadData = async () => {
  try {
    const [expensesRes, flowRes] = await Promise.all([
      fetchWithAuth('http://localhost:8000/api/finances/expenses/'),
      fetchWithAuth('http://localhost:8000/api/finances/cash-flow/')
    ])
    
    if (expensesRes.ok && flowRes.ok) {
      const data = await expensesRes.json()
      const flow = await flowRes.json()
      
      rawData.value = data

      const monthMap = {}
      const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
      const today = new Date()
      for (let i = 5; i >= 0; i--) {
        const d = new Date(today.getFullYear(), today.getMonth() - i, 1)
        const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
        monthMap[key] = { label: `${monthNames[d.getMonth()]} ${d.getFullYear()}`, income: 0, expense: 0 }
      }

      let globalIncome = 0; let globalExpense = 0
      data.forEach(item => {
        const val = parseFloat(item.amount); const key = item.date.substring(0, 7)
        if (val >= 0) globalIncome += val; else globalExpense += Math.abs(val)
        if (monthMap[key]) { if (val >= 0) monthMap[key].income += val; else monthMap[key].expense += Math.abs(val) }
      })

      summaryData.totalIncome = globalIncome
      summaryData.totalExpense = globalExpense
      summaryData.balanceEvolution = globalIncome - globalExpense
      summaryData.projected30d = flow.projected_balance_30d

      const sortedKeys = Object.keys(monthMap).sort()
      const labels = []; const incomes = []; const expenses = []; const balances = []
      let runningBalance = 0
      sortedKeys.forEach(key => {
        labels.push(monthMap[key].label); incomes.push(monthMap[key].income.toFixed(2)); expenses.push(monthMap[key].expense.toFixed(2))
        runningBalance += (monthMap[key].income - monthMap[key].expense); balances.push(runningBalance.toFixed(2))
      })

      nextTick(() => initCharts(labels, incomes, expenses, balances, flow.timeline))
    }
  } catch (error) {
    showToast('Erro ao carregar os dados.', 'error')
  }
}

onMounted(() => {
  const token = localStorage.getItem('access_token')
  if (!token) router.push('/'); else {
    isAuthorized.value = true; loadData()
    window.addEventListener('resize', handleResize)
    window.addEventListener('theme-changed', handleThemeChange)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('theme-changed', handleThemeChange)
  barChartInstance.value?.dispose(); lineChartInstance.value?.dispose(); projectionChartInstance.value?.dispose()
})
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />

  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Relatórios e Análises</h1>
        <p>Acompanhe a evolução histórica e as previsões futuras</p>
      </div>
      <button @click="exportToPDF" class="export-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
        Exportar PDF
      </button>
    </div>

    <div class="summary-cards">
      <div class="card summary-item highlight-card">
        <div class="card-data">
          <h3>Crescimento Patrimonial</h3>
          <span :class="['summary-value', summaryData.balanceEvolution >= 0 ? 'text-positive' : 'text-negative']">
            {{ formatCurrency(summaryData.balanceEvolution) }}
          </span>
        </div>
        <div class="card-icon-wrapper highlight-icon">📈</div>
      </div>
      
      <div class="card summary-item">
        <div class="card-data">
          <h3>Previsão (Próximos 30 dias)</h3>
          <span :class="['summary-value', summaryData.projected30d >= 0 ? 'text-positive' : 'text-negative']">
            {{ formatCurrency(summaryData.projected30d) }}
          </span>
        </div>
        <div class="card-icon-wrapper positive-bg">🔮</div>
      </div>

      <div class="card summary-item">
        <div class="card-data">
          <h3>Total Histórico (Receitas)</h3>
          <span class="summary-value positive">{{ formatCurrency(summaryData.totalIncome) }}</span>
        </div>
        <div class="card-icon-wrapper positive-bg">↗</div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-wrapper">
        <div class="chart-header">
          <h2>Comparativo Mensal</h2>
          <p>Receitas versus Despesas nos últimos 6 meses</p>
        </div>
        <div ref="barChartRef" class="chart-canvas"></div>
      </div>

      <div class="chart-wrapper">
        <div class="chart-header">
          <h2>Tendência de Saldo Futuro</h2>
          <p>Projeção para os próximos 30 dias</p>
        </div>
        <div ref="projectionChartRef" class="chart-canvas"></div>
      </div>

      <div class="chart-wrapper">
        <div class="chart-header">
          <h2>Evolução do Saldo Histórico</h2>
          <p>Acumulação do seu saldo ao longo do semestre</p>
        </div>
        <div ref="lineChartRef" class="chart-canvas"></div>
      </div>
    </div>

    <FooterComp />
  </SideLayout>
</template>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.header-titles h1 { color: var(--text-primary); font-size: 2rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.5px; transition: color 0.3s; }
.header-titles p { color: var(--text-secondary); margin: 0; font-size: 1.05rem; transition: color 0.3s; }

.export-btn { 
  display: flex; 
  align-items: center; 
  gap: 10px; 
  padding: 12px 20px; 
  background: #0f172a; 
  color: white; 
  border: none; 
  border-radius: 12px; 
  font-weight: 700; 
  cursor: pointer; 
  transition: 0.3s;
}
.export-btn:hover { background: #1e293b; transform: translateY(-2px); }

.summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 35px; }
.card { background: var(--bg-card); padding: 25px 30px; border-radius: 20px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.3s, border-color 0.3s; }
.card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.highlight-card { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: none; }
.highlight-card .card-data h3 { color: #94a3b8; }
.card-data h3 { color: var(--text-secondary); font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 8px 0; transition: color 0.3s; }
.summary-value { font-size: 1.8rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; color: var(--text-primary); display: block; transition: color 0.3s; }
.text-positive { color: #34d399; }
.text-negative { color: #f87171; }
.positive { color: #059669; }
.negative { color: #dc2626; }
.card-icon-wrapper { width: 60px; height: 60px; border-radius: 16px; display: flex; align-items: center; justify-content: center; }
.positive-bg { background-color: var(--positive-bg); color: #10b981; }
.negative-bg { background-color: var(--negative-bg); color: #ef4444; }
.highlight-icon { background-color: rgba(255, 255, 255, 0.1); color: #f7b500; font-size: 1.5rem; }
.charts-grid { display: flex; flex-direction: column; gap: 30px; margin-bottom: 40px; }
.chart-wrapper { background: var(--bg-card); border-radius: 20px; padding: 30px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); transition: background-color 0.3s, border-color 0.3s; }
.chart-header { margin-bottom: 20px; }
.chart-header h2 { color: var(--text-primary); font-size: 1.3rem; font-weight: 800; margin: 0 0 5px 0; transition: color 0.3s; }
.chart-header p { color: var(--text-secondary); font-size: 0.95rem; margin: 0; transition: color 0.3s; }
.chart-canvas { width: 100%; height: 350px; }
@media (max-width: 768px) { .page-header { flex-direction: column; align-items: flex-start; gap: 15px; } .chart-canvas { height: 250px; } .chart-wrapper { padding: 20px; } }
</style>