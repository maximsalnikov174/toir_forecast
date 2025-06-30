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
  <div class="services-header sticky-header">
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
                :LastServiceDate="item.last_service_date"
                :DBSWCAN="item.days_between_service_work_completed_and_now"
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

.sticky-header {
  position: sticky;
  top: 0; /* Расстояние от верхнего края, можно настроить */
  z-index: 100; /* Чтобы заголовок был поверх других элементов */
  background-color: #777777;
  padding-top: 10px; /* Отступ сверху для лучшего вида */
  margin-bottom: 10px; /* Отступ снизу */
}

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
  position: relative;
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
  position: relative;
  margin-left: 10px;
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

}

.empty-status-card {
  width: 150px;
  height: 80px;
  visibility: hidden;
  flex-shrink: 0;
}
</style>