<template>
  <div class="q-pa-md" style="max-width: 300px">
    <div class="q-gutter-md">

      <q-select standout v-model="model" :options="options" label="Standout" />

    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  setup () {
    return {
      model: ref(null),
      options: [
        'Google', 'Facebook', 'Twitter', 'Apple', 'Oracle'
      ]
    }
  }
}
</script>
