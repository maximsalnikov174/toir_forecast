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

    <!-- Иконка документа для role_id = 4 -->
    <div
      v-if="shouldShowDocumentIcon"
      class="document-icon-corner"
      @click.stop="handleDocumentIconClick"
    >
      📄
      <span v-if="total_docs_count > 0" class="doc-count-badge">{{ total_docs_count }}</span>
    </div>

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

    <div
      v-if="dragOver && isRole4"
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
    <DeliveryModal
      v-model="showDeliveryModal"
      :delivery-data="deliveryData"
      @close="closeDeliveryModal"
      @refresh-data="handleRefreshData"
      :bar-code="barCodeValue"
      :zvr_number="zvr_number"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useFilterStore } from 'src/components/Functions/FilterStoreAcceptButton';
import { useAuthStore } from 'src/stores/useAuthStore';
import { useFileUploadService } from '../../Functions/fileUploadService';
import ModalWindow from '../ModalWindow.vue';
import WindowCompletion from '../WindowCompletion.vue';
import DeliveryModal from '../DeliveryModal.vue';
import { deliveryService } from '../../Functions/deliveryService';

const hover = ref(false);
const dragOver = ref(false);
const dragCounter = ref(0);
const showModal = ref(false);
const showCompletionModal = ref(false);
const showDeliveryModal = ref(false);
const { selectedDivId } = useFilterStore();
const authStore = useAuthStore();
const $q = useQuasar();
const { uploadFile } = useFileUploadService();
const deliveryData = ref({});
const loading = ref(false);

const handleRefreshData = () => {
  loadDeliveryData();
};

const isRole4 = computed(() => {
  return authStore.user?.role_id === 4;
});

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
  },
  total_docs_count: {
    type: [String, Number],
    default: null
  },
});

const emit = defineEmits(['file-dropped', 'submitted', 'document-click', 'refresh-delivery-data']);

// Добавляем вычисляемое свойство для отображения иконки документа
const shouldShowDocumentIcon = computed(() => {
  return isRole4.value &&
         props.total_docs_count !== null &&
         props.total_docs_count !== undefined &&
         props.total_docs_count !== '' &&
         props.total_docs_count > 0;
});

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

const shouldShowDocumentHover = computed(() => {
  return hover.value && authStore.user?.role_id === 5;
});

const shouldShowPlusIcon = computed(() => {
  return hover.value &&
         (authStore.user?.is_superuser || authStore.user?.users_organization.id === selectedDivId.value) &&
         (props.zvr_number === null || props.zvr_number === '');
});

const shouldShowHover = computed(() => {
  return hover.value &&
         (authStore.user?.is_superuser || authStore.user?.users_organization.station_id !== null || authStore.user?.role_id === 6) &&
         !props.service_work_completed;
});

const loadDeliveryData = async () => {
  loading.value = true;
  try {
    deliveryData.value = await deliveryService.getDeliveryData(props.id);
  } catch (error) {
    showNotify({
      type: 'negative',
      message: error.message || 'Ошибка при загрузке данных о доставке',
      timeout: 3000
    });
    deliveryData.value = {};
  } finally {
    loading.value = false;
  }
};

const handleCardClick = () => {
  if (props.divId) {
    selectedDivId.value = props.divId;
  }
};

// Обработчик клика по иконке документа
const handleDocumentIconClick = async () => {
  await loadDeliveryData();
  showDeliveryModal.value = true;
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

const handleDocumentClick = async () => {
  await loadDeliveryData();
  showDeliveryModal.value = true;
};

const closeDeliveryModal = () => {
  showDeliveryModal.value = false;
};

const handleDragEnter = (e) => {
  if (!isRole4.value) return;
  e.preventDefault();
  dragCounter.value++;
  dragOver.value = true;
};

const handleDragLeave = (e) => {
  if (!isRole4.value) return;
  e.preventDefault();
  dragCounter.value--;
  if (dragCounter.value === 0) {
    dragOver.value = false;
  }
};

const handleDrop = async (event) => {
  if (!isRole4.value) return;
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
  color: #000000;
}

/* Стили для иконки документа в правом нижнем углу */
.document-icon-corner {
  position: absolute;
  bottom: 5px;
  right: 5px;
  font-size: 16px;
  cursor: pointer;
  z-index: 10;
  transition: transform 0.2s ease;
}

.document-icon-corner:hover {
  transform: scale(1.2);
}

.doc-count-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background-color: #ff4757;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
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
  border-color: transparent #00FF00 transparent transparent;
}

.status-indicator.normal {
  border-color: transparent #0000FF transparent transparent;
}

/* Остальные стили остаются без изменений */
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
</style>