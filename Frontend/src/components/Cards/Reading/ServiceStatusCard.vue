<template>
  <div class="q-pa-md">
    <q-card class="service-status-card">
      <q-card-section class="card-content">
        <div class="vertical-bar top-bar"></div>
        <div class="vertical-bar bottom-bar"></div>
        <div class="characteristic-title">{{ lastReading }}</div>
        <div class="other-text">Текущее: {{ requestReading }}</div>
        <div class="additional-text">Отклонение: {{ divergence }}</div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup>
defineProps({
  lastReading: {
    type: [String, Number],
    default: 'Н/Д'
  },
  requestReading: {
    type: [String, Number],
    default: 'Н/Д'
  },
  divergence: {
    type: [String, Number],
    default: 'Н/Д'
  }
});
</script>

<style scoped>
.service-status-card {
  width: 150px;
  height: 80px;
  background-color: #FFFFFF;
  position: relative;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.vertical-bar {
  position: absolute;
  width: 5px;
  height: 30px;
  left: 3px;
  background: #A5A5A5;
}

.top-bar {
  top: 3px;
}

.bottom-bar {
  top: 35px;
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
  letter-spacing: 0%;
  text-align: right;
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
  letter-spacing: 0%;
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
  letter-spacing: 0%;
}
</style>