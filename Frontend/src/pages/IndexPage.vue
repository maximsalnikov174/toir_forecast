<template>
  <div class="buttons-container">
    <division-select />
    <minimal-status />
  </div>
</template>

<script setup>
import  MinimalStatus  from '../components/UI/Button/MinimalStatus.vue';
import DivisionSelect from '../components/UI/Button/DivisionSelect.vue'
</script>


<style scoped>
.buttons-container {
  display: flex;
  gap: 16px; /* Расстояние между элементами */
  align-items: center; /* Выравнивание по вертикали */
}

/* Если нужно чтобы элементы занимали доступное пространство */
.buttons-container > * {
  flex: 1;
}

/* Или если нужно прижать к краям */
/*
.buttons-container {
  justify-content: space-between;
}
*/
</style>