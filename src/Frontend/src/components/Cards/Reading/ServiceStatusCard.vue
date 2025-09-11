<template>
  <div
    class="service-status-card"
    @mouseover="handleMouseOver"
    @mouseleave="handleMouseLeave"
    @click="handleCardClick"
    @drop.prevent="handleDrop"
    @dragover.prevent="handleDragOver"
    @dragenter.prevent="handleDragEnter"
    @dragleave="handleDragLeave"
    :class="{ 'drag-over': dragOver, 'file-hover': fileHover }"
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

    <!-- Анимация загрузки при наведении с файлами -->
    <div
      v-if="fileHover && isRole4"
      class="file-hover-animation"
      :class="{ 'animating': isAnimating, 'completed': animationCompleted }"
    >
      <div class="animation-progress" :style="{ width: animationProgress + '%' }"></div>
      <div class="animation-text">
        {{ animationText }}
      </div>
    </div>

    <!-- Иконка документа для role_id = 4 и role_id = 5 -->
    <div
      v-if="shouldShowDocumentIcon"
      class="document-icon-corner"
      :class="{ 'no-click': authStore.user?.role_id === 5 }"
      @click.stop="authStore.user?.role_id !== 5 ? handleDocumentIconClick() : null"
    >
      📄
      <span v-if="showDocCountBadge" class="doc-count-badge">{{ unprocessedDocsCount }}</span>
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

    <!-- Оверлей для документа (для role_id ===5 ) -->
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

    <!-- Индикатор загрузки файлов -->
    <div
      v-if="isUploading"
      class="upload-overlay"
    >
      <div class="upload-content">
        <q-spinner
          color="primary"
          size="3em"
        />
        <div class="upload-text">Загрузка файлов...</div>
        <div class="upload-progress" v-if="uploadProgress > 0">
          {{ uploadProgress }}%
        </div>
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

    <!-- Модальное окно для отображения таблица доставки -->
    <DeliveryModal
      v-model="showDeliveryModal"
      :delivery-data="deliveryData"
      @close="closeDeliveryModal"
      @refresh-data="handleRefreshData"
      @submit-success="onSubmitSuccessMaster"
      :bar-code="barCodeValue"
      :zvr_number="zvr_number"
    />
  </div>
</template>

<script setup>
import { computed, ref, onUnmounted, onMounted } from 'vue';
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
const { uploadFiles } = useFileUploadService();
const deliveryData = ref({});
const loading = ref(false);

// Состояния для анимации загрузки
const fileHover = ref(false);
const isAnimating = ref(false);
const animationCompleted = ref(false);
const animationProgress = ref(0);
const animationInterval = ref(null);
const animationDuration = 1500; // 1.5 секунды для анимации

// Добавляем состояние для отслеживания загрузки файлов
const isUploading = ref(false);
const uploadProgress = ref(0);

const handleRefreshData = () => {
  loadDeliveryData();
};

const isRole4 = computed(() => {
  return authStore.user?.role_id === 4 || authStore.user?.role_id === 2 || authStore.user?.role_id === 6 || authStore.user?.role_id === 5 ;
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
  total_docs_processed_count: {
    type: [String, Number],
    default: 0
  },
});

const emit = defineEmits(['file-dropped', 'submitted', 'document-click', 'refresh-delivery-data']);

// Текст для анимации
const animationText = computed(() => {
  if (animationCompleted.value) return 'Готово!';
  if (isAnimating.value) return 'Загрузка...';
  return 'Перетащите для загрузки';
});

// Очистка интервала при размонтировании компонента
onUnmounted(() => {
  stopAnimation();
});

const handleMouseOver = () => {
  // Не активируем ховер если идет загрузка
  if (!isUploading.value) {
    hover.value = true;
  }
};

const handleMouseLeave = () => {
  // Сбрасываем только если нет активной загрузки файлов
  if (!isUploading.value) {
    resetAllStates();
  }
};

const startAnimation = () => {
  if (!isRole4.value) return;

  stopAnimation();

  isAnimating.value = true;
  animationCompleted.value = false;
  animationProgress.value = 0;

  const startTime = Date.now();

  animationInterval.value = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(100, (elapsed / animationDuration) * 100);

    animationProgress.value = progress;

    if (progress >= 100) {
      animationCompleted.value = true;
      stopAnimation();

      // Показываем уведомление о готовности к загрузке
      showNotify({
        type: 'positive',
        message: 'Готово к загрузке! Отпустите файлы',
        timeout: 1000
      });
    }
  }, 16); // ~60 FPS
};

const stopAnimation = () => {
  if (animationInterval.value) {
    clearInterval(animationInterval.value);
    animationInterval.value = null;
  }
  isAnimating.value = false;
};

// Функция для полного сброса всех состояний
const resetAllStates = () => {
  hover.value = false;
  dragOver.value = false;
  dragCounter.value = 0;
  fileHover.value = false;
  stopAnimation();
  animationProgress.value = 0;
  animationCompleted.value = false;
  isAnimating.value = false;
};

// Добавляем вычисляемое свойство для отображения иконки документа
const shouldShowDocumentIcon = computed(() => {
  const isAllowedRole = authStore.user?.role_id === 4 || authStore.user?.role_id === 5;
  return isAllowedRole &&
         props.total_docs_count !== null &&
         props.total_docs_count !== undefined &&
         props.total_docs_count !== '' &&
         props.total_docs_count > 0 &&
         !isUploading.value; // Не показывать во время загрузки
});

// Вычисляем количество необработанных документов (разницу)
const unprocessedDocsCount = computed(() => {
  const total = Number(props.total_docs_count) || 0;
  const processed = Number(props.total_docs_processed_count) || 0;
  return Math.max(0, total - processed); // Гарантируем неотрицательное значение
});

// Показывать бейдж только если есть необработанные документы
const showDocCountBadge = computed(() => {
  return unprocessedDocsCount.value > 0;
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
  if (isUploading.value) return false;
  return hover.value && authStore.user?.role_id === 5;
});

const shouldShowPlusIcon = computed(() => {
  if (isUploading.value) return false;
  return hover.value &&
         (authStore.user?.is_superuser || authStore.user?.users_organization.id === selectedDivId.value) &&
         (props.zvr_number === null || props.zvr_number === '');
});

const shouldShowHover = computed(() => {
  if (!authStore.isAuthenticated || isUploading.value) return false;
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
  fileHover.value = true;

  // Запускаем анимацию только если она еще не запущена
  if (!isAnimating.value && !animationCompleted.value) {
    startAnimation();
  }
};

const handleDragLeave = (e) => {
  if (!isRole4.value) return;
  e.preventDefault();
  dragCounter.value--;

  // Сбрасываем состояния только когда все drag события завершены
  if (dragCounter.value <= 0) {
    dragCounter.value = 0;
    dragOver.value = false;
    fileHover.value = false;

    // Если анимация не завершена, сбрасываем ее
    if (!animationCompleted.value) {
      stopAnimation();
      animationProgress.value = 0;
    }
  }
};

// Добавляем обработчик для глобального dragleave
const handleGlobalDragLeave = (e) => {
  // Проверяем, что курсор покидает окно браузера
  if (e.clientY <= 0 || e.clientX <= 0 ||
      e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) {
    resetAllStates();
  }
};

const handleDragOver = (e) => {
  if (!isRole4.value) return;
  e.preventDefault();
  dragOver.value = true;
};

const handleDrop = async (event) => {
  if (!isRole4.value) return;

  const files = Array.from(event.dataTransfer.files);
  if (files.length === 0) {
    resetAllStates();
    return;
  }

  // Если анимация не завершена, прерываем операцию
  if (!animationCompleted.value) {
    showNotify({
      type: 'warning',
      message: 'Завершите процесс загрузки, удерживая файлы над карточкой',
      timeout: 1000
    });
    resetAllStates();
    return; // Прерываем выполнение
  }

  // Устанавливаем состояние загрузки
  isUploading.value = true;
  uploadProgress.value = 0;

  try {
    // Используем uploadFiles вместо uploadFile для множественной загрузки
    const result = await uploadFiles(files, props.id, (progress) => {
      uploadProgress.value = Math.round(progress * 100);
    });

    if (result.success) {
      emit('file-dropped', {
        files: files,
        cardId: props.id,
        response: result.data
      });

      showNotify({
        type: 'positive',
        message: result.message,
        timeout: 2000
      });

      // Вызываем onSubmitSuccessMaster при успешной загрузке
      if (props.onSubmitSuccessMaster) {
        props.onSubmitSuccessMaster();
      }

    } else {
      emit('file-dropped-error', {
        files: files,
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
      files: files,
      cardId: props.id,
      error: error
    });

    showNotify({
      type: 'negative',
      message: 'Неожиданная ошибка при загрузке файлов',
      timeout: 3000
    });
  } finally {
    // Сбрасываем состояние загрузки
    isUploading.value = false;
    uploadProgress.value = 0;
    resetAllStates();
  }
};

const openModal = () => {
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  resetAllStates();
};

const openCompletionModal = () => {
  showCompletionModal.value = true;
};

const closeCompletionModal = () => {
  showCompletionModal.value = false;
  resetAllStates();
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

onMounted(() => {
  window.addEventListener('dragleave', handleGlobalDragLeave);
});

onUnmounted(() => {
  window.removeEventListener('dragleave', handleGlobalDragLeave);
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
  overflow: hidden;
}

.service-status-card.file-hover {
  border-color: #6a0dad;
  box-shadow: 0 0 10px rgba(106, 13, 173, 0.5);
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

/* Анимация загрузки при наведении с файлами */
.file-hover-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(106, 13, 173, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 15;
  transition: all 0.3s ease;
}

.file-hover-animation.animating {
  background: rgba(106, 13, 173, 0.2);
}

.file-hover-animation.completed {
  background: rgba(0, 128, 0, 0.2);
}

.animation-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 5px;
  background-color: #000000;
  transition: width 0.1s linear;
  border-radius: 0 0 8px 8px;
}

.file-hover-animation.completed .animation-progress {
  background: #000000;
}

.animation-text {
  font-size: 10px;
  font-weight: 500;
  color: #6a0dad;
  text-align: center;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  max-width: 100%;
  z-index: 1;
}

.file-hover-animation.completed .animation-text {
  color: #4caf50;
}

/* Стили для иконки документа в правом нижнем углу */
.document-icon-corner {
  position: absolute;
  bottom: 2px;
  right: 11px;
  font-size: 16px;
  cursor: pointer;
  z-index: 10;
  transition: transform 0.2s ease;
}

.document-icon-corner:hover {
  transform: scale(1.1);
}

.document-icon-corner.no-click {
  cursor: default !important;
  pointer-events: none;
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

/* Стили для индикатора загрузки */
.upload-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

.upload-content {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-text {
  font-size: 12px;
  font-weight: 500;
  color: #333;
}

.upload-progress {
  font-size: 11px;
  font-weight: bold;
  color: #1976d2;
  background-color: rgba(25, 118, 210, 0.1);
  padding: 2px 6px;
  border-radius: 10px;
}
</style>