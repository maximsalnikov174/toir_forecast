<template>
  <div class="buttons-container">
    <division-select />
    <minimal-status />
    <GroupTs />
    <HideServiceWorkWithZvr />
    <ToAccept @servicesFetched="handleServicesFetched" />
  </div>

  <!-- Добавляем контейнер для карточек -->
  <div class="cards-container">
    <ServiceNamesCard
      v-for="service in services"
      :key="service.service_name_id"
      :name="service.name"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import MinimalStatus from '../components/UI/Button/MinimalStatus.vue'
import DivisionSelect from '../components/UI/Button/DivisionSelect.vue'
import GroupTs from '../components/UI/Button/GroupTs.vue'
import HideServiceWorkWithZvr from '../components/UI/Button/HideServiceWorkWithZvr.vue'
import ToAccept from 'src/components/UI/Button/ToAccept.vue'
import ServiceNamesCard from '../components/Cards/Reading/ServiceNamesCards.vue'

const services = ref([]);

const handleServicesFetched = (servicesData) => {
  services.value = servicesData;
}
</script>

<style scoped>
.buttons-container {
  display: flex;
  gap: 16px;
  align-items: center;
}
.buttons-container *{
  flex: 1;
}

.cards-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}
</style>