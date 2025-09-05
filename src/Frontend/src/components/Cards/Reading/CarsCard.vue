<template>
  <q-card
    class="car-card"
    :class="{ 'bg-pink-2': isLowDistance, 'selected-division': isSelectedDivision }"
    @click="copyGrzToClipboard"
    style="cursor: pointer;"
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
          >
            <q-img
              :src="getStatusImage(status.special_status_id)"
              class="status-image"
              :class="{ 'small': activeStatuses.length > 1 }"
            />
            <q-tooltip
              class="bg-red text-body2"
              anchor="top middle"
              self="bottom middle"
              :offset="[0, 10]"
            >
              <div class="tooltip-content">
                <div v-if="status.comment" class="tooltip-row">
                  <q-icon name="comment" size="sm" />
                  <span>{{ status.comment }}</span>
                </div>
                <div v-if="status.date_left" class="tooltip-row">
                  <q-icon name="event" size="sm" />
                  <span>До: {{ formatDate(status.date_left) }}</span>
                </div>
              </div>
            </q-tooltip>
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

    <q-dialog v-model="showAddStatusDialog">
      <AddCarSpecialStatus
        :car-id="id"
        :grz="grz"
        @close="showAddStatusDialog = false"
        @submit-success="onStatusAdded"
      />
    </q-dialog>
  </q-card>
</template>

<script>
import { defineComponent, computed, ref } from 'vue'
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
  emits: ['status-added'],
  setup(props, { emit }) {
    const $q = useQuasar()
    const showAddStatusDialog = ref(false)
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

    const openAddStatusDialog = () => {
      if (showPlusIcon.value) {
        showAddStatusDialog.value = true
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
      openAddStatusDialog,
      showPlusIcon,
      onStatusAdded
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

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tooltip-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>