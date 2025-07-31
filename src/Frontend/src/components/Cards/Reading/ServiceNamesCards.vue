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
  min-width: 150px;
  max-width: 150px;
  min-height: 41px; /* Изменено с height на min-height */
  background-color: #555555;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 5px 10px; /* Увеличено padding сверху и снизу */
  border-radius: 4px;
  flex-shrink: 0;
  word-break: break-word; /* Добавлено для переноса длинных слов */
}

.card-text {
  font-family: Inter, sans-serif;
  font-weight: 400;
  font-size: 12px;
  line-height: 1.2; /* Увеличено для многострочного текста */
  letter-spacing: 0%;
  text-align: center;
  color: white;
  white-space: normal; /* Изменено с nowrap на normal */
  overflow: visible; /* Изменено с hidden на visible */
  text-overflow: clip; /* Изменено с ellipsis на clip */
  display: -webkit-box;
  -webkit-box-orient: vertical;
  width: 100%;
}
</style>