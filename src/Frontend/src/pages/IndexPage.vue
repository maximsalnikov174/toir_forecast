<template>
  <div class="index-page">
    <div class="header-info">
      <!-- Кнопка возврата вверх -->
      <button v-show="showScrollButton" class="scroll-to-top" @click="scrollToTop">↑</button>
      <div class="date-and-manual">
        <div class="current-date">{{ currentDate }}</div>
        <button class="manual-button" @click="colorsDialog.open()">
          <span class="material-icons">menu_book</span>
        </button>
      </div>
      <div class="user-controls">
        <div class="user-name-placeholder">
          {{
            authStore.user?.name && authStore.user?.surname
              ? `${authStore.user.name} ${authStore.user.surname}`
              : 'Гость'
          }}
        </div>
        <button class="login-logout-button" @click="handleAuth">
          {{ authStore.isAuth ? 'Выйти' : 'Войти' }}
        </button>
      </div>
    </div>

    <ColorsOfRepairShops ref="colorsDialog" />

    <LoginRegisterDialog
      ref="authDialog"
      @login="handleLogin"
      @register="handleRegister"
      @close="handleDialogClose"
    />

    <div class="buttons-container">
      <template v-if="shouldShowDivisionControls">
        <division-select />
        <minimal-status />
        <GroupTs />
        <HideServiceWorkWithZvr />
        <ToAccept
          ref="toAcceptRef"
          @tableDataFetched="handleTableDataFetched"
          @servicesFetched="handleServicesFetched"
          @carsFetched="handleCarsFetched"
        />
      </template>
    </div>

    <div class="data-container">
      <!-- Заголовок с именами сервисов -->
      <div class="services-header sticky-header">
        <div class="cars-header-placeholder">
          <LetterSearch
            :cars="cars"
            :active-letters="activeLetters"
            :active-digits="activeDigits"
            @update:activeLetters="activeLetters = $event"
            @update:activeDigits="activeDigits = $event"
            @filter-change="handleFilterChange"
          />
        </div>
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
        <div v-for="(car,) in filteredCars" :key="car.personal_id" class="data-row">
          <CarCard
            :grz="car.grz"
            :model="car.car_model?.name || ''"
            :daliDistanse="car.indicators?.daily_distance"
            :requestReading="car.indicators?.request_reading"
            :id="car.id"
            :status-associations="car.status_associations || []"
            @status-added="handleStatusAdded"
          />
          <div class="status-cards">
            <template v-for="(item, itemIndex) in getTableDataForCar(car)" :key="itemIndex">
              <ServiceStatusCard
                v-if="item"
                :Divergence="item.divergence"
                :LastServiceDate="item.last_service_date"
                :DBSWCAN="item.days_between_service_work_completed_and_now"
                :request_status_id="item.request_status_id"
                :zvr_create_date="item.zvr_create_date"
                :zvr_number="item.zvr_number"
                :service_work_completed="item.service_work_completed"
                :id="item.id"
                :station="item.station"
                @submitted="handleApply"
                :onSubmitSuccessMaster="loadMasterData"
                :total_docs_count="item.total_docs_count"
                :total_docs_processed_count="item.total_docs_processed_count"
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
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import MinimalStatus from '../components/UI/Button/MinimalStatus.vue'
import DivisionSelect from '../components/UI/Button/DivisionSelect.vue'
import GroupTs from '../components/UI/Button/GroupTs.vue'
import HideServiceWorkWithZvr from '../components/UI/Button/HideServiceWorkWithZvr.vue'
import ToAccept from 'src/components/UI/Button/ToAccept.vue'
import ServiceNamesCard from '../components/Cards/Reading/ServiceNamesCards.vue'
import ServiceStatusCard from '../components/Cards/Reading/ServiceStatusCard.vue'
import CarCard from '../components/Cards/Reading/CarsCard.vue'
import LoginRegisterDialog from 'src/components/UI/Windows/LoginRegisterDialog.vue'
import { useAuthStore } from 'src/stores/useAuthStore'
import { getCurrentDateInDB } from 'src/components/Functions/CurrentDateInDB'
import ColorsOfRepairShops from '../components/Cards/ColorsOfRepairShops.vue'
import { masterApi } from 'src/components/Functions/masterApi.js'
import LetterSearch from '../components/Cards/Reading/LetterSearch.vue'

const loading = ref(false)
const showScrollButton = ref(false)
const colorsDialog = ref(null)
const tableData = ref([])
const services = ref([])
const cars = ref([])
const authStore = useAuthStore()
const authDialog = ref(null)
const currentDate = ref('Загрузка даты...')
const toAcceptRef = ref(null)
const activeLetters = ref([])
const activeDigits = ref([])

// Функция для получения данных таблицы для конкретной машины
const getTableDataForCar = (car) => {
  const index = cars.value.findIndex(c => c.personal_id === car.personal_id)
  return index !== -1 ? tableData.value[index] : []
}

// Вычисляем отфильтрованные машины
const filteredCars = computed(() => {
  if (activeLetters.value.length === 0 && activeDigits.value.length === 0) {
    return cars.value
  }

  return cars.value.filter(car => {
    const grzWithoutSpaces = car.grz.replace(/\s+/g, '')
    const firstChar = grzWithoutSpaces.charAt(0)

    // Проверяем букву
    const isLetterMatch = activeLetters.value.length === 0 ||
                         (firstChar && /[А-ЯA-Z]/.test(firstChar) &&
                          activeLetters.value.includes(firstChar.toUpperCase()))

    // Проверяем цифру (ищем первую цифру в GRZ)
    let isDigitMatch = activeDigits.value.length === 0
    if (!isDigitMatch) {
      const firstDigit = grzWithoutSpaces.match(/\d/)?.[0]
      isDigitMatch = firstDigit && activeDigits.value.includes(firstDigit)
    }

    return isLetterMatch && isDigitMatch
  })
})

const shouldShowDivisionControls = computed(() => {
  if (!authStore.isAuth) return true
  if (!authStore.user?.users_organization) return true
  return authStore.user.users_organization.station_id === null
})

const isMasterUser = computed(() => {
  return (
    authStore.isAuth &&
    authStore.user?.users_organization &&
    authStore.user.users_organization.station_id !== null
  )
})

const checkScrollPosition = () => {
  showScrollButton.value = window.scrollY > 300
}

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  })
}

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
  if (authStore.isAuth) {
    authStore.clearAuthData()
    // Очищаем данные при выходе
    tableData.value = []
    services.value = []
    cars.value = []
  } else {
    authDialog.value?.open()
  }
}

const handleDialogClose = () => {
  // Дополнительная логика при закрытии диалога
}

const handleApply = () => {
  toAcceptRef.value?.handleApply()
}

const handleStatusAdded = () => {
  toAcceptRef.value?.handleApply()
}

// Функция для загрузки данных мастера
const loadMasterData = async () => {
  if (!isMasterUser.value) return

  try {
    loading.value = true

    const token = authStore.token
    if (!token) {
      console.error('Токен не найден')
      return
    }

    console.log('Загрузка данных для мастера...')

    // Используем API функции из отдельного файла
    const masterData = await masterApi.loadAllMasterData(token)

    handleTableDataFetched(masterData.tableData)
    handleServicesFetched(masterData.services)
    handleCarsFetched(masterData.cars)
  } catch (error) {
    console.error('Ошибка при загрузке данных мастера:', error)
  } finally {
    loading.value = false
  }
}



// Также следим за изменениями пользователя
watch(
  () => authStore.user,
  (newUser) => {
    if (
      newUser?.users_organization?.station_id !== null &&
      newUser?.users_organization?.station_id !== undefined &&
      authStore.isAuth
    ) {
      console.log(
        'Данные пользователя изменились, station_id:',
        newUser.users_organization.station_id,
      )
      loadMasterData()
    }
  },
  { deep: true },
)

onMounted(async () => {
  try {
    const dateData = await getCurrentDateInDB()
    currentDate.value = dateData.current_db_status
  } catch (error) {
    currentDate.value = 'Ошибка загрузки даты'
    console.error(error)
  }

  window.addEventListener('scroll', checkScrollPosition)

  // Автоматически загружаем данные для мастера при монтировании, если пользователь уже авторизован
  if (isMasterUser.value) {
    console.log('Автоматическая загрузка данных для мастера при монтировании')
    loadMasterData()
  }
})

onUnmounted(() => {
  window.removeEventListener('scroll', checkScrollPosition)
})
</script>

<style scoped>
/* Стили остаются без изменений */
.date-and-manual {
  display: flex;
  align-items: center;
  gap: 4px;
}

.current-date {
  font-weight: 500;
  color: #3a3939;
  padding: 8px 8px 8px 12px;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 600;
}

.manual-button {
  background: none;
  border: none;
  cursor: pointer;
  color: #000000;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: -4px;
}

.manual-button:hover {
  background-color: #f0f0f0;
}

.material-icons {
  font-size: 25px;
}

.scroll-to-top {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: #4a76a8;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  transition: background-color 0.3s;
}

.scroll-to-top:hover {
  background-color: #3a5f8a;
}

.header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

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

/* Добавляем новые стили для поиска по буквам */
.cars-header-placeholder {
  width: 242px;
  display: flex;
  flex-direction: column;
}

.service-names-row {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  flex: 1;
  position: relative;

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
