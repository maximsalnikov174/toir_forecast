<template>
  <q-card
    class="car-card"
    :class="{ 'bg-pink-2': isLowDistance, 'selected-division': isSelectedDivision }"
    @click="copyGrzToClipboard"
    style="cursor: pointer;"
  >
    <q-card-section horizontal>
      <q-img
        v-if="statusImage"
        :src="statusImage"
        class="car-image"
      />
      <div v-else class="car-image-placeholder" @click.stop="openAddStatusDialog">
        <span class="plus-icon">+</span>
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
        :on-submit-success="onStatusAdded"
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
    id: {
      type: Number,
      required: true
    },
    divId: {
      type: [String, Number],
      default: null
    }
  },

  methods: {
    onStatusAdded() {
      this.$emit('status-added') // Эмитим событие при успешном добавлении
    }
  },
  setup(props) {
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

    const openAddStatusDialog = () => {
      // Проверяем, что пользователь суперпользователь ИЛИ его подразделение совпадает с выбранным
      if (authStore.user?.is_superuser || authStore.user?.organization_id === selectedDivId.value) {
        showAddStatusDialog.value = true
      }
    }

    const copyGrzToClipboard = () => {
      // Добавляем % перед и после GRZ
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

    return {
      isLowDistance,
      isSelectedDivision,
      statusImage,
      copyGrzToClipboard,
      showAddStatusDialog,
      openAddStatusDialog
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
  opacity: 0;
  font-size: 24px;
  font-weight: bold;
  color: #555;
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
</style>