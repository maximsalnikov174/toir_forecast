<template>
  <div
    class="service-status-card"
    @mouseover="hover = true"
    @mouseleave="hover = false"
    @click="handleClick"
  >
    <div v-if="showTopBar" class="vertical-bar top-bar"></div>
    <div v-if="showBottomBar" class="vertical-bar bottom-bar"></div>
    <div class="status-indicator" :class="indicatorClass"></div>
    <div class="characteristic-title">{{ Divergence }} км</div>
    <div class="other-text">{{ displayDate }}</div>
    <div v-if="DBSWCAN" class="additional-text">{{ DBSWCAN }} Дней</div>

    <!-- Элемент появляется только при наведении и совпадении organization_id с selectedDivId -->
    <div v-if="shouldShowHover" class="hover-overlay" @click.stop="openModal">
      <div class="plus-icon">+</div>
    </div>

    <!-- Модальное окно -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-close" @click="closeModal">×</div>
        <slot name="modal-content">
          <!-- Содержимое модального окна можно передать через слот -->
          <p>Это модальное окно</p>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useFilterStore } from 'src/components/Functions/FilterStoreAcceptButton';
import { useAuthStore } from 'src/stores/useAuthStore';

const hover = ref(false);
const showModal = ref(false);
const { selectedDivId } = useFilterStore();
const authStore = useAuthStore();

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
  service_work_completed_fact: {
    type: [Date, String, null],
    default: null
  },
  divId: {
    type: [String, Number],
    default: null
  }
});

// Проверяем условия для отображения hover-эффекта
const shouldShowHover = computed(() => {
  return hover.value &&
         authStore.user?.organization_id === selectedDivId.value;
});

const handleClick = () => {
  if (props.divId) {
    selectedDivId.value = props.divId;
  }
};

// Открытие модального окна
const openModal = () => {
  showModal.value = true;
};

// Закрытие модального окна с сбросом hover
const closeModal = () => {
  showModal.value = false;
  hover.value = false; // Сбрасываем состояние hover
};

// Форматирование даты
const formattedDate = computed(() => {
  if (props.LastServiceDate instanceof Date) {
    return props.LastServiceDate.toLocaleDateString();
  }
  return props.LastServiceDate;
});

const displayDate = computed(() => {
  return props.zvr_number !== null ? props.zvr_number : formattedDate.value;
});

// Класс для индикатора статуса
const indicatorClass = computed(() => {
  const statusMap = {
    1: 'exceeded',
    2: 'approaching',
    3: 'upcoming',
    4: 'normal'
  };
  return statusMap[props.request_status_id];
});

// Показывать верхнюю полосу?
const showTopBar = computed(() => {
  return props.zvr_create_date !== null;
});

// Показывать нижнюю полосу?
const showBottomBar = computed(() => {
  return props.service_work_completed_fact !== null;
});
</script>

<style scoped>
.service-status-card {
  width: 150px;
  height: 80px;
  background: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
  flex-shrink: 0;
  cursor: pointer;
}

.vertical-bar {
  position: absolute;
  width: 5px;
  height: 30px;
  left: 3px;
  background: #A5A5A5;
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
  top: 23px;
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
  color: #000000;
}

.additional-text {
  position: absolute;
  width: 120px;
  height: 12px;
  top: 47px;
  left: 13px;
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  font-size: 10px;
  line-height: 100%;
  color: #000000;
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
  border-color: transparent #0000FF transparent transparent;
}

.status-indicator.normal {
  border-color: transparent #00FF00 transparent transparent;
}

.hover-overlay {
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
}

.plus-icon {
  font-size: 24px;
  font-weight: bold;
  color: white;
  text-shadow: 0 0 3px rgba(0, 0, 0, 0.5);
}

/* Стили для модального окна */
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
  width: 400px;
  height: 250px;
  background: #FFFFFF;
  border-radius: 8px;
  padding: 15px;
  position: relative;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.modal-close {
  position: absolute;
  top: 5px;
  right: 10px;
  font-size: 20px;
  cursor: pointer;
  color: #A5A5A5;
}

.modal-close:hover {
  color: #000000;
}
</style>