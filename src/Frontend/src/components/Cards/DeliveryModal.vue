<template>
  <q-dialog v-model="showModal" persistent>
    <q-card class="delivery-modal">
      <!-- Навигация между доставками -->
      <q-card-section v-if="hasMultipleDeliveries" class="navigation-section">
        <div class="navigation-controls">
          <q-btn
            icon="chevron_left"
            color="primary"
            @click="prevDelivery"
            :disable="currentDeliveryIndex === 0"
            round
            dense
          />
          <div class="navigation-info">
            Доставка {{ currentDeliveryIndex + 1 }} из {{ deliveries.length }}
          </div>
          <q-btn
            icon="chevron_right"
            color="primary"
            @click="nextDelivery"
            :disable="currentDeliveryIndex === deliveries.length - 1"
            round
            dense
          />
        </div>
      </q-card-section>

      <q-card-section class="header-section">
        <div class="header-content">
          <div class="delivery-info">
            <div class="delivery-title">
              Доставка №{{ currentDelivery.delivery }}
              <span v-if="hasMultipleDeliveries" class="delivery-counter">
                ({{ currentDeliveryIndex + 1 }} из {{ deliveries.length }})
              </span>
            </div>
            <div class="zvr-number" v-if="zvr_number">
              <span class="zvr-label">ЗВР:</span> {{ zvr_number }}
            </div>
            <div class="delivery-details">
              <div>От организации: {{ fromOrganizationName }}</div>
              <div>ID работы: {{ currentDelivery.service_work_id }}</div>
            </div>
          </div>
          <div class="barcode-section">
            <div class="barcode-label">Штрих-код:</div>
            <canvas ref="barcodeCanvas" class="barcode-canvas"></canvas>
          </div>
        </div>
      </q-card-section>

      <q-card-section class="q-pt-none delivery-content">
        <table class="delivery-table bordered-table">
          <thead>
            <tr>
              <th class="cell-border">СНБ</th>
              <th class="cell-border">Наименование материала</th>
              <th class="cell-border">Количество</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in currentDelivery.components"
              :key="index"
              :class="{ 'active-row': currentRowIndex === index && currentCellIndex >= 0 }"
              @click="handleRowClick(index, $event)"
            >
              <td
                class="cell-border"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 0,
                  'copied-cell': copiedCells.has(`${index}-0`),
                }"
              >
                {{ item.snb }}
              </td>
              <td
                class="cell-border"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 1,
                  'copied-cell': copiedCells.has(`${index}-1`),
                }"
              >
                {{ item.material_name }}
              </td>
              <td
                class="cell-border text-center"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 2,
                  'copied-cell': copiedCells.has(`${index}-2`),
                }"
              >
                {{ item.material_count }}
              </td>
            </tr>
            <tr v-if="!currentDelivery.components || currentDelivery.components.length === 0">
              <td colspan="3" class="cell-border text-center text-grey">
                Нет данных о компонентах
              </td>
            </tr>
          </tbody>
        </table>
      </q-card-section>

      <q-card-section class="copy-status" v-if="copyStatus">
        {{ copyStatus }}
      </q-card-section>

      <q-card-actions align="right">
        <q-btn label="Закрыть" color="primary" @click="closeModal" />
        <q-btn
          label="Сбросить выделение"
          color="secondary"
          @click="resetCopiedCells"
          v-if="copiedCells.size > 0"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import JsBarcode from 'jsbarcode'
import { deliveryService } from '../Functions/deliveryService'

const $q = useQuasar()
const showModal = ref(false)
const currentRowIndex = ref(-1)
const currentCellIndex = ref(-1)
const copyStatus = ref('')
const barcodeCanvas = ref(null)
const copiedCells = ref(new Set())
const currentDeliveryIndex = ref(0)

const emit = defineEmits(['close', 'update:modelValue'])

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  deliveryData: {
    type: [Object, Array],
    default: () => ({}),
  },
  barCode: {
    type: String,
    default: '',
  },
  zvr_number: {
    type: String,
    default: '',
  },
})

// Вычисляемое свойство для массива доставок
const deliveries = computed(() => {
  if (Array.isArray(props.deliveryData)) {
    return props.deliveryData
  } else if (props.deliveryData && Object.keys(props.deliveryData).length > 0) {
    return [props.deliveryData]
  }
  return []
})

// Проверка на наличие нескольких доставок
const hasMultipleDeliveries = computed(() => {
  return deliveries.value.length > 1
})

// Текущая доставка
const currentDelivery = computed(() => {
  return deliveries.value[currentDeliveryIndex.value] || {}
})

// Вычисляемое свойство для названия организации
const fromOrganizationName = computed(() => {
  return deliveryService.getOrganizationName(currentDelivery.value.from_organization)
})

// Вычисляемое свойство для штрих-кода
const barcodeValue = computed(() => {
  return currentDelivery.value.bar_code || props.barCode || 'NO_DATA'
})

// Синхронизируем значение модального окна
watch(
  () => props.modelValue,
  (value) => {
    showModal.value = value
    if (value) {
      generateBarcode()
    } else {
      resetAllStates()
    }
  },
)

watch(showModal, (value) => {
  if (value !== props.modelValue) {
    emit('update:modelValue', value)
  }
  if (!value) {
    resetAllStates()
  }
})

// Переключение на следующую доставку
const nextDelivery = () => {
  if (currentDeliveryIndex.value < deliveries.value.length - 1) {
    currentDeliveryIndex.value++
    resetCopiedCells()
    generateBarcode()
  }
}

// Переключение на предыдущую доставку
const prevDelivery = () => {
  if (currentDeliveryIndex.value > 0) {
    currentDeliveryIndex.value--
    resetCopiedCells()
    generateBarcode()
  }
}

// Функция для генерации штрих-кода
const generateBarcode = () => {
  nextTick(() => {
    if (barcodeCanvas.value && barcodeValue.value) {
      try {
        JsBarcode(barcodeCanvas.value, barcodeValue.value, {
          format: 'CODE128',
          width: 2,
          height: 60,
          displayValue: true,
          margin: 10,
          fontSize: 16,
          textMargin: 5,
        })
      } catch (error) {
        console.error('Ошибка генерации штрих-кода:', error)
      }
    }
  })
}

// Сброс всех состояний
const resetAllStates = () => {
  currentRowIndex.value = -1
  currentCellIndex.value = -1
  copyStatus.value = ''
  copiedCells.value.clear()
  currentDeliveryIndex.value = 0
}

// Обработчик клика по строке таблицы
const handleRowClick = (rowIndex) => {
  if (rowIndex !== currentRowIndex.value) {
    currentRowIndex.value = rowIndex
    currentCellIndex.value = 0
  } else {
    currentCellIndex.value = (currentCellIndex.value + 1) % 3
  }

  const cellValue = getCellValue(rowIndex, currentCellIndex.value)
  copyToClipboard(cellValue)

  const cellId = `${rowIndex}-${currentCellIndex.value}`
  copiedCells.value.add(cellId)
}

// Сброс выделения скопированных ячеек
const resetCopiedCells = () => {
  copiedCells.value.clear()
  currentCellIndex.value = -1
  currentRowIndex.value = -1
}

// Получение значения ячейки
const getCellValue = (rowIndex, cellIndex) => {
  const component = currentDelivery.value.components?.[rowIndex]
  if (!component) return ''

  switch (cellIndex) {
    case 0:
      return component.snb || ''
    case 1:
      return component.material_name || ''
    case 2:
      return component.material_count?.toString() || ''
    default:
      return ''
  }
}

// Копирование текста в буфер обмена
const copyToClipboard = (text) => {
  if (!text) return

  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.top = '0'
  textArea.style.left = '0'
  textArea.style.opacity = '0'

  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()

  try {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).catch(fallbackCopy)
    } else {
      fallbackCopy()
    }
  } catch {
    fallbackCopy()
  } finally {
    document.body.removeChild(textArea)
  }
}

// Fallback метод копирования
const fallbackCopy = () => {
  try {
    document.execCommand('copy')
  } catch {
    showNotify({
      type: 'negative',
      message: 'Не удалось скопировать текст',
      timeout: 3000,
    })
  }
}

const showNotify = (options) => {
  $q.notify(options)
}

const closeModal = () => {
  showModal.value = false
  emit('close')
}

// Следим за изменениями в данных доставки
watch(
  () => props.deliveryData,
  () => {
    currentDeliveryIndex.value = 0
    generateBarcode()
  },
  { deep: true },
)

onMounted(() => {
  if (props.modelValue) {
    generateBarcode()
  }
})
</script>

<style scoped>
.delivery-modal {
  min-width: 1000px;
  max-width: 95vw;
  max-height: 80vh;
}

.header-section {
  background-color: #f5f5f5;
  border-bottom: 1px solid #ddd;
  padding: 16px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.delivery-info {
  flex: 1;
}

.delivery-title {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
}

.delivery-counter {
  font-size: 16px;
  color: #666;
  font-weight: normal;
}

.zvr-number {
  font-size: 16px;
  font-weight: 600;
  color: #35f51c;
  margin-bottom: 8px;
  border-radius: 4px;
  display: inline-block;
}

.zvr-label {
  color: black;
}

.delivery-details {
  font-size: 14px;
  color: #666;
}

.delivery-details div {
  margin-bottom: 4px;
}

.barcode-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.barcode-label {
  font-size: 16px;
  font-weight: 700;
  color: red;
}

.barcode-canvas {
  height: 90px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.navigation-section {
  padding: 10px 16px;
  background-color: #f0f0f0;
  border-bottom: 1px solid #ddd;
}

.navigation-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.navigation-info {
  font-weight: 600;
  color: #333;
}

.delivery-content {
  max-height: 50vh;
  overflow-y: auto;
  padding: 0;
}

/* Стили для таблицы */
.bordered-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Inter', sans-serif;
  border: 2px solid #ddd;
}

.bordered-table th,
.bordered-table td {
  border: 1px solid #bdbdbd;
  padding: 16px 12px;
  font-size: 14px;
  vertical-align: middle;
  min-height: 50px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.bordered-table th {
  background-color: #e0e0e0;
  font-weight: bold;
  text-align: left;
  position: sticky;
  top: 0;
  z-index: 1;
  font-size: 15px;
  padding: 18px 12px;
  cursor: default;
}

.bordered-table th.cell-border {
  border-bottom: 2px solid #9e9e9e;
}

.bordered-table td.cell-border {
  border: 1px solid #bdbdbd;
}

.bordered-table tr:hover {
  background-color: #f5f5f5;
}

.bordered-table th:nth-child(3),
.bordered-table td:nth-child(3) {
  text-align: center;
  width: 100px;
}

/* Чередование цветов строк */
.bordered-table tr:nth-child(even) {
  background-color: #fafafa;
}

.bordered-table tr:nth-child(even):hover {
  background-color: #f0f0f0;
}

/* Стили для активной строки и ячейки */
.active-row {
  background-color: #e3f2fd !important;
}

.active-cell {
  background-color: #bbdefb !important;
  font-weight: bold;
}

/* Стили для скопированных ячеек */
.copied-cell {
  background-color: #c8e6c9 !important;
  border: 2px solid #4caf50 !important;
  font-weight: bold;
  position: relative;
}

.copied-cell::after {
  content: '✓';
  position: absolute;
  top: 2px;
  right: 2px;
  color: #4caf50;
  font-weight: bold;
  font-size: 12px;
}

.text-center {
  text-align: center;
}

.text-grey {
  color: #9e9e9e;
  font-style: italic;
}

.cell-border {
  border: 1px solid #bdbdbd !important;
}

.copy-status {
  background-color: #e8f5e9;
  color: #2e7d32;
  padding: 8px 16px;
  border-radius: 4px;
  margin: 10px 16px;
  font-weight: 500;
  text-align: center;
}
</style>
