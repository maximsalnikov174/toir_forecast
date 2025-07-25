<template>
  <q-card
    class="car-card"
    :class="{ 'bg-pink-2': isLowDistance }"
    @click="copyGrzToClipboard"
    style="cursor: pointer;"
  >
    <q-card-section horizontal>
      <q-img
        src="your-image-path-here"
        class="car-image"
      />

      <q-card-section class="car-content">
        <div class="characteristic-subtitle">{{ model }}</div>
        <div class="car-grz">{{ grz }}</div>
        <div class="row items-center">
          <div class="additional-info">{{ requestReading }} км</div>
          <div class="car-value">{{ daliDistanse }} км/день </div>
        </div>
      </q-card-section>
    </q-card-section>
  </q-card>
</template>

<script>
import { defineComponent, computed } from 'vue'
import { useQuasar } from 'quasar'

export default defineComponent({
  name: 'CarCard',
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
    }
  },
  setup(props) {
    const $q = useQuasar()

    const isLowDistance = computed(() => {
      return props.daliDistanse < 1
    })

    const copyGrzToClipboard = () => {
      // Удаляем все нецифровые символы (буквы, пробелы, дефисы и т.д.)
      const cleanGrz = props.grz.replace(/[^А-Яа-я0-9]/g, '')

      navigator.clipboard.writeText(cleanGrz)
        .then(() => {
          $q.notify({
            message: 'GRZ скопирован в буфер обмена',
            color: 'positive',
            position: 'top',
            timeout: 1000
          })
        })
        .catch(err => {
          console.error('Не удалось скопировать GRZ:', err)
          $q.notify({
            message: 'Ошибка при копировании GRZ',
            color: 'negative',
            position: 'top',
            timeout: 1000
          })
        })
    }

    return {
      isLowDistance,
      copyGrzToClipboard
    }
  }
})
</script>

<style scoped>
.car-card {
  width: 212px;
  height: 80px;
  background: #FFFFFF;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-right: 20px;
  flex-shrink: 0;
  transition: transform 0.2s;
}

.car-card:hover {
  transform: translateY(-2px);
}

.car-image {
  width: 38px;
  height: 38px;
  margin: 21px 0 0 16px;
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