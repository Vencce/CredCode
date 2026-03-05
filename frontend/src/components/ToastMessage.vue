<script setup>
import { watch } from 'vue'

const props = defineProps({
  show: Boolean,
  message: String,
  type: {
    type: String,
    default: 'error'
  }
})

const emit = defineEmits(['update:show'])

let timeoutId

watch(() => props.show, (newVal) => {
  if (newVal) {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      emit('update:show', false)
    }, 4000)
  }
})

const close = () => {
  emit('update:show', false)
}
</script>

<template>
  <Transition name="toast">
    <div v-if="show" :class="['toast-container', type]">
      <div class="toast-content">
        <span class="message">{{ message }}</span>
      </div>
      <button @click="close" class="close-btn">&times;</button>
    </div>
  </Transition>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 30px;
  right: 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 320px;
  padding: 18px 24px;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  font-family: 'Inter', sans-serif;
}

.toast-container.error {
  background-color: #fee2e2;
  border-left: 6px solid #ef4444;
  color: #991b1b;
}

.toast-container.success {
  background-color: #dcfce7;
  border-left: 6px solid #22c55e;
  color: #166534;
}

.toast-content {
  flex: 1;
}

.message {
  font-weight: 600;
  font-size: 0.95rem;
  line-height: 1.4;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: inherit;
  margin-left: 15px;
  opacity: 0.6;
  transition: opacity 0.3s;
}

.close-btn:hover {
  opacity: 1;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(50px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(50px);
}
</style>