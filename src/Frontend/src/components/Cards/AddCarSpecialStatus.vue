<template>
  <q-card style="min-width: 300px">
    <q-card-section>
      <div class="text-h6">Выберите статус</div>

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

        <template v-slot:selected-item="scope">
          <q-chip
            removable
            @remove="scope.removeAtIndex(scope.index)"
            :tabindex="scope.tabindex"
          >
            <q-avatar>
              <q-img
                :src="getStatusImage(scope.opt.id)"
                width="24px"
                height="24px"
              />
            </q-avatar>
            {{ scope.opt.name }}
          </q-chip>
        </template>
      </q-select>
    </q-card-section>

    <q-card-actions align="right">
      <q-btn flat label="Закрыть" color="primary" v-close-popup />
    </q-card-actions>
  </q-card>
</template>

<script>
import { defineComponent, computed } from 'vue'
import { useStatusOptions } from '../Functions/ButtonSelectGroupTs.js'

// Импортируем изображения статусов
import status1 from 'src/assets/1.png'
import status2 from 'src/assets/2.png'
import status3 from 'src/assets/3.png'
import status4 from 'src/assets/4.png'
import status5 from 'src/assets/5.png'

export default defineComponent({
  name: 'AddCarSpecialStatus',
  emits: ['close'],
  setup() {
    const {
      statusOptions,
      selectedSpecialStatuses,
      loading
    } = useStatusOptions()

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

    return {
      statusOptionsWithImages, // Возвращаем computed свойство
      selectedSpecialStatuses,
      loading,
      getStatusImage
    }
  }
})
</script>

<style scoped>
/* Стили для выравнивания иконок в выпадающем списке */
.q-item__section--avatar {
  min-width: 30px;
}
</style>