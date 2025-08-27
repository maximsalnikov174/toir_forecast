<template>
  <q-dialog v-model="showModal" persistent>
    <q-card class="delivery-modal">
      <q-card-section class="header-section">
        <div class="header-content">
          <div class="delivery-title">Доставка</div>
          <div class="barcode-section">
            <div class="barcode-label">Штрих-код:</div>
            <canvas ref="barcodeCanvas" class="barcode-canvas"></canvas>
          </div>
        </div>
      </q-card-section>

      <q-card-section class="q-pt-none delivery-content">
        <!-- Обычная HTML таблица с явными границами -->
        <table class="delivery-table bordered-table">
          <thead>
            <tr>
              <th class="cell-border">Номенклатурный номер</th>
              <th class="cell-border">Кол-во запрошено</th>
              <th class="cell-border">Организация получатель</th>
              <th class="cell-border">Описание</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in deliveryData"
              :key="item.id"
              :class="{ 'active-row': currentRowIndex === index && currentCellIndex >= 0 }"
              @click="handleRowClick(index, $event)"
            >
              <td
                class="cell-border"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 0,
                  'copied-cell': copiedCells.has(`${index}-0`)
                }"
              >{{ item.nomenclature_number }}</td>
              <td
                class="cell-border text-center"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 1,
                  'copied-cell': copiedCells.has(`${index}-1`)
                }"
              >{{ item.quantity_requested }}</td>
              <td
                class="cell-border"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 2,
                  'copied-cell': copiedCells.has(`${index}-2`)
                }"
              >{{ item.recipient_organization }}</td>
              <td
                class="cell-border"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 3,
                  'copied-cell': copiedCells.has(`${index}-3`)
                }"
              >{{ item.description }}</td>
            </tr>
            <tr v-if="deliveryData.length === 0">
              <td colspan="4" class="cell-border text-center text-grey">
                Нет данных о доставке
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
import { ref, watch, nextTick, onMounted, computed } from 'vue';
import { useQuasar } from 'quasar';
import JsBarcode from 'jsbarcode';

const $q = useQuasar();
const showModal = ref(false);
const currentRowIndex = ref(-1);
const currentCellIndex = ref(-1);
const copyStatus = ref('');
const barcodeCanvas = ref(null);
const copiedCells = ref(new Set()); // Храним ID скопированных ячеек

const emit = defineEmits(['close', 'update:modelValue']);

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  deliveryData: {
    type: Array,
    default: () => []
  },
  barCode: {
    type: String,
    default: ''
  }
});

// Вычисляемое свойство для получения первого номенклатурного номера
const firstNomenclatureNumber = computed(() => {
  return props.deliveryData.length > 0
    ? props.deliveryData[0].nomenclature_number
    : props.barCode || 'NO_DATA';
});

// Синхронизируем значение модального окна
watch(() => props.modelValue, (value) => {
  showModal.value = value;
  if (value) {
    generateBarcode();
  } else {
    // Сбрасываем все состояния при закрытии через пропс
    resetAllStates();
  }
});

watch(showModal, (value) => {
  if (value !== props.modelValue) {
    emit('update:modelValue', value);
  }
  if (!value) {
    // Сбрасываем все состояния при закрытии через кнопку
    resetAllStates();
  }
});

// Функция для генерации штрих-кода
const generateBarcode = () => {
  nextTick(() => {
    if (barcodeCanvas.value && firstNomenclatureNumber.value) {
      try {
        JsBarcode(barcodeCanvas.value, firstNomenclatureNumber.value, {
          format: "CODE128",
          width: 2,
          height: 60,
          displayValue: true,
          margin: 10,
          fontSize: 16,
          textMargin: 5
        });
      } catch {
        console.error('Ошибка генерации штрих-кода');
      }
    }
  });
};

// Сброс всех состояний
const resetAllStates = () => {
  currentRowIndex.value = -1;
  currentCellIndex.value = -1;
  copyStatus.value = '';
  copiedCells.value.clear();
};

// Обработчик клика по строке таблицы
const handleRowClick = (rowIndex) => {
  if (rowIndex !== currentRowIndex.value) {
    currentRowIndex.value = rowIndex;
    currentCellIndex.value = 0;
  } else {
    currentCellIndex.value = (currentCellIndex.value + 1) % 4;
  }

  const cellValue = getCellValue(rowIndex, currentCellIndex.value);
  copyToClipboard(cellValue);

  // Добавляем ячейку в множество скопированных
  const cellId = `${rowIndex}-${currentCellIndex.value}`;
  copiedCells.value.add(cellId);
};

// Сброс выделения скопированных ячеек
const resetCopiedCells = () => {
  copiedCells.value.clear();
  currentCellIndex.value = -1;
  currentRowIndex.value = -1;
};

// Получение значения ячейки
const getCellValue = (rowIndex, cellIndex) => {
  const row = props.deliveryData[rowIndex];
  if (!row) return '';

  switch (cellIndex) {
    case 0: return row.nomenclature_number || '';
    case 1: return row.quantity_requested || '';
    case 2: return row.recipient_organization || '';
    case 3: return row.description || '';
    default: return '';
  }
};

// Копирование текста в буфер обмена
const copyToClipboard = (text) => {
  if (!text) return; // Не копируем пустые строки

  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.top = '0';
  textArea.style.left = '0';
  textArea.style.opacity = '0';

  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).catch(() => {
        fallbackCopy();
      });
    } else {
      fallbackCopy();
    }
  } catch {
    fallbackCopy();
  } finally {
    document.body.removeChild(textArea);
  }
};

// Fallback метод копирования для HTTP
const fallbackCopy = () => {
  try {
    const successful = document.execCommand('copy');
    if (!successful) {
      showNotify({
        type: 'negative',
        message: 'Не удалось скопировать текст. Разрешите доступ к буферу обмена.',
        timeout: 3000
      });
    }
  } catch {
    showNotify({
      type: 'negative',
      message: 'Не удалось скопировать текст',
      timeout: 3000
    });
  }
};

const showNotify = (options) => {
  $q.notify(options);
};

const closeModal = () => {
  showModal.value = false;
  emit('close');
};

// Следим за изменениями в данных доставки и генерируем штрих-код
watch(() => props.deliveryData, () => {
  generateBarcode();
}, { deep: true });

onMounted(() => {
  if (props.modelValue) {
    generateBarcode();
  }
});
</script>

<style scoped>
.delivery-modal {
  min-width: 900px;
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
  align-items: center;
}

.delivery-title {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.barcode-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.barcode-label {
  font-size: 16px;
  font-weight: 500;
}

.barcode-canvas {
  height: 70px;
  background: white;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.delivery-content {
  max-height: 50vh;
  overflow-y: auto;
  padding: 0;
}

/* Стили для обычной HTML таблицы с явными границами и увеличенными ячейками */
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

.bordered-table th:nth-child(2),
.bordered-table td:nth-child(2) {
  text-align: center;
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
  background-color: #c8e6c9 !important; /* Светло-зеленый фон */
  border: 2px solid #4caf50 !important; /* Зеленая рамка */
  font-weight: bold;
  position: relative;
}

.copied-cell::after {
  content: "✓";
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

/* Убедимся, что все ячейки имеют границы */
.cell-border {
  border: 1px solid #bdbdbd !important;
}

/* Стили для статуса копирования */
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