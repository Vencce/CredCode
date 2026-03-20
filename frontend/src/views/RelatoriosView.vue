<script setup>
import { ref, onMounted, onUnmounted, reactive, nextTick, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
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
const barChartInstance = shallowRef(null)
const lineChartInstance = shallowRef(null)

const summaryData = reactive({
  totalIncome: 0,
  totalExpense: 0,
  balanceEvolution: 0
})

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

const initCharts = (months, incomes, expenses, balances) => {
  if (!barChartRef.value || !lineChartRef.value) return
  
  if (!barChartInstance.value) barChartInstance.value = echarts.init(barChartRef.value)
  if (!lineChartInstance.value) lineChartInstance.value = echarts.init(lineChartRef.value)

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  const textColor = isDark ? '#94a3b8' : '#64748b'
  const gridColor = isDark ? '#1e293b' : '#f1f5f9'

  const barOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['Receitas', 'Despesas'],
      textStyle: { color: textColor },
      bottom: 0
    },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '5%', containLabel: true },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { color: textColor },
      axisLine: { lineStyle: { color: gridColor } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: textColor },
      splitLine: { lineStyle: { color: gridColor, type: 'dashed' } }
    },
    series: [
      {
        name: 'Receitas',
        type: 'bar',
        data: incomes,
        itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] }
      },
      {
        name: 'Despesas',
        type: 'bar',
        data: expenses,
        itemStyle: { color: '#ef4444', borderRadius: [4, 4, 0, 0] }
      }
    ]
  }

  const lineOption = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>Saldo: R$ {c}'
    },
    grid: { left: '3%', right: '4%', bottom: '10%', top: '5%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: months,
      axisLabel: { color: textColor },
      axisLine: { lineStyle: { color: gridColor } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: textColor },
      splitLine: { lineStyle: { color: gridColor, type: 'dashed' } }
    },
    series: [
      {
        data: balances,
        type: 'line',
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(247, 181, 0, 0.4)' },
            { offset: 1, color: 'rgba(247, 181, 0, 0.05)' }
          ])
        },
        itemStyle: { color: '#f7b500' },
        lineStyle: { width: 3 }
      }
    ]
  }

  barChartInstance.value.setOption(barOption)
  lineChartInstance.value.setOption(lineOption)
}

const handleResize = () => {
  if (barChartInstance.value) barChartInstance.value.resize()
  if (lineChartInstance.value) lineChartInstance.value.resize()
}

const handleThemeChange = () => {
  loadData()
}

const loadData = async () => {
  try {
    const expensesRes = await fetchWithAuth('http://localhost:8000/api/finances/expenses/')
    
    if (expensesRes.ok) {
      const data = await expensesRes.json()
      
      const monthMap = {}
      const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
      
      const today = new Date()
      for (let i = 5; i >= 0; i--) {
        const d = new Date(today.getFullYear(), today.getMonth() - i, 1)
        const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
        const label = `${monthNames[d.getMonth()]} ${d.getFullYear()}`
        monthMap[key] = { label, income: 0, expense: 0, balance: 0 }
      }

      let globalIncome = 0
      let globalExpense = 0

      data.forEach(item => {
        const val = parseFloat(item.amount)
        const parts = item.date.split('-')
        const key = `${parts[0]}-${parts[1]}`
        
        if (val >= 0) globalIncome += val
        else globalExpense += Math.abs(val)

        if (monthMap[key]) {
          if (val >= 0) monthMap[key].income += val
          else monthMap[key].expense += Math.abs(val)
        }
      })

      summaryData.totalIncome = globalIncome
      summaryData.totalExpense = globalExpense
      summaryData.balanceEvolution = globalIncome - globalExpense

      const sortedKeys = Object.keys(monthMap).sort()
      const labels = []
      const incomes = []
      const expenses = []
      const balances = []
      
      let runningBalance = 0

      sortedKeys.forEach(key => {
        labels.push(monthMap[key].label)
        incomes.push(monthMap[key].income.toFixed(2))
        expenses.push(monthMap[key].expense.toFixed(2))
        runningBalance += (monthMap[key].income - monthMap[key].expense)
        balances.push(runningBalance.toFixed(2))
      })

      nextTick(() => {
        initCharts(labels, incomes, expenses, balances)
      })
    }
  } catch (error) {
    showToast('Erro ao carregar os dados dos relatórios.', 'error')
  }
}

onMounted(() => {
  const token = localStorage.getItem('access_token')
  if (!token) {
    router.push('/')
  } else {
    isAuthorized.value = true
    loadData()
    window.addEventListener('resize', handleResize)
    window.addEventListener('theme-changed', handleThemeChange)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('theme-changed', handleThemeChange)
  if (barChartInstance.value) barChartInstance.value.dispose()
  if (lineChartInstance.value) lineChartInstance.value.dispose()
})
</script>

<template>
  <ToastMessage v-model:show="toast.show" :message="toast.message" :type="toast.type" />

  <SideLayout v-if="isAuthorized">
    <div class="page-header">
      <div class="header-titles">
        <h1>Relatórios e Análises</h1>
        <p>Acompanhe a evolução gráfica do seu património</p>
      </div>
    </div>

    <div class="summary-cards">
      <div class="card summary-item highlight-card">
        <div class="card-data">
          <h3>Crescimento Patrimonial</h3>
          <span :class="['summary-value', summaryData.balanceEvolution >= 0 ? 'text-positive' : 'text-negative']">
            {{ formatCurrency(summaryData.balanceEvolution) }}
          </span>
        </div>
        <div class="card-icon-wrapper highlight-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"></path><path d="M18 9l-5 5-3-3-5 5"></path></svg>
        </div>
      </div>
      
      <div class="card summary-item">
        <div class="card-data">
          <h3>Total Histórico (Receitas)</h3>
          <span class="summary-value positive">{{ formatCurrency(summaryData.totalIncome) }}</span>
        </div>
        <div class="card-icon-wrapper positive-bg">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
        </div>
      </div>

      <div class="card summary-item">
        <div class="card-data">
          <h3>Total Histórico (Despesas)</h3>
          <span class="summary-value negative">{{ formatCurrency(summaryData.totalExpense) }}</span>
        </div>
        <div class="card-icon-wrapper negative-bg">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>
        </div>
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
          <h2>Evolução do Saldo</h2>
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
.highlight-icon { background-color: rgba(255, 255, 255, 0.1); color: #f7b500; }

.charts-grid { display: flex; flex-direction: column; gap: 30px; margin-bottom: 40px; }

.chart-wrapper { background: var(--bg-card); border-radius: 20px; padding: 30px; box-shadow: var(--shadow-md); border: 1px solid var(--border-color); transition: background-color 0.3s, border-color 0.3s; }
.chart-header { margin-bottom: 20px; }
.chart-header h2 { color: var(--text-primary); font-size: 1.3rem; font-weight: 800; margin: 0 0 5px 0; transition: color 0.3s; }
.chart-header p { color: var(--text-secondary); font-size: 0.95rem; margin: 0; transition: color 0.3s; }
.chart-canvas { width: 100%; height: 350px; }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 15px; }
  .chart-canvas { height: 250px; }
  .chart-wrapper { padding: 20px; }
}
</style>