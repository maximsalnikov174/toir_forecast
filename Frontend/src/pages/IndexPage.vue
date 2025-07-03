<template>
  <div class="index-page">
    <div class="user-controls">
      <div class="user-name-placeholder">
        {{ userName || 'Гость' }}
      </div>
      <button class="login-logout-button" @click="handleAuth">
        {{ isLoggedIn ? 'Выйти' : 'Войти' }}
      </button>
    </div>

    <LoginRegisterDialog
      ref="authDialog"
      @login="handleLogin"
      @register="handleRegister"
      @close="handleDialogClose"
    />

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
          <CarCard :grz="car.grz"
          :model="car.car_model?.name || ''"
          :daliDistanse="car.indicators?.daily_distance"
          :requestReading="car.indicators?.request_reading"
          />
          <div class="status-cards">
            <template v-for="(item, itemIndex) in tableData[rowIndex]" :key="itemIndex">
              <ServiceStatusCard
                v-if="item"
                :Divergence="item.divergence"
                :LastServiceDate="item.last_service_date"
                :DBSWCAN="item.days_between_service_work_completed_and_now"
                :request_status_id="item.request_status_id"
                :zvr_create_date="item.zvr_create_date"
                :zvr_number="item.zvr_number"
                :service_work_completed_fact="item.service_work_completed_fact"
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
import { ref } from 'vue'
import MinimalStatus from '../components/UI/Button/MinimalStatus.vue'
import DivisionSelect from '../components/UI/Button/DivisionSelect.vue'
import GroupTs from '../components/UI/Button/GroupTs.vue'
import HideServiceWorkWithZvr from '../components/UI/Button/HideServiceWorkWithZvr.vue'
import ToAccept from 'src/components/UI/Button/ToAccept.vue'
import ServiceNamesCard from '../components/Cards/Reading/ServiceNamesCards.vue'
import ServiceStatusCard from '../components/Cards/Reading/ServiceStatusCard.vue'
import CarCard from '../components/Cards/Reading/CarsCard.vue'
import LoginRegisterDialog from 'src/components/UI/Windows/LoginRegisterDialog.vue'

const tableData = ref([])
const services = ref([])
const cars = ref([])
const isLoggedIn = ref(false)
const userName = ref('')
const authDialog = ref(null)

const handleTableDataFetched = (data) => {
  tableData.value = data
}

const handleServicesFetched = (servicesData) => {
  services.value = servicesData
}

const handleCarsFetched = (carsData) => {
  cars.value = carsData
}

const handleAuth = () => {
  if (isLoggedIn.value) {
    // Выход из системы
    isLoggedIn.value = false
    userName.value = ''
  } else {
    // Показываем диалог авторизации
    authDialog.value?.open()
  }
}

const handleLogin = (credentials) => {
  // Здесь должна быть логика входа
  console.log('Login attempt with:', credentials)

  // Временная заглушка для демонстрации
  isLoggedIn.value = true
  userName.value = 'Иванов И.И.'

  authDialog.value?.close()
}

const handleRegister = (userData) => {
  // Здесь должна быть логика регистрации
  console.log('Registration attempt with:', userData)

  // Временная заглушка для демонстрации
  isLoggedIn.value = true
  userName.value = userData.name

  authDialog.value?.close()
}

const handleDialogClose = () => {
  // Можно добавить дополнительную логику при закрытии диалога
}
</script>

<style scoped>
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: #777777;
  padding-top: 10px;
  margin-bottom: 10px;
}

.index-page {
  padding: 20px;
  font-family: 'Inter', sans-serif;
}

.user-controls {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
  margin-bottom: 5px;
}

.user-name-placeholder {
  padding: 8px 12px;
  background-color: #f0f0f0;
  border-radius: 4px;
  font-weight: 500;
}

.login-logout-button {
  padding: 8px 16px;
  background-color: #4a76a8;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.login-logout-button:hover {
  background-color: #3a5f8a;
}

.buttons-container {
  display: flex;
  gap: 16px;
  align-items: top;
}

.buttons-container * {
  flex: 1;
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
  gap: 4px;
  overflow-x: auto;
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
  gap: 4px;
  overflow-x: auto;
}

.empty-status-card {
  width: 150px;
  height: 80px;
  visibility: hidden;
  flex-shrink: 0;
}
</style>