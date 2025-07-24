<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-close" @click="close">×</div>
      <slot>
        <div v-if="loading" class="loading">Загрузка...</div>
        <div v-else>
          <div class="radio-container">
            <div v-for="station in stations" :key="station.id" class="radio-wrapper">
              <input
                type="radio"
                :id="'station-' + station.id"
                :value="station.id"
                v-model="selectedStation"
                class="round-radio"
                name="station"
              />
              <label :for="'station-' + station.id" class="radio-label">{{ station.name }}</label>
            </div>
          </div>

          <div class="q-pa-md input-container">
            <div class="q-gutter-md">
              <q-input
                filled
                v-model="zvr_number"
                label="Укажите 7 последних цифр №ЗВР"
                mask="# # # # # # #"
                fill-mask
              />
            </div>
            <q-btn
              class="submit-btn"
              color="primary"
              label="Внести"
              @click="submit"
              :loading="submitting"
              :disable="submitting"
            />
          </div>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue' // Убрали onMounted, добавили watch
import { api } from '../../boot/axios.js'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'src/stores/useAuthStore'

const $q = useQuasar()
const authStore = useAuthStore()

const { show, serviceWorkId } = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  serviceWorkId: {
    type: [String, Number],
    required: true,
  },
})

const emit = defineEmits(['close', 'update:selected', 'submitted'])
const stations = ref([])
const selectedStation = ref(null)
const loading = ref(false)
const submitting = ref(false)
const zvr_number = ref('')

// Добавляем watcher для пропса show
watch(() => show, (newVal) => {
  if (newVal) {
    fetchStationID()
  }
})

const fetchStationID = async () => {
  try {
    loading.value = true
    const response = await api.get('/station', {
      headers: {
        accept: 'application/json',
      },
    })
    stations.value = response.data
  } catch (error) {
    console.error('Ошибка:', error)
    stations.value = []
    $q.notify({
      type: 'negative',
      message: 'Ошибка при загрузке станций',
    })
  } finally {
    loading.value = false
  }
}

const submit = async () => {
  if (!zvr_number.value || !selectedStation.value) {
    $q.notify({
      type: 'warning',
      message: 'Заполните все поля',
    })
    return
  }

  try {
    submitting.value = true

    // Убираем пробелы из номера ЗВР
    const cleanZvrNumber = zvr_number.value.replace(/\s/g, '')

    // Отправляем запрос с выбранной станцией
    await api.patch(
      `/service_work/add_zvr`,
      {
        service_work_id: serviceWorkId,
        zvr_number: cleanZvrNumber,
        station_id: selectedStation.value,
      },
      {
        headers: {
          accept: 'application/json',
          Authorization: `Bearer ${authStore.token}`,
          'Content-Type': 'application/json',
        },
      },
    )

    $q.notify({
      type: 'positive',
      message: 'Данные успешно сохранены',
    })

    emit('submitted')
    close()
  } catch (error) {
    console.error('Ошибка при отправке данных:', error)
    $q.notify({
      type: 'negative',
      message: error.response?.data?.detail || 'Ошибка при сохранении данных',
    })

    if (error.response && error.response.status === 401) {
      authStore.clearAuthData()
    }
  } finally {
    submitting.value = false
  }
}


const close = () => {
  selectedStation.value = null
  zvr_number.value = ''
  emit('close')
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
  background: #ffffff;
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
  color: #a5a5a5;
}

.modal-close:hover {
  color: #000000;
}

.radio-container {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-top: 20px;
}

.radio-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.round-radio {
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

.round-radio:checked {
  border-color: #5c5c5c;
}

.round-radio:checked::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgb(22, 7, 228);
}

.radio-label {
  cursor: pointer;
  user-select: none;
}

.loading {
  text-align: center;
  margin-top: 20px;
  font-size: 16px;
  color: #666;
}

.input-container {
  margin-top: 20px;
  padding: 0 10px;
}

.submit-btn {
  margin-top: 15px;
  width: 100%;
}
</style>
