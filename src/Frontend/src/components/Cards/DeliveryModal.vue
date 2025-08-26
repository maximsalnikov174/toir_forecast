<template>
  <q-dialog v-model="showModal" persistent>
    <q-card class="delivery-modal">
      <q-card-section class="q-pt-none delivery-content">
        <!-- Обычная HTML таблица с явными границами -->
        <table class="delivery-table bordered-table">
          <thead>
            <tr>
              <th class="cell-border">Доставка</th>
              <th class="cell-border">Номенклатурный номер</th>
              <th class="cell-border">Кол-во запрошено</th>
              <th class="cell-border">Организация получатель</th>
              <th class="cell-border">Описание</th>
              <th class="cell-border">Штрих-код</th>
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
              >{{ item.delivery_info }}</td>
              <td
                class="cell-border"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 1,
                  'copied-cell': copiedCells.has(`${index}-1`)
                }"
              >{{ item.nomenclature_number }}</td>
              <td
                class="cell-border text-center"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 2,
                  'copied-cell': copiedCells.has(`${index}-2`)
                }"
              >{{ item.quantity_requested }}</td>
              <td
                class="cell-border"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 3,
                  'copied-cell': copiedCells.has(`${index}-3`)
                }"
              >{{ item.recipient_organization }}</td>
              <td
                class="cell-border"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 4,
                  'copied-cell': copiedCells.has(`${index}-4`)
                }"
              >{{ item.description }}</td>
              <td
                class="cell-border text-center"
                :class="{
                  'active-cell': currentRowIndex === index && currentCellIndex === 5,
                  'copied-cell': copiedCells.has(`${index}-5`)
                }"
                @click.stop="handleBarcodeClick"
              >
                <canvas :ref="el => setBarcodeRef(el, item.id)" class="barcode-canvas"></canvas>
              </td>
            </tr>
            <tr v-if="deliveryData.length === 0">
              <td colspan="6" class="cell-border text-center text-grey">
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
import { ref, watch, nextTick, onMounted } from 'vue';
import { useQuasar } from 'quasar';
import JsBarcode from 'jsbarcode';

const $q = useQuasar();
const showModal = ref(false);
const currentRowIndex = ref(-1);
const currentCellIndex = ref(-1);
const copyStatus = ref('');
const barcodeRefs = ref({});
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
  }
});

// Синхронизируем значение модального окна
watch(() => props.modelValue, (value) => {
  showModal.value = value;
  if (value) {
    generateBarcodes();
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

// Устанавливаем ref для штрих-кода
const setBarcodeRef = (el, id) => {
  if (el) {
    barcodeRefs.value[id] = el;
  }
};

// Обработчик клика по штрих-коду (ничего не делает)
const handleBarcodeClick = (event) => {
  event.stopPropagation();
  // Не копируем штрих-код, просто останавливаем всплытие события
};

// Функция для генерации штрих-кодов
const generateBarcodes = () => {
  nextTick(() => {
    props.deliveryData.forEach(item => {
      const canvas = barcodeRefs.value[item.id];
      if (canvas && item.nomenclature_number) {
        try {
          JsBarcode(canvas, item.nomenclature_number, {
            format: "CODE128",
            width: 2,
            height: 40,
            displayValue: false,
            margin: 5
          });
        } catch {
          console.error('Ошибка генерации штрих-кода');
        }
      }
    });
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
const handleRowClick = (rowIndex, event) => {
  // Если клик был по canvas (штрих-коду), не обрабатываем
  if (event.target.tagName === 'CANVAS') return;

  if (rowIndex !== currentRowIndex.value) {
    currentRowIndex.value = rowIndex;
    currentCellIndex.value = 0;
  } else {
    // Пропускаем ячейку со штрих-кодом (индекс 2)
    currentCellIndex.value = (currentCellIndex.value + 1) % 6;
    // Если попали на ячейку со штрих-кодом, переходим к следующей
    if (currentCellIndex.value === 5) {
      currentCellIndex.value = (currentCellIndex.value + 1) % 6;
    }
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
};

// Получение значения ячейки
const getCellValue = (rowIndex, cellIndex) => {
  const row = props.deliveryData[rowIndex];
  if (!row) return '';

  switch (cellIndex) {
    case 0: return row.delivery_info || '';
    case 1: return row.nomenclature_number || '';
    case 2: return row.quantity_requested || '';
    case 3: return row.recipient_organization || '';
    case 4: return row.description || '';
    case 5: return ''; // Пустая строка для штрих-кода
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

// Следим за изменениями в данных доставки и генерируем штрих-коды
watch(() => props.deliveryData, () => {
  generateBarcodes();
}, { deep: true });

onMounted(() => {
  if (props.modelValue) {
    generateBarcodes();
  }
});
</script>

<style scoped>
.delivery-modal {
  min-width: 1100px;
  max-width: 95vw;
  max-height: 80vh;
}

.delivery-content {
  max-height: 60vh;
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

.bordered-table th:nth-child(3),
.bordered-table td:nth-child(3),
.bordered-table th:nth-child(4),
.bordered-table td:nth-child(4) {
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

/* Стили для canvas штрих-кода */
.barcode-canvas {
  display: block;
  margin: 0 auto;
  max-width: 100%;
  height: 50px;
  cursor: default; /* Курсор по умолчанию для штрих-кода */
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