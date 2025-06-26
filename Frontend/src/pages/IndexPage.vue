<template>
  <div class="buttons-container">
    <division-select />
    <minimal-status />
    <GroupTs />
    <HideServiceWorkWithZvr />
    <ToAccept
      @tableDataFetched="handleTableDataFetched"
      @servicesFetched="handleServicesFetched"
      @carsFetched="handleCarsFetched"
    />
  </div>

  <div class="main-container">
    <!-- Имена сервисов -->
    <div class="service-names-row">
      <!-- Пустое место для колонки машин -->
      <div class="cars-column-placeholder"></div>

      <!-- Карточки имен сервисов -->
      <div class="service-names-container">
        <ServiceNamesCard
          v-for="(service,) in services"
          :key="service.service_name_id"
          :name="service.name"
        />
      </div>
    </div>

    <!-- Строки с карточками машин и статусов -->
    <div class="status-rows-container">
      <div v-for="(car, rowIndex) in cars" :key="car.personal_id" class="status-row">
        <!-- Карточка машины -->
        <CarCard :grz="car.grz" />

        <!-- Карточки статусов -->
        <template v-for="(item, itemIndex) in tableData[rowIndex]" :key="itemIndex">
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
import CarCard from '../components/Cards/Reading/CarsCard.vue'

const tableData = ref([]);
const services = ref([]);
const cars = ref([]);

const handleTableDataFetched = (data) => {
  tableData.value = data;
}

const handleServicesFetched = (servicesData) => {
  services.value = servicesData;
}

const handleCarsFetched = (carsData) => {
  cars.value = carsData;
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

.main-container {
  display: flex;
  flex-direction: column;
}

.service-names-row {
  display: flex;
  margin-bottom: 10px;
}

.cars-column-placeholder {
  width: 212px;
  margin-right: 20px;
}

.service-names-container {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  flex: 1;
}

.status-rows-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.empty-card {
  width: 150px;
  height: 80px;
  visibility: hidden;
}
</style>