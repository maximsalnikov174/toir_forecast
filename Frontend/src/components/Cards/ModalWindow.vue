<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-close" @click="close">×</div>
      <slot>
        <div v-if="loading" class="loading">Загрузка...</div>
        <div v-else>
          <div class="checkbox-container">
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
import { ref, onMounted } from 'vue'
import { api } from "../../boot/axios.js";
import { useQuasar } from 'quasar'

const $q = useQuasar()

const { show, serviceWorkId } = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  serviceWorkId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['close', 'update:selected', 'submitted'])
const stations = ref([])
const selectedStations = ref([])
const loading = ref(false)
const submitting = ref(false)
const zvr_number = ref('')

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
    $q.notify({
      type: 'negative',
      message: 'Ошибка при загрузке станций'
    })
  } finally {
    loading.value = false
  }
}

const submit = async () => {
  if (!zvr_number.value || selectedStations.value.length === 0) {
    $q.notify({
      type: 'warning',
      message: 'Заполните все поля'
    })
    return
  }

  try {
    submitting.value = true

    // Убираем пробелы из номера ЗВР
    const cleanZvrNumber = zvr_number.value.replace(/\s/g, '')

    // Отправляем запрос для каждой выбранной станции
    const requests = selectedStations.value.map(stationId =>
      api.patch(`/service_work/add_zvr?service_work_id=${serviceWorkId}&zvr_number=${cleanZvrNumber}&station_id=${stationId}`, null, {
        headers: {
          'accept': 'application/json'
        }
      })
    )

    await Promise.all(requests)

    $q.notify({
      type: 'positive',
      message: 'Данные успешно сохранены'
    })

    emit('submitted')
    close()
  } catch (error) {
    console.error('Ошибка при отправке данных:', error)
    $q.notify({
      type: 'negative',
      message: 'Ошибка при сохранении данных'
    })
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchStationID()
})

const close = () => {
  selectedStations.value = []
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

.input-container {
  margin-top: 20px;
  padding: 0 10px;
}

.submit-btn {
  margin-top: 15px;
  width: 100%;
}
</style>