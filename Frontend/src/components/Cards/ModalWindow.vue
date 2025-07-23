<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-close" @click="close">×</div>
      <slot>
        <div v-if="loading" class="loading">Загрузка...</div>
        <div v-else class="checkbox-container">
          <div v-for="station in stations" :key="station.id" class="checkbox-wrapper">
            <input
              type="checkbox"
              :id="'station-' + station.id"
              :value="station.id"
              v-model="selectedStations"
              class="round-checkbox"
            />
            <label :for="'station-' + station.id" class="checkbox-label">{{ station.name }}</label>
          </div>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from "../../boot/axios.js";


const { show } = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'update:selected'])
const stations = ref([])
const selectedStations = ref([])
const loading = ref(false)

const fetchStationID = async () => {
  try {
    loading.value = true
    const response = await api.get('/station', {
      headers: {
        'accept': 'application/json'
      }
    })
    stations.value = response.data
  } catch (error) {
    console.error('Ошибка:', error)
    stations.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStationID()
})

const close = () => {
  emit('close')
  emit('update:selected', selectedStations.value)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 80%;
  max-width: 600px;
  min-height: 250px;
  background: #FFFFFF;
  border-radius: 8px;
  padding: 25px;
  position: relative;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.modal-close {
  position: absolute;
  top: 10px;
  right: 15px;
  font-size: 28px;
  cursor: pointer;
  color: #A5A5A5;
}

.modal-close:hover {
  color: #000000;
}

.checkbox-container {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-top: 20px;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.round-checkbox {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border: 2px solid #5c5c5c;
  border-radius: 50%;
  outline: none;
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
}

.round-checkbox:checked {
  background-color: #f4f4f5;
  border-color: #5c5c5c;
}

.round-checkbox:checked::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgb(22, 7, 228);
}



.checkbox-label {
  cursor: pointer;
  user-select: none;
}

.loading {
  text-align: center;
  margin-top: 20px;
  font-size: 16px;
  color: #666;
}
</style>