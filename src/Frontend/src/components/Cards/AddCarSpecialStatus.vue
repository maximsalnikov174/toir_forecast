<template>
  <q-card style="min-width: 350px">
    <q-card-section>
      <div class="text-h6">Установить статус ТС: &laquo;{{ grz }}&raquo;</div>

      <q-select
        v-model="selectedSpecialStatus"
        :options="statusOptionsWithImages"
        option-label="name"
        option-value="id"
        label="Выбрать из списка"
        filled
        map-options
        emit-value
        :loading="loading"
        clearable
        class="q-mb-md"
      >
        <template v-slot:option="scope">
          <q-item v-bind="scope.itemProps">
            <q-item-section avatar>
              <q-img :src="getStatusImage(scope.opt.id)" width="24px" height="24px" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ scope.opt.name }}</q-item-label>
            </q-item-section>
          </q-item>
        </template>
      </q-select>

      <q-input
        v-model="dateValue"
        label="Указать дату окончания его действия"
        filled
        mask="##.##.####"
        placeholder="ДД.ММ.ГГГГ"
        hint="Например: 31.12.2025"
        :rules="[validateDate]"
        class="q-mb-md"
      >
        <template v-slot:append>
          <q-icon name="event" class="cursor-pointer">
            <q-popup-proxy cover transition-show="scale" transition-hide="scale">
              <q-date
                v-model="dateValue"
                mask="DD.MM.YYYY"
                :options="disablePastDates"
                today-btn
                first-day-of-week="1"
                navigation-min-year-month="2023/01"
                navigation-max-year-month="2030/12"
                color="primary"
              >
                <template v-slot:default>
                  <div class="row justify-end q-gutter-sm q-pa-sm">
                    <q-btn
                      label="Отмена"
                      color="grey"
                      v-close-popup
                      flat
                    />
                    <q-btn
                      label="Применить"
                      color="primary"
                      v-close-popup
                    />
                  </div>
                </template>
              </q-date>
            </q-popup-proxy>
          </q-icon>
        </template>
      </q-input>

      <q-input
        v-model="commentValue"
        label="Оставить комментарий (опционально)"
        filled
        type="textarea"
        autogrow
        class="q-mb-md"
      />
    </q-card-section>

    <q-card-actions align="center">
      <q-btn
        label="Установить"
        color="primary"
        @click="saveData"
        :loading="isSaving"
        :disable="!selectedSpecialStatus"
      />
    </q-card-actions>
  </q-card>
</template>

<script>
import { defineComponent, computed, ref } from 'vue'
import { useAuthorizedStatusOptions } from '../Functions/AuthorizeSelectGroupTs.js'
import { date as qDate } from 'quasar'
import { api } from 'boot/axios'
import { useAuthStore } from 'src/stores/useAuthStore'
import { Quasar } from 'quasar'
import ru from 'quasar/lang/ru'

// Установка русской локали
Quasar.lang.set(ru)

import status1 from 'src/assets/1.png'
import status2 from 'src/assets/2.png'
import status3 from 'src/assets/3.png'
import status4 from 'src/assets/4.png'
import status5 from 'src/assets/5.png'

export default defineComponent({
  name: 'AddCarSpecialStatus',
  props: {
    carId: {
      type: Number,
      required: true,
      validator: value => value > 0
    },
    onSubmitSuccess: {
      type: Function,
      default: null
    },
    grz: {
      type: String,
      required: true
    },
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const { statusOptions, loading } = useAuthorizedStatusOptions()
    const selectedSpecialStatus = ref(null)
    const dateValue = ref('')
    const commentValue = ref('')
    const isSaving = ref(false)
    const authStore = useAuthStore()

    const getStatusImage = (statusId) => {
      switch (statusId) {
        case 1: return status1
        case 2: return status2
        case 3: return status3
        case 4: return status4
        case 5: return status5
        default: return null
      }
    }

    const statusOptionsWithImages = computed(() => {
      return statusOptions.value?.map(option => ({
        ...option,
        image: getStatusImage(option.id),
      })) || []
    })

    const disablePastDates = (date) => {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const selectedDate = new Date(date)
      return selectedDate >= today
    }

    const validateDate = (val) => {
      if (!val) return true

      const [day, month, year] = val.split('.')
      if (!qDate.isValid(`${year}-${month}-${day}`)) {
        return 'Некорректная дата'
      }

      const inputDate = new Date(year, month - 1, day)
      const today = new Date()
      today.setHours(0, 0, 0, 0)

      if (inputDate < today) {
        return 'Дата не может быть раньше сегодняшнего дня'
      }

      return true
    }

    const formatDateForApi = (dateStr) => {
      if (!dateStr) return null
      const [day, month, year] = dateStr.split('.')
      return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
    }

    const saveData = async () => {
      if (!selectedSpecialStatus.value) {
        alert('Пожалуйста, выберите статус')
        return
      }

      isSaving.value = true

      try {
        const formattedDate = formatDateForApi(dateValue.value)

        await api.patch(`/car/${props.carId}/add_special_status`, null, {
          params: {
            special_status_id: selectedSpecialStatus.value,
            date_from_user: formattedDate || '',
            comment: commentValue.value || '',
          },
          headers: {
            Authorization: `Bearer ${authStore.token}`,
          },
        })

        emit('save')
        emit('close')
        if (props.onSubmitSuccess) {
          props.onSubmitSuccess()
        }
      } catch (error) {
        console.error('Ошибка при сохранении статуса:', error)
        alert(`Ошибка: ${error.response?.data?.message || error.message}`)
      } finally {
        isSaving.value = false
      }
    }

    return {
      statusOptionsWithImages,
      selectedSpecialStatus,
      loading,
      dateValue,
      commentValue,
      isSaving,
      getStatusImage,
      validateDate,
      disablePastDates,
      saveData,
    }
  },
})
</script>

<style scoped>
.q-item__section--avatar {
  min-width: 30px;
}
</style>