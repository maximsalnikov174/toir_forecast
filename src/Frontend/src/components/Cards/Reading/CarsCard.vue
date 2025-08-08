<template>
  <q-card
    class="car-card"
    :class="{ 'bg-pink-2': isLowDistance, 'selected-division': isSelectedDivision }"
    @click="copyGrzToClipboard"
    style="cursor: pointer;"
  >
    <q-card-section horizontal>
      <div class="status-image-container">
        <q-img
          v-if="statusImage"
          :src="statusImage"
          class="car-image"
        />
        <q-tooltip
         class="bg-red text-body2"
          v-if="hasStatusInfo"
          anchor="top middle"
          self="bottom middle"
          :offset="[0, 10]"
        >
          <div class="tooltip-content">
            <div v-if="specialStatusComment" class="tooltip-row">
              <q-icon name="comment" size="sm" />
              <span>{{ specialStatusComment }}</span>
            </div>
            <div v-if="specialStatusDateLeft" class="tooltip-row">
              <q-icon name="event" size="sm" />
              <span>До: {{ formattedDateLeft }}</span>
            </div>
          </div>
        </q-tooltip>
        <div
          v-else
          class="car-image-placeholder"
          @click.stop="openAddStatusDialog"
        >
          <span class="plus-icon" v-if="showPlusIcon">+</span>
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
      type: Number,
      required: false,
    },
    specialStatusId: {
      type: Number,
      required: false,
    },
    specialStatusComment: {
      type: String,
      required: false,
      default: ''
    },
    specialStatusDateLeft: {
      type: String,
      required: false,
      default: ''
    },
    id: {
      type: Number,
      required: true
    },
    divId: {
      type: [String, Number],
      default: null
    }
  },
  emits: ['status-added'],
  setup(props, { emit }) {
    const $q = useQuasar()
    const showAddStatusDialog = ref(false)
    const { selectedDivId } = useFilterStore()
    const authStore = useAuthStore()

    const isLowDistance = computed(() => {
      return props.daliDistanse < 1
    })

    const isSelectedDivision = computed(() => {
      return props.divId && props.divId === selectedDivId.value
    })

    const showPlusIcon = computed(() => {
      return authStore.user?.is_superuser || authStore.user?.organization_id === selectedDivId.value
    })

    const statusImage = computed(() => {
      switch(props.specialStatusId) {
        case 1: return status1
        case 2: return status2
        case 3: return status3
        case 4: return status4
        case 5: return status5
        default: return null
      }
    })

    const formattedDateLeft = computed(() => {
      if (!props.specialStatusDateLeft) return ''
      const date = new Date(props.specialStatusDateLeft)
      return date.toLocaleDateString('ru-RU')
    })

    const hasStatusInfo = computed(() => {
      return props.specialStatusComment || props.specialStatusDateLeft
    })

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
      isLowDistance,
      isSelectedDivision,
      statusImage,
      formattedDateLeft,
      hasStatusInfo,
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

.status-image-container {
  position: relative;
  display: flex;
}

.car-image {
  width: 38px;
  height: 38px;
  margin: 21px 0 0 16px;
  object-fit: contain;
}

.car-image-placeholder {
  width: 38px;
  height: 38px;
  margin: 21px 0 0 16px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  cursor: pointer;
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