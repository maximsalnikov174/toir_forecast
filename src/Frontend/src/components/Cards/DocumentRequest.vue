<template>
  <q-dialog v-model="showDialog" persistent>
    <q-card style="min-width: 450px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Фильтр по датам и цеху</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="closeDialog" />
      </q-card-section>

      <q-card-section>
        <!-- Поле выбора цеха -->
        <div class="q-mb-md">
          <q-select
            standout
            v-model="organization_id"
            :options="workshops"
            option-label="normal_name"
            option-value="id"
            label="Выберите цех"
            emit-value
            map-options
            clearable
            filled
            class="q-mb-md"
          />
        </div>

        <!-- Поле "Дата начала" -->
        <div class="q-mb-md">
          <q-input
            v-model="start_day"
            label="Дата начала"
            filled
            class="q-mb-sm"
            clearable
          >
            <template v-slot:append>
              <q-icon name="event" class="cursor-pointer">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-date v-model="start_day" mask="YYYY-MM-DD">
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Закрыть" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>

        <!-- Поле "Дата конца" -->
        <div class="q-mb-md">
          <q-input
            v-model="end_day"
            label="Дата конца"
            filled
            class="q-mb-sm"
            clearable
          >
            <template v-slot:append>
              <q-icon name="event" class="cursor-pointer">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-date v-model="end_day" mask="YYYY-MM-DD">
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Закрыть" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>

        <!-- Чекбокс "Только завершенные" -->
        <div class="q-mb-lg">
          <q-checkbox
            v-model="completed_only"
            label="Только завершенные"
          />
        </div>
      </q-card-section>

      <!-- Кнопки действий -->
      <q-card-actions align="right">
        <q-btn flat label="Сбросить" color="grey" @click="resetFilters" />
        <q-space />
        <q-btn flat label="Отмена" color="primary" @click="closeDialog" />
        <q-btn flat label="Применить" color="primary" @click="applyFilters" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, defineEmits } from 'vue'
import { DivisionFuctionSelect } from '../Functions/SelectDivision.js'

const emit = defineEmits(['filters-applied', 'loading', 'error'])

const showDialog = ref(false)
const start_day = ref('')
const end_day = ref('')
const completed_only = ref(false)
const organization_id = ref(null)

// Используем ту же функцию для получения списка цехов
const { divisions: workshops } = DivisionFuctionSelect()

const open = () => {
  showDialog.value = true
}

const closeDialog = () => {
  showDialog.value = false
}

const applyFilters = async () => {
  try {
    emit('loading', true)

    // Собираем параметры запроса
    const params = {}

    if (organization_id.value) {
      params.organization_id = organization_id.value
    }

    if (start_day.value) {
      params.start_day = start_day.value
    }

    if (end_day.value) {
      params.end_day = end_day.value
    }

    if (completed_only.value) {
      params.completed_only = completed_only.value
    }

    console.log('Отправка запроса с параметрами:', params)

    // Отправляем GET запрос
    const response = await fetch(`/stats/all_service_works_completed?${new URLSearchParams(params)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    })

    if (!response.ok) {
      throw new Error(`Ошибка HTTP: ${response.status}`)
    }

    const data = await response.json()

    console.log('Получены данные:', data)

    // Эмитим событие с полученными данными
    emit('filters-applied', data)

    // Закрываем диалог
    showDialog.value = false

  } catch (error) {
    console.error('Ошибка при отправке запроса:', error)
    emit('error', error.message)
  } finally {
    emit('loading', false)
  }
}

const resetFilters = () => {
  organization_id.value = null
  start_day.value = ''
  end_day.value = ''
  completed_only.value = false
}

defineExpose({ open })
</script>