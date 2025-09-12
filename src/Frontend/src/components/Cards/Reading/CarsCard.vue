<template>
  <q-card
    class="car-card"
    :class="{ 'bg-pink-2': isLowDistance, 'selected-division': isSelectedDivision }"
    @click="copyGrzToClipboard"
    style="cursor: pointer;"
    ref="cardRef"
  >
    <q-card-section horizontal>
      <div class="status-images-container">
        <div
          class="car-image-placeholder"
          :class="{
            'has-status': activeStatuses.length > 0,
            'multiple-statuses': activeStatuses.length > 1
          }"
          @click.stop="openAddStatusDialog"
        >
          <!-- Отображаем все активные статусы -->
          <div
            v-for="(status, index) in activeStatuses"
            :key="index"
            class="status-image-wrapper"
            :class="{ 'small-image': activeStatuses.length > 1 }"
            @mouseenter="showStatusPopup(status, $event)"
            @mouseleave="hideStatusPopup"
          >
            <q-img
              :src="getStatusImage(status.special_status_id)"
              class="status-image"
              :class="{ 'small': activeStatuses.length > 1 }"
            />
          </div>

          <!-- Плюсик для добавления статуса -->
          <span class="plus-icon" v-if="showPlusIcon && activeStatuses.length === 0">+</span>
        </div>
      </div>

      <q-card-section class="car-content">
        <div class="characteristic-subtitle">{{ model }}</div>
        <div class="car-grz">{{ grz }}</div>
        <div class="row items-center">
          <div class="additional-info">{{ requestReading }} <span style="color: gray;">км</span></div>
          <div class="car-value">{{ daliDistanse }} <span style="color: gray;">км/день</span></div>
        </div>
      </q-card-section>
    </q-card-section>

    <!-- Попап с информацией о статусе (вне карточки) -->
    <div
      v-if="currentStatus && isPopupVisible"
      class="status-popup-global"
      :style="popupStyle"
      @mouseenter="keepPopupVisible"
      @mouseleave="hideStatusPopup"
      ref="statusPopupRef"
    >
      <div class="popup-header">
        <span>Статус автомобиля</span>
        <q-icon
          name="close"
          class="close-icon"
          @click="openRemoveStatusDialog(currentStatus)"
        />
      </div>

      <div class="popup-content">
        <div v-if="currentStatus.comment" class="popup-row">
          <q-icon name="comment" size="sm" />
          <span>{{ currentStatus.comment }}</span>
        </div>
        <div v-if="currentStatus.date_left" class="popup-row">
          <q-icon name="event" size="sm" />
          <span>До: {{ formatDate(currentStatus.date_left) }}</span>
        </div>
      </div>
    </div>

    <q-dialog v-model="showAddStatusDialog">
      <AddCarSpecialStatus
        :car-id="id"
        :grz="grz"
        @close="showAddStatusDialog = false"
        @submit-success="onStatusAdded"
      />
    </q-dialog>

    <!-- Диалог подтверждения удаления статуса -->
    <q-dialog v-model="showRemoveStatusDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="warning" color="primary" text-color="white" />
          <span class="q-ml-sm">Вы хотите убрать статус?</span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Отмена" color="primary" v-close-popup />
          <q-btn flat label="Подтвердить" color="primary" @click="removeStatus" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-card>
</template>

<script>
import { defineComponent, computed, ref, nextTick } from 'vue'
import { useQuasar } from 'quasar'
import AddCarSpecialStatus from '../AddCarSpecialStatus.vue'
import { useFilterStore } from 'src/components/Functions/FilterStoreAcceptButton'
import { useAuthStore } from 'src/stores/useAuthStore'

import status1 from 'src/assets/1.png'
import status2 from 'src/assets/2.png'
import status3 from 'src/assets/3.png'
import status4 from 'src/assets/4.png'
import status5 from 'src/assets/5.png'

export default defineComponent({
  name: 'CarCard',
  components: {
    AddCarSpecialStatus
  },
  props: {
    grz: {
      type: String,
      required: true
    },
    model: {
      type: String,
      required: false,
      default: ''
    },
    daliDistanse: {
      type: Number,
      required: false,
    },
    requestReading: {
      type: [String, Number],
      required: false,
    },
    id: {
      type: Number,
      required: true
    },
    divId: {
      type: [String, Number],
      default: null
    },
    statusAssociations: {
      type: Array,
      default: () => []
    }
  },
  emits: ['status-added', 'status-removed'],
  setup(props, { emit }) {
    const $q = useQuasar()
    const showAddStatusDialog = ref(false)
    const showRemoveStatusDialog = ref(false)
    const statusToRemove = ref(null)
    const isPopupVisible = ref(false)
    const isHoveringPopup = ref(false)
    const currentStatus = ref(null)
    const popupPosition = ref({ top: 0, left: 0 })
    const cardRef = ref(null)
    const statusPopupRef = ref(null)
    const { selectedDivId } = useFilterStore()
    const authStore = useAuthStore()

    const activeStatuses = computed(() => {
      return props.statusAssociations.filter(status => status.is_active) || []
    })

    const isLowDistance = computed(() => {
      return props.daliDistanse < 1
    })

    const isSelectedDivision = computed(() => {
      return props.divId && props.divId === selectedDivId.value
    })

    const showPlusIcon = computed(() => {
      return authStore.user?.is_superuser || authStore.user?.users_organization.id === selectedDivId.value
    })

    const popupStyle = computed(() => {
      return {
        top: `${popupPosition.value.top}px`,
        left: `${popupPosition.value.left}px`,
        display: isPopupVisible.value ? 'block' : 'none'
      }
    })

    const getStatusImage = (statusId) => {
      switch(statusId) {
        case 1: return status1
        case 2: return status2
        case 3: return status3
        case 4: return status4
        case 5: return status5
        default: return null
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString('ru-RU')
    }

    // Функция для нахождения максимального z-index на странице
    const findMaxZIndex = () => {
      const allElements = document.querySelectorAll('*')
      let maxZIndex = 9999998

      allElements.forEach(el => {
        if (el === statusPopupRef.value) return // Пропускаем сам попап

        const zIndex = parseInt(window.getComputedStyle(el).zIndex)
        if (!isNaN(zIndex) && zIndex > maxZIndex) {
          maxZIndex = zIndex
        }
      })

      return maxZIndex + 1
    }

    // Функция для установки максимального z-index
    const setMaxZIndex = () => {
      if (statusPopupRef.value) {
        const maxZIndex = findMaxZIndex()
        statusPopupRef.value.style.zIndex = maxZIndex.toString()
      }
    }

    const showStatusPopup = (status, event) => {
      currentStatus.value = status

      // Получаем позицию элемента статуса относительно документа
      const statusElement = event.target
      const statusRect = statusElement.getBoundingClientRect()

      // Позиционируем попап относительно документа
      popupPosition.value = {
        top: statusRect.bottom + window.scrollY - 340,
        left: statusRect.left + window.scrollX
      }

      isPopupVisible.value = true
      isHoveringPopup.value = false

      // Устанавливаем максимальный z-index после отображения попапа
      nextTick(() => {
        setMaxZIndex()
      })
    }

    const hideStatusPopup = () => {
      isHoveringPopup.value = false
      // Добавляем небольшую задержку перед скрытием, чтобы можно было переместить курсор на попап
      setTimeout(() => {
        if (!isHoveringPopup.value) {
          isPopupVisible.value = false
        }
      }, 100)
    }

    const keepPopupVisible = () => {
      isHoveringPopup.value = true
    }

    const openAddStatusDialog = () => {
      if (showPlusIcon.value) {
        showAddStatusDialog.value = true
      }
    }

    const openRemoveStatusDialog = (status) => {
      if (showPlusIcon.value) {
        statusToRemove.value = status
        isPopupVisible.value = false // Скрываем попап при открытии диалога
        showRemoveStatusDialog.value = true
      }
    }

    const removeStatus = async () => {
      try {
        // Здесь должен быть API-запрос для удаления статуса
        // Например: await api.removeCarStatus(statusToRemove.value.id)

        // После успешного удаления:
        $q.notify({
          message: 'Статус успешно удален',
          color: 'positive',
          position: 'top',
          timeout: 1000
        })

        // Эмитируем событие для обновления родительского компонента
        emit('status-removed', statusToRemove.value)

        // Закрываем диалог
        showRemoveStatusDialog.value = false
        statusToRemove.value = null
      } catch (error) {
        console.error('Ошибка при удалении статуса:', error)
        $q.notify({
          message: 'Ошибка при удалении статуса',
          color: 'negative',
          position: 'top',
          timeout: 1000
        })
      }
    }

    const copyGrzToClipboard = () => {
      const grzWithPercent = `%${props.grz}%`
      const textArea = document.createElement('textarea')
      textArea.value = grzWithPercent
      textArea.style.position = 'fixed'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      try {
        const successful = document.execCommand('copy')
        if (successful) {
          $q.notify({
            message: 'GRZ скопирован в буфер обмена',
            color: 'positive',
            position: 'top',
            timeout: 1000
          })
        } else {
          throw new Error('Copy command unsuccessful')
        }
      } catch (err) {
        console.error('Не удалось скопировать GRZ:', err)
        $q.notify({
          message: 'Ошибка при копировании GRZ',
          color: 'negative',
          position: 'top',
          timeout: 1000
        })
      } finally {
        document.body.removeChild(textArea)
      }
    }

    const onStatusAdded = () => {
      emit('status-added')
      showAddStatusDialog.value = false
    }

    return {
      activeStatuses,
      isLowDistance,
      isSelectedDivision,
      getStatusImage,
      formatDate,
      copyGrzToClipboard,
      showAddStatusDialog,
      showRemoveStatusDialog,
      openAddStatusDialog,
      openRemoveStatusDialog,
      removeStatus,
      showPlusIcon,
      onStatusAdded,
      showStatusPopup,
      hideStatusPopup,
      keepPopupVisible,
      isPopupVisible,
      currentStatus,
      popupStyle,
      cardRef,
      statusPopupRef
    }
  }
})
</script>

<style scoped>
.car-card {
  width: 212px;
  height: 80px;
  background: #E9E7DA;
  border-radius: 8px;
  border: 1px solid #000000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-right: 20px;
  flex-shrink: 0;
  transition: transform 0.2s;
  position: relative;
}

.car-card:hover {
  transform: translateY(-2px);
}

.car-card.selected-division {
  border: 2px solid purple;
}

.status-images-container {
  position: relative;
  display: flex;
  padding: 21px 0 0 16px;
}

.car-image-placeholder {
  width: 38px;
  height: 38px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  cursor: pointer;
}

.car-image-placeholder.has-status {
  background-color: transparent;
}

.car-image-placeholder.multiple-statuses {
  flex-wrap: wrap;
  gap: 2px;
  padding: 2px;
  align-content: flex-start;
}

.status-image-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-image-wrapper.small-image {
  flex: 1;
  min-width: 16px;
}

.status-image {
  width: 38px;
  height: 38px;
  object-fit: contain;
}

.status-image.small {
  width: 16px;
  height: 16px;
}

.plus-icon {
  font-size: 24px;
  font-weight: bold;
  color: #555;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.car-image-placeholder:hover .plus-icon {
  opacity: 1;
}

.car-content {
  padding: 10px 0 0 8px;
}

.characteristic-subtitle {
  width: 125px;
  height: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 200;
  font-size: 10px;
  line-height: 100%;
  color: #000000;
  margin-bottom: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.car-grz {
  width: 150px;
  height: 22px;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 18px;
  line-height: 100%;
  color: #000000;
  margin-bottom: 10px;
}

.additional-info {
  width: 71px;
  height: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  font-size: 10px;
  line-height: 100%;
  color: #000000;
}

.car-value {
  width: 71px;
  height: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  font-size: 10px;
  line-height: 100%;
  color: #000000;
  margin-left: 5px;
}

/* Стили для глобального попапа статуса (вне карточки) */
.status-popup-global {
  position: fixed;
  z-index: 10000; /* Базовый высокий z-index */
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  min-width: 200px;
  pointer-events: auto;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
}

.close-icon {
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
}

.close-icon:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.popup-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.popup-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>