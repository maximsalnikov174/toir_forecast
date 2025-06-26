<template>
  <div class="buttons-container">
    <division-select />
    <minimal-status />
    <GroupTs />
    <HideServiceWorkWithZvr />
    <ToAccept
      @tableDataFetched="handleTableDataFetched"
      @servicesFetched="handleServicesFetched"
    />
  </div>

  <!-- Горизонтальный контейнер для имен сервисов -->
  <div class="service-names-container">
    <ServiceNamesCard
      v-for="(service,) in services"
      :key="service.service_name_id"
      :name="service.name"
    />
  </div>

  <!-- Горизонтальные строки статусов -->
  <div class="status-rows-container">
    <div v-for="(row, rowIndex) in tableData" :key="rowIndex" class="status-row">
      <template v-for="(item, itemIndex) in row" :key="itemIndex">
        <ServiceStatusCard
          v-if="item"
          :lastReading="item.last_service_reading"
          :requestReading="item.request_reading"
          :divergence="item.divergence"
        />
        <div v-else class="empty-card"></div>
      </template>
    </div>
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
import ServiceStatusCard from '../components/Cards/Reading/ServiceStatusCard.vue'

const tableData = ref([]);
const services = ref([]);

const handleTableDataFetched = (data) => {
  tableData.value = data;
}

const handleServicesFetched = (servicesData) => {
  services.value = servicesData;
}
</script>

<style scoped>
.buttons-container {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 20px;
}
.buttons-container * {
  flex: 1;
}

.service-names-container {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  overflow-x: auto;
  padding-bottom: 10px;
}

.service-names-container *{
  flex:1
}

.status-rows-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-rows-container *{
  flex:1

}

.status-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 10px;
}

.empty-card {
  width: 118px; /* Ширина ServiceStatusCard */
  height: 0;
  visibility: hidden;
}
</style>