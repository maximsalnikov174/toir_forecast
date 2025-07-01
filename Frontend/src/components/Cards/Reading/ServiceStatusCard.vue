<template>
  <div class="service-status-card">
    <div class="vertical-bar top-bar"></div>
    <div class="vertical-bar bottom-bar"></div>
    <div class="status-indicator" :class="indicatorClass"></div>
    <div class="characteristic-title">{{ lastReading }} км</div>
    <div class="other-text"> {{ formattedDate }}</div>
    <div class="additional-text"> {{ DBSWCAN }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  lastReading: {
    type: [String, Number],
    default: 'Н/Д'
  },
  LastServiceDate: {
    type: [Date, String],
    default: 'Н/Д'
  },
  DBSWCAN: {
    type: [Number, String],
    default: 'Н/Д'
  },
  request_status_id: {
    type: Number,
    default: 4, // По умолчанию зеленый
    validator: (value) => [1, 2, 3, 4].includes(value)
  }
});

const formattedDate = computed(() => {
  if (props.LastServiceDate instanceof Date) {
    return props.LastServiceDate.toLocaleDateString();
  }
  return props.LastServiceDate;
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
</style>