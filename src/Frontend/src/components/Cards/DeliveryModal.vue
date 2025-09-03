<template>
  <q-dialog v-model="showModal" persistent>
    <q-card class="delivery-modal">
      <!-- Крестик закрытия в правом верхнем углу -->
      <q-btn class="close-button" icon="close" flat round dense @click="closeModal" v-close-popup />

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
            <span v-if="isDeliveryBlocked || isViewOnly" class="blocked-label">(только просмотр)</span>
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
              <span v-if="isDeliveryBlocked || isViewOnly" class="blocked-badge">ТОЛЬКО ПРОСМОТР</span>
              <span v-if="showTransferWarning" class="transfer-warning">ТРЕБУЕТСЯ ПЕРЕМЕЩЕНИЕ</span>
            </div>
            <div class="zvr-number" v-if="zvr_number">
              <span class="zvr-label">ЗВР:</span> {{ zvr_number }}
            </div>
            <div class="delivery-details">
              <div>организация получатель: {{ currentDelivery.organization?.name }}</div>
              <div>ID работы: {{ currentDelivery.service_work_id }}</div>
              <div>ID карточки: {{ currentDelivery.id }}</div>
            </div>
          </div>
          <div class="barcode-section">
            <div class="barcode-label">Штрих-код:</div>
            <canvas ref="barcodeCanvas" class="barcode-canvas"></canvas>
          </div>
        </div>
      </q-card-section>

      <q-card-section
        class="q-pt-none delivery-content"
        @click="!isDeliveryBlocked && !isViewOnly && handleTableClick()"
      >
        <table class="delivery-table bordered-table">
          <thead>
            <tr>
              <th class="cell-border">СНБ</th>
              <th class="cell-border">Количество</th>
              <th class="cell-border">Наименование материала</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in currentDelivery.components"
              :key="index"
              :class="{
                'active-row': currentRowIndex === index && !isDeliveryBlocked && !isViewOnly,
                'blocked-row': isDeliveryBlocked || isViewOnly,
              }"
            >
              <td
                class="cell-border"
                :class="{
                  'active-cell':
                    currentRowIndex === index && currentCellIndex === 0 && !isDeliveryBlocked && !isViewOnly,
                  'copied-cell': copiedCells.has(`${index}-0`) && !isDeliveryBlocked && !isViewOnly,
                  'blocked-cell': isDeliveryBlocked || isViewOnly,
                }"
              >
                {{ item.snb }}
              </td>
              <td
                class="cell-border text-center"
                :class="{
                  'active-cell':
                    currentRowIndex === index && currentCellIndex === 1 && !isDeliveryBlocked && !isViewOnly,
                  'copied-cell': copiedCells.has(`${index}-1`) && !isDeliveryBlocked && !isViewOnly,
                  'blocked-cell': isDeliveryBlocked || isViewOnly,
                }"
              >
                {{ item.material_count }}
              </td>

              <td
                class="cell-border"
                :class="{
                  'blocked-cell': isDeliveryBlocked || isViewOnly,
                }"
              >
                {{ item.material_name }}
              </td>
            </tr>
            <tr v-if="!currentDelivery.components || currentDelivery.components.length === 0">
              <td colspan="4" class="cell-border text-center text-grey">
                Нет данных о компонентах
              </td>
            </tr>
          </tbody>
        </table>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn
          label="Сбросить выделение"
          color="secondary"
          @click="resetCopiedCells"
          v-if="copiedCells.size > 0 && !isDeliveryBlocked && !isViewOnly"
          :disable="isDeliveryBlocked || isViewOnly"
        />

        <q-btn
          label="Внесено"
          color="positive"
          @click="handleMarkAsEntered"
          v-if="allCellsCopied && !isDeliveryBlocked && !isViewOnly"
          :disable="isDeliveryBlocked || isViewOnly || isMarkingAsEntered"
          :loading="isMarkingAsEntered"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import JsBarcode from 'jsbarcode'
import { useDeliveryActions } from 'src/components/Functions/useDeliveryActions'
import { storeToRefs } from 'pinia'
import { useAuthStore } from 'src/stores/useAuthStore';

const $q = useQuasar()
const showModal = ref(false)
const currentRowIndex = ref(-1)
const currentCellIndex = ref(-1)
const copyStatus = ref('')
const barcodeCanvas = ref(null)
const copiedCells = ref(new Set())
const currentDeliveryIndex = ref(0)

const emit = defineEmits(['close', 'update:modelValue', 'entered', 'refreshData'])

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

const authStore = useAuthStore()
const { user } = storeToRefs(authStore)

// Проверка роли пользователя (только просмотр для role_id = 4)
const isViewOnly = computed(() => {
  return user.value?.role_id === 4 || user.value?.role_id === 2
})

const {
  isMarkingAsEntered,
  markAsEntered: markDeliveryAsEntered,
  resetEnteredDeliveries,
  enteredDeliveries,
} = useDeliveryActions()

// Проверка, заблокирована ли текущая доставка
const isDeliveryBlocked = computed(() => {
  return currentDelivery.value.to_insert === true
})

// Проверка, требуется ли перемещение (для role_id = 4)
const showTransferWarning = computed(() => {
  return user.value?.role_id === 5 && currentDelivery.value.transfer === true
})

// Вычисляемое свойство для массива доставок (обновлено для нового формата)
const deliveries = computed(() => {
  // Если пришел массив - возвращаем его (старый формат)
  if (Array.isArray(props.deliveryData)) {
    return props.deliveryData
  }

  // Если пришел объект с docs_in_service_work (новый формат)
  if (props.deliveryData && props.deliveryData.docs_in_service_work) {
    return Array.isArray(props.deliveryData.docs_in_service_work)
      ? props.deliveryData.docs_in_service_work
      : [props.deliveryData.docs_in_service_work]
  }

  // Если пришел пустой объект или другой формат
  if (props.deliveryData && Object.keys(props.deliveryData).length > 0) {
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

// Вычисляемое свойство для штрих-кода
const barcodeValue = computed(() => {
  return currentDelivery.value.bar_code || props.barCode || 'NO_DATA'
})

// Находим следующую ячейку для копирования
const findNextCellToCopy = () => {
  if (!currentDelivery.value.components || isViewOnly.value) return null

  for (let rowIndex = 0; rowIndex < currentDelivery.value.components.length; rowIndex++) {
    for (let cellIndex = 0; cellIndex < 2; cellIndex++) {
      const cellId = `${rowIndex}-${cellIndex}`
      if (!copiedCells.value.has(cellId)) {
        return { rowIndex, cellIndex }
      }
    }
  }
  return null
}

// Проверяем, все ли ячейки текущей доставки скопированы
const allCellsCopied = computed(() => {
  if (!currentDelivery.value.components || currentDelivery.value.components.length === 0 || isDeliveryBlocked.value || isViewOnly.value) {
    return false
  }

  const totalCells = currentDelivery.value.components.length * 2
  return copiedCells.value.size >= totalCells && !enteredDeliveries.value.has(currentDelivery.value.delivery)
})

// Обработчик клика по таблице
const handleTableClick = () => {
  if (isDeliveryBlocked.value || isViewOnly.value) return

  const nextCell = findNextCellToCopy()
  if (!nextCell) {
    // Все ячейки уже скопированы
    showNotify({
      type: 'info',
      message: 'Все ячейки уже скопированы',
      timeout: 2000,
    })
    return
  }

  // Устанавливаем текущую ячейку
  currentRowIndex.value = nextCell.rowIndex
  currentCellIndex.value = nextCell.cellIndex

  // Копируем ячейку
  const cellValue = getCellValue(nextCell.rowIndex, nextCell.cellIndex)
  copyToClipboard(cellValue)

  // Помечаем как скопированную
  const cellId = `${nextCell.rowIndex}-${nextCell.cellIndex}`
  copiedCells.value.add(cellId)

  // Показываем статус
  copyStatus.value = `Скопировано: ${cellValue}`
  setTimeout(() => {
    copyStatus.value = ''
  }, 2000)

  // Находим следующую ячейку для подсветки
  const newNextCell = findNextCellToCopy()
  if (newNextCell) {
    currentRowIndex.value = newNextCell.rowIndex
    currentCellIndex.value = newNextCell.cellIndex
  } else {
    // Все ячейки скопированы
    currentRowIndex.value = -1
    currentCellIndex.value = -1
  }
}

// Получение значения ячейки
const getCellValue = (rowIndex, cellIndex) => {
  const component = currentDelivery.value.components?.[rowIndex]
  if (!component) return ''

  switch (cellIndex) {
    case 0:
      return component.snb || ''
    case 1:
      return component.material_count?.toString() || ''
    default:
      return ''
  }
}

// Копирование текста в буфер обмена
const copyToClipboard = (text) => {
  if (!text || isDeliveryBlocked.value || isViewOnly.value) return

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

// Сброс выделения скопированных ячеек
const resetCopiedCells = () => {
  if (isDeliveryBlocked.value || isViewOnly.value) return
  copiedCells.value.clear()
  const nextCell = findNextCellToCopy()
  if (nextCell) {
    currentRowIndex.value = nextCell.rowIndex
    currentCellIndex.value = nextCell.cellIndex
  } else {
    currentRowIndex.value = -1
    currentCellIndex.value = -1
  }
}

// Обработчик кнопки "Внесено"
const handleMarkAsEntered = async () => {
  if (isDeliveryBlocked.value || isViewOnly.value) return

  const success = await markDeliveryAsEntered(currentDelivery.value)
  if (success) {
    emit('entered', currentDelivery.value)
    emit('refreshData')
  }
}

const showNotify = (options) => {
  $q.notify(options)
}

const closeModal = () => {
  showModal.value = false
  emit('close')
}

// Синхронизируем значение модального окна
watch(
  () => props.modelValue,
  (value) => {
    showModal.value = value
    if (value) {
      generateBarcode()
      // При открытии находим первую ячейку для копирования
      nextTick(() => {
        const nextCell = findNextCellToCopy()
        if (nextCell) {
          currentRowIndex.value = nextCell.rowIndex
          currentCellIndex.value = nextCell.cellIndex
        }
      })
    } else {
      resetAllStates()
    }
  },
)

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
  resetEnteredDeliveries() // Сбрасываем отмеченные доставки
}

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

// Следим за изменениями в данных доставки
watch(
  () => props.deliveryData,
  () => {
    currentDeliveryIndex.value = 0
    resetEnteredDeliveries() // Сбрасываем при новых данных
    resetCopiedCells()
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
/* Стили остаются без изменений */
.delivery-modal {
  width: 1000px;
  max-width: 2000px;
  max-height: 80vh;
  position: relative;
}

.close-button {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1000;
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
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.delivery-counter {
  font-size: 16px;
  color: #666;
  font-weight: normal;
}

.blocked-badge {
  background-color: #ffeb3b;
  color: #333;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.transfer-warning {
  background-color: #ff9800;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.blocked-label {
  color: #f44336;
  font-weight: bold;
  margin-left: 8px;
}

.zvr-number {
  font-size: 16px;
  font-weight: 600;
  color: #1434c2;
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
  position: relative;
  cursor: pointer;
}

.delivery-content:hover {
  background-color: #fafafa;
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

.bordered-table td:not(.blocked-cell) {
  cursor: pointer;
}

.bordered-table td.blocked-cell {
  background-color: #f5f5f5 !important;
  color: #9e9e9e !important;
  cursor: not-allowed !important;
}

.bordered-table th:nth-child(2),
.bordered-table td:nth-child(2) {
  text-align: center;
  width: 100px;
}

.bordered-table th:nth-child(3),
.bordered-table td:nth-child(3) {
  text-align: center;
}

/* Чередование цветов строк */
.bordered-table tr:nth-child(even):not(.blocked-row) {
  background-color: #fafafa;
}

.bordered-table tr:nth-child(even):not(.blocked-row):hover {
  background-color: #f0f0f0;
}

/* Стили для активной ячейки */
.active-cell {
  background-color: #bbdefb !important;
  font-weight: bold;
  border: 2px solid #2196f3 !important;
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

/* Стили для заблокированных ячеек */
.blocked-cell {
  background-color: #f5f5f5 !important;
  color: #9e9e9e !important;
  cursor: not-allowed !important;
}

.blocked-row {
  background-color: #fafafa !important;
  cursor: not-allowed !important;
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
  background-color: 'e8f5e9';
  color: '#2e7d32';
  padding: 8px 16px;
  border-radius: 4px;
  margin: 10px 16px;
  font-weight: 500;
  text-align: center;
}

/* Выравнивание кнопок действий справа */
.q-card-actions {
  justify-content: flex-end;
  gap: 8px;
}
</style>