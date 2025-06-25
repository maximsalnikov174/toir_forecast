<template>
  <div class="ServiceNamesCard">
    <div class="card-text">{{ name }}</div>
  </div>
</template>

<script setup>
defineProps({
  name: {
    type: String,
    required: true
  }
});
</script>

<style scoped>
.ServiceNamesCard {
  width: auto; /* Изменено с фиксированной ширины */
  min-width: 118px;
  height: 41px;
  background-color: #555555;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0 10px;
  border-radius: 4px;
}

.card-text {
  font-family: Inter, sans-serif;
  font-weight: 400;
  font-size: 12px;
  line-height: 100%;
  letter-spacing: 0%;
  text-align: center;
  color: white;
  white-space: nowrap; /* Предотвращает перенос текста */
  overflow: hidden;
  text-overflow: ellipsis; /* Добавляет многоточие если текст не помещается */
  max-width: 100%;
}
</style>