<template>
  <div class="index-page">
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

    <div class="data-container">
      <!-- Заголовок с именами сервисов -->
      <div class="services-header">
        <div class="cars-header-placeholder"></div>
        <div class="service-names-row">
          <ServiceNamesCard
            v-for="service in services"
            :key="service.service_name_id"
            :name="service.name"
          />
        </div>
      </div>

      <!-- Основные данные - машины и статусы -->
      <div class="data-rows">
        <div v-for="(car, rowIndex) in cars" :key="car.personal_id" class="data-row">
          <CarCard :grz="car.grz" />
          <div class="status-cards">
            <template v-for="(item, itemIndex) in tableData[rowIndex]" :key="itemIndex">
              <ServiceStatusCard
                v-if="item"
                :lastReading="item.last_service_reading"
                :requestReading="item.request_reading"
                :divergence="item.divergence"
              />
              <div v-else class="empty-status-card"></div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import MinimalStatus from '../components/UI/Button/MinimalStatus.vue';
import DivisionSelect from '../components/UI/Button/DivisionSelect.vue';
import GroupTs from '../components/UI/Button/GroupTs.vue';
import HideServiceWorkWithZvr from '../components/UI/Button/HideServiceWorkWithZvr.vue';
import ToAccept from 'src/components/UI/Button/ToAccept.vue';
import ServiceNamesCard from '../components/Cards/Reading/ServiceNamesCards.vue';
import ServiceStatusCard from '../components/Cards/Reading/ServiceStatusCard.vue';
import CarCard from '../components/Cards/Reading/CarsCard.vue';

const tableData = ref([]);
const services = ref([]);
const cars = ref([]);

const handleTableDataFetched = (data) => {
  tableData.value = data;
};

const handleServicesFetched = (servicesData) => {
  services.value = servicesData;
};

const handleCarsFetched = (carsData) => {
  cars.value = carsData;
};
</script>

<style scoped>
.index-page {
  padding: 20px;
  font-family: 'Inter', sans-serif;
}

.buttons-container {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 20px;
}

.buttons-container *{
  flex:1;

}

.data-container {
  display: flex;
  flex-direction: column;
}

.services-header {
  display: flex;
  margin-bottom: 10px;
}

.cars-header-placeholder {
  width: 212px;
  margin-right: 20px;
  flex-shrink: 0;
}

.service-names-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 10px;
  flex: 1;
}

.data-rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.data-row {
  display: flex;
  gap: 10px;
}

.status-cards {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 10px;
}

.empty-status-card {
  width: 150px;
  height: 80px;
  visibility: hidden;
  flex-shrink: 0;
}
</style>