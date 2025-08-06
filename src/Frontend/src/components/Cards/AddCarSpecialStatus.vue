<template>
  <q-card style="min-width: 300px">
    <q-card-section>
      <div class="text-h6">Тест</div>
    </q-card-section>

    <q-card-actions align="right">
      <q-btn flat label="Закрыть" color="primary" v-close-popup />
    </q-card-actions>
  </q-card>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'AddCarSpecialStatus',
  emits: ['close'],
  setup() {
    return {}
  }
})
</script>