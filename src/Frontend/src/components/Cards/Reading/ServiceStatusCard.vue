<template>
  <div
    class="service-status-card"
    @mouseover="hover = true"
    @mouseleave="hover = false"
    @click="handleCardClick"
    @drop.prevent="handleDrop"
    @dragover.prevent="dragOver = true"
    @dragenter.prevent="handleDragEnter"
    @dragleave="handleDragLeave"
    :class="{ 'drag-over': dragOver }"
  >
    <!-- Верхняя полоска -->
    <div
      v-if="showTopBar"
      class="vertical-bar top-bar"
      :class="topBarClass"
    ></div>

    <!-- Нижняя полоска (теперь того же цвета что и верхняя) -->
    <div
      v-if="showBottomBar"
      class="vertical-bar bottom-bar"
      :class="topBarClass"
    ></div>

    <div class="status-indicator" :class="indicatorClass"></div>
    <div class="characteristic-title">{{ Divergence }} км</div>
    <div class="other-text">{{ displayDate }}</div>
    <div v-if="zvr_create_date" class="zvr-create-date">{{ zvr_create_date }}</div>
    <div v-if="DBSWCAN" class="additional-text">{{ DBSWCAN }} </div>

    <!-- Оверлей для основной карточки -->
    <div
      v-if="shouldShowHover"
      class="hover-overlay"
      @click.stop="handleOverlayClick"
    ></div>

    <!-- Отдельный оверлей для плюсика -->
    <div
      v-if="shouldShowPlusIcon"
      class="plus-hover-overlay"
      @click.stop="handleOverlayClick"
    >
      <div class="plus-icon">+</div>
    </div>

    <!-- Оверлей для документа (для station_id === 99) -->
    <div
      v-if="shouldShowDocumentHover"
      class="document-hover-overlay"
      @click.stop="handleDocumentClick"
    >
      <div class="document-icon">📄</div>
      <div class="document-text">Просмотр документа</div>
    </div>

    <!-- Оверлей для drag-and-drop -->
    <div
      v-if="dragOver"
      class="drag-overlay"
    >
      <div class="drag-content">
        <div class="drag-icon">📁</div>
        <div class="drag-text">Перетащите файл сюда</div>
      </div>
    </div>

    <ModalWindow
      v-model:show="showModal"
      :serviceWorkId="serviceWorkId"
      @close="closeModal"
      @submitted="$emit('submitted')"
      :onSubmitSuccess="handleApply"
    />

    <WindowCompletion
      v-model:show="showCompletionModal"
      :serviceWorkId="serviceWorkId"
      @close="closeCompletionModal"
      @submitted="$emit('submitted')"
      :onSubmitSuccess="handleApply"
      :onSubmitSuccessMaster="onSubmitSuccessMaster"
    />

    <!-- Модальное окно для отображения таблицы доставки -->
    <q-dialog v-model="showDeliveryModal" persistent>
      <q-card class="delivery-modal">
        <q-card-section class="q-pt-none delivery-content">
          <!-- Обычная HTML таблица с явными границами -->
          <table class="delivery-table bordered-table">
            <thead>
              <tr>
                <th class="cell-border">Доставка</th>
                <th class="cell-border">Номенклатурный номер</th>
                <th class="cell-border">Штрих-код</th>
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
                  :class="{ 'active-cell': currentRowIndex === index && currentCellIndex === 0 }"
                >{{ item.delivery_info }}</td>
                <td
                  class="cell-border"
                  :class="{ 'active-cell': currentRowIndex === index && currentCellIndex === 1 }"
                >{{ item.nomenclature_number }}</td>
                <td
                  class="cell-border text-center"
                  :class="{ 'active-cell': currentRowIndex === index && currentCellIndex === 2 }"
                >
                  <canvas :ref="'barcodeCanvas_' + item.id" class="barcode-canvas"></canvas>
                </td>
                <td
                  class="cell-border text-center"
                  :class="{ 'active-cell': currentRowIndex === index && currentCellIndex === 3 }"
                >{{ item.quantity_requested }}</td>
                <td
                  class="cell-border"
                  :class="{ 'active-cell': currentRowIndex === index && currentCellIndex === 4 }"
                >{{ item.recipient_organization }}</td>
                <td
                  class="cell-border"
                  :class="{ 'active-cell': currentRowIndex === index && currentCellIndex === 5 }"
                >{{ item.description }}</td>
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
          <q-btn label="Закрыть" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup>
import { computed, ref, nextTick, watch } from 'vue';
import { useQuasar } from 'quasar';
import { useFilterStore } from 'src/components/Functions/FilterStoreAcceptButton';
import { useAuthStore } from 'src/stores/useAuthStore';
import { useFileUploadService } from '../../Functions/fileUploadService'; // Импортируем сервис
import ModalWindow from '../ModalWindow.vue';
import WindowCompletion from '../WindowCompletion.vue';
import JsBarcode from 'jsbarcode';

const hover = ref(false);
const dragOver = ref(false);
const dragCounter = ref(0);
const showModal = ref(false);
const showCompletionModal = ref(false);
const showDeliveryModal = ref(false);
const { selectedDivId } = useFilterStore();
const authStore = useAuthStore();
const $q = useQuasar();
const { uploadFile } = useFileUploadService(); // Используем сервис
// Данные для таблицы доставки
const deliveryData = ref([]);
const loading = ref(false);

// Переменные для отслеживания текущей позиции копирования
const currentRowIndex = ref(-1);
const currentCellIndex = ref(-1);
const copyStatus = ref('');

const showNotify = (options) => {
  $q.notify(options);
};

const props = defineProps({
  Divergence: {
    type: [String, Number],
    default: 'Н/Д'
  },
  LastServiceDate: {
    type: [Date, String],
    default: 'Н/Д'
  },
  DBSWCAN: {
    type: [Number, String],
    default: ''
  },
  request_status_id: {
    type: Number,
    default: 4,
    validator: (value) => [1, 2, 3, 4].includes(value)
  },
  zvr_create_date: {
    type: [Date, String, null],
    default: null
  },
  zvr_number: {
    type: [String, null],
    default: null
  },
  service_work_completed: {
    type: [Date, String, null],
    default: null
  },
  divId: {
    type: [String, Number],
    default: null
  },
  id: {
    type: [Number, String],
    required: true
  },
  station: {
    type: Object,
    default: () => ({ id: null })
  },
  onSubmitSuccessMaster: {
    type: Function,
    default: () => {}
  },
  documentUrl: {
    type: String,
    default: null
  }
});

const emit = defineEmits(['file-dropped', 'submitted', 'document-click']);

const topBarClass = computed(() => {
  if (!props.station?.id) return '';

  const stationClassMap = {
    1: 'station-purple',
    2: 'station-orange',
    3: 'station-turquoise',
  };

  return stationClassMap[props.station.id] || '';
});

const serviceWorkId = ref(props.id);

// Показывать иконку документа для пользователей со station_id === 99
const shouldShowDocumentHover = computed(() => {
  return hover.value &&
         authStore.user?.users_organization?.station_id === 99;
});

const shouldShowPlusIcon = computed(() => {
  return hover.value &&
  (authStore.user?.is_superuser || authStore.user?.users_organization.id === selectedDivId.value)&&
  props.zvr_number === null || props.zvr_number === '';
});

const shouldShowHover = computed(() => {
  return hover.value &&
         (authStore.user?.is_superuser || authStore.user?.users_organization.station_id !== null) &&
         !props.service_work_completed;
});

// Функция для генерации штрих-кодов
const generateBarcodes = () => {
  nextTick(() => {
    deliveryData.value.forEach(item => {
      const canvasRef = 'barcodeCanvas_' + item.id;
      const canvas = document.querySelector(`[ref="${canvasRef}"]`);

      if (canvas && item.nomenclature_number) {
        try {
          JsBarcode(canvas, item.nomenclature_number, {
            format: "CODE128",
            width: 2,
            height: 40,
            displayValue: false,
            margin: 5
          });
        } catch (error) {
          console.error('Ошибка генерации штрих-кода:', error);
        }
      }
    });
  });
};

// Обработчик клика по строке таблицы
const handleRowClick = (rowIndex, event) => {
  // Если клик был по canvas (штрих-коду), не обрабатываем
  if (event.target.tagName === 'CANVAS') return;

  // Если это новая строка, сбрасываем индекс ячейки
  if (rowIndex !== currentRowIndex.value) {
    currentRowIndex.value = rowIndex;
    currentCellIndex.value = 0;
  } else {
    // Переходим к следующей ячейке
    currentCellIndex.value = (currentCellIndex.value + 1) % 6;
  }

  // Копируем содержимое текущей ячейки
  const cellValue = getCellValue(rowIndex, currentCellIndex.value);
  copyToClipboard(cellValue);

  // Показываем статус копирования
  const columnNames = ['Доставка', 'Номенклатурный номер', 'Штрих-код', 'Кол-во', 'Организация', 'Описание'];
  copyStatus.value = `Скопировано: ${columnNames[currentCellIndex.value]} - ${cellValue}`;

  // Автоматически скрываем статус через 2 секунды
  setTimeout(() => {
    copyStatus.value = '';
  }, 2000);
};

// Получение значения ячейки
const getCellValue = (rowIndex, cellIndex) => {
  const row = deliveryData.value[rowIndex];
  if (!row) return '';

  switch (cellIndex) {
    case 0: return row.delivery_info || '';
    case 1: return row.nomenclature_number || '';
    case 2: return row.nomenclature_number || ''; // Для штрих-кода используем тот же номер
    case 3: return row.quantity_requested || '';
    case 4: return row.recipient_organization || '';
    case 5: return row.description || '';
    default: return '';
  }
};

// Копирование текста в буфер обмена (работает с HTTP)
const copyToClipboard = (text) => {
  // Создаем временный textarea элемент
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
    // Пытаемся использовать современный API
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(() => {
        console.log('Текст скопирован через Clipboard API');
      }).catch(err => {
        console.error('Ошибка Clipboard API:', err);
        // Fallback для HTTP
        fallbackCopy(textArea);
      });
    } else {
      // Fallback для HTTP
      fallbackCopy(textArea);
    }
  } catch (err) {
    console.error('Ошибка копирования:', err);
    fallbackCopy(textArea);
  } finally {
    document.body.removeChild(textArea);
  }
};

// Fallback метод копирования для HTTP
const fallbackCopy = () => {
  try {
    // Старый метод для HTTP
    const successful = document.execCommand('copy');
    if (successful) {
      console.log('Текст скопирован через execCommand');
    } else {
      console.error('Не удалось скопировать текст');
      showNotify({
        type: 'negative',
        message: 'Не удалось скопировать текст. Разрешите доступ к буферу обмена.',
        timeout: 3000
      });
    }
  } catch (err) {
    console.error('Ошибка fallback копирования:', err);
    showNotify({
      type: 'negative',
      message: 'Не удалось скопировать текст',
      timeout: 3000
    });
  }
};

// Следим за изменениями в данных доставки и генерируем штрих-коды
watch(deliveryData, () => {
  generateBarcodes();
});

// Загрузка данных о доставке
const loadDeliveryData = async () => {
  loading.value = true;
  try {
    // Здесь должен быть API запрос для получения данных
    // Временно используем mock данные
    deliveryData.value = [
      {
        id: 1,
        delivery_info: 'Доставка №12345',
        nomenclature_number: 'ABC-123',
        quantity_requested: 5,
        recipient_organization: 'ООО "Ромашка"',
        description: 'Запчасти для оборудования'
      },
      {
        id: 2,
        delivery_info: 'Доставка №12346',
        nomenclature_number: 'XYZ-789',
        quantity_requested: 3,
        recipient_organization: 'ИП Иванов',
        description: 'Расходные материалы'
      },
      {
        id: 3,
        delivery_info: 'Доставка №12347',
        nomenclature_number: 'DEF-456',
        quantity_requested: 10,
        recipient_organization: 'ЗАО "Вектор"',
        description: 'Инструменты'
      }
    ];

    // Генерируем штрих-коды после загрузки данных
    generateBarcodes();
  } catch  {
    showNotify({
      type: 'negative',
      message: 'Ошибка при загрузке данных о доставке',
      timeout: 3000
    });
  } finally {
    loading.value = false;
  }
};

const handleCardClick = () => {
  if (props.divId) {
    selectedDivId.value = props.divId;
  }
};

const handleOverlayClick = () => {
  if (props.service_work_completed) {
    return;
  }

  if (props.zvr_number) {
    openCompletionModal();
  } else {
    openModal();
  }
};

// Обработчик клика по документу
const handleDocumentClick = async () => {
  // Сбрасываем состояние копирования при открытии модального окна
  currentRowIndex.value = -1;
  currentCellIndex.value = -1;
  copyStatus.value = '';

  await loadDeliveryData();
  showDeliveryModal.value = true;
};

const handleDragEnter = (e) => {
  e.preventDefault();
  dragCounter.value++;
  dragOver.value = true;
};

const handleDragLeave = (e) => {
  e.preventDefault();
  dragCounter.value--;

  if (dragCounter.value === 0) {
    dragOver.value = false;
  }
};

const handleDrop = async (event) => {
  dragOver.value = false;
  dragCounter.value = 0;

  const files = event.dataTransfer.files;
  if (files.length === 0) return;

  try {
    const result = await uploadFile(files[0], props.id);

    if (result.success) {
      emit('file-dropped', {
        file: files[0],
        cardId: props.id,
        response: result.data
      });

      showNotify({
        type: 'positive',
        message: result.message,
        timeout: 2000
      });
    } else {
      emit('file-dropped-error', {
        file: files[0],
        cardId: props.id,
        error: result.originalError
      });

      showNotify({
        type: 'negative',
        message: result.error,
        timeout: 3000
      });
    }

  } catch (error) {
    emit('file-dropped-error', {
      file: files[0],
      cardId: props.id,
      error: error
    });

    showNotify({
      type: 'negative',
      message: 'Неожиданная ошибка при загрузке файла',
      timeout: 3000
    });
  }
};

const openModal = () => {
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  hover.value = false;
};

const openCompletionModal = () => {
  showCompletionModal.value = true;
};

const closeCompletionModal = () => {
  showCompletionModal.value = false;
  hover.value = false;
};

const formattedDate = computed(() => {
  if (props.LastServiceDate instanceof Date) {
    return props.LastServiceDate.toLocaleDateString();
  }
  return props.LastServiceDate;
});

const displayDate = computed(() => {
  return props.zvr_number !== null ? props.zvr_number : formattedDate.value;
});

const indicatorClass = computed(() => {
  const statusMap = {
    1: 'exceeded',
    2: 'approaching',
    3: 'upcoming',
    4: 'normal'
  };
  return statusMap[props.request_status_id];
});

const showTopBar = computed(() => {
  return props.zvr_create_date !== null;
});

const showBottomBar = computed(() => {
  return props.service_work_completed !== null;
});
</script>

<style scoped>
.zvr-create-date {
  position: absolute;
  width: 120px;
  height: 12px;
  top: 22px;
  left: 13px;
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  font-size: 9px;
  line-height: 100%;
  color: #8a8989;
}

.service-status-card {
  width: 150px;
  height: 80px;
  background: #FFFFFF;
  border-radius: 8px;
  border: 1px solid #000000;
  border-color: #000000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
  flex-shrink: 0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.service-status-card.drag-over {
  border: 1px dashed #ffffff;
  background-color: rgba(106, 13, 173, 0.1);
  transform: scale(1);
}

.station-purple {
  background: purple;
}

.station-orange {
  background: orange;
}

.station-turquoise {
  background: turquoise;
}

.vertical-bar {
  position: absolute;
  width: 5px;
  height: 30px;
  left: 3px;
}

.top-bar {
  top: 8px;
}

.bottom-bar {
  top: 43px;
}

.characteristic-title {
  position: absolute;
  width: 120px;
  height: 22px;
  top: 32px;
  left: 22px;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 18px;
  line-height: 100%;
  color: #000000;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.other-text {
  position: absolute;
  width: 120px;
  height: 12px;
  top: 9px;
  left: 13px;
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  font-size: 10px;
  line-height: 100%;
  color: #8a8989;
}

.additional-text {
  position: absolute;
  width: 120px;
  height: 12px;
  top: 49px;
  left: 13px;
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  font-size: 10px;
  line-height: 100%;
  color: #000000; /* ИСПРАВЛЕНО: убраны кавычки и добавлен цвет */
}

.status-indicator {
  position: absolute;
  top: 0;
  right: 0;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 0 20px 20px 0;
  border-color: transparent #A5A5A5 transparent transparent;
  border-radius: 0 8px 0 0;
}

.status-indicator.exceeded {
  border-color: transparent #FF0000 transparent transparent;
}

.status-indicator.approaching {
  border-color: transparent #FFFF00 transparent transparent;
}

.status-indicator.upcoming {
  border-color: transparent #00FF00  transparent transparent;
}

.status-indicator.normal {
  border-color: transparent #0000FF transparent transparent;
}

/* Обычный оверлей для карточек с ZVR номером */
.hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(128, 0, 128, 0.3);
  border-radius: 8px;
  cursor: pointer;
  z-index: 5;
}

/* Отдельный оверлей для плюсика */
.plus-hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(128, 0, 128, 0.3);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 5;
}

.plus-icon {
  font-size: 24px;
  font-weight: bold;
  color: white;
  text-shadow: 0 0 3px rgba(0, 0, 0, 0.5);
}

/* Оверлей для документа (для station_id === 99) */
.document-hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 128, 0, 0.3);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 6;
  transition: background-color 0.2s ease;
}

.document-hover-overlay:hover {
  background-color: rgba(0, 128, 0, 0.5);
}

.document-icon {
  font-size: 32px;
  margin-bottom: 5px;
  filter: drop-shadow(0 0 2px rgba(0, 0, 0, 0.5));
}

.document-text {
  font-size: 12px;
  font-weight: bold;
  color: white;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.7);
  text-align: center;
  max-width: 90%;
}

/* Оверлей для drag-and-drop */
.drag-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 99%;
  height: 100%;
  background-color: rgba(106, 13, 173, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.drag-content {
  text-align: center;
}

.drag-icon {
  font-size: 24px;
  margin-bottom: 5px;
}

.drag-text {
  font-size: 12px;
  font-weight: bold;
  color: #ffffff;
}

/* Стили для модального окна доставки */
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