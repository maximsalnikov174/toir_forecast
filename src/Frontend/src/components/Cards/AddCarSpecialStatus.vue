<template>
  <q-card style="min-width: 350px">
    <q-card-section>
      <div class="text-h6">Добавить статус</div>

      <!-- Поле выбора статусов -->
      <q-select
        v-model="selectedSpecialStatuses"
        :options="statusOptionsWithImages"
        option-label="name"
        option-value="id"
        label="Статус"
        filled
        map-options
        emit-value
        :loading="loading"
        multiple
        clearable
        class="q-mb-md"
      >
        <template v-slot:option="scope">
          <q-item v-bind="scope.itemProps">
            <q-item-section avatar>
              <q-img
                :src="getStatusImage(scope.opt.id)"
                width="24px"
                height="24px"
              />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ scope.opt.name }}</q-item-label>
            </q-item-section>
          </q-item>
        </template>
      </q-select>

      <!-- Поле выбора даты -->
      <q-input
        v-model="dateValue"
        label="Дата"
        filled
        mask="##.##.####"
        placeholder="ДД.ММ.ГГГГ"
        hint="Формат: ДД.ММ.ГГГГ"
        :rules="[validateDate]"
        class="q-mb-md"
      >
        <template v-slot:append>
          <q-icon name="event" class="cursor-pointer">
            <q-popup-proxy cover transition-show="scale" transition-hide="scale">
              <q-date v-model="dateValue" mask="DD.MM.YYYY" />
            </q-popup-proxy>
          </q-icon>
        </template>
      </q-input>

      <!-- Поле для комментария -->
      <q-input
        v-model="commentValue"
        label="Комментарий"
        filled
        type="textarea"
        autogrow
        class="q-mb-md"
      />
    </q-card-section>

    <q-card-actions align="center">
      <q-btn label="добавить статус" color="primary" @click="saveData" />
    </q-card-actions>
  </q-card>
</template>

<script>
import { defineComponent, computed, ref } from 'vue'
import { useStatusOptions } from '../Functions/ButtonSelectGroupTs.js'
import { date as qDate } from 'quasar'

// Импортируем изображения статусов
import status1 from 'src/assets/1.png'
import status2 from 'src/assets/2.png'
import status3 from 'src/assets/3.png'
import status4 from 'src/assets/4.png'
import status5 from 'src/assets/5.png'

export default defineComponent({
  name: 'AddCarSpecialStatus',
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const {
      statusOptions,
      selectedSpecialStatuses,
      loading
    } = useStatusOptions()

    const dateValue = ref('')
    const commentValue = ref('')

    // Получаем изображение статуса по ID
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

    // Добавляем изображения в опции статусов
    const statusOptionsWithImages = computed(() => {
      return statusOptions.value?.map(option => ({
        ...option,
        image: getStatusImage(option.id)
      })) || []
    })

    // Валидация даты
    const validateDate = (val) => {
      if (!val) return true // Разрешаем пустое значение

      const [day, month, year] = val.split('.')
      const isValid = qDate.isValid(`${year}-${month}-${day}`)
      return isValid || 'Некорректная дата'
    }

    // Сохранение данных
    const saveData = () => {
      emit('save', {
        statuses: selectedSpecialStatuses.value,
        date: dateValue.value,
        comment: commentValue.value
      })
      emit('close')
    }

    return {
      statusOptionsWithImages,
      selectedSpecialStatuses,
      loading,
      dateValue,
      commentValue,
      getStatusImage,
      validateDate,
      saveData
    }
  }
})
</script>

<style scoped>
.q-item__section--avatar {
  min-width: 30px;
}
</style>