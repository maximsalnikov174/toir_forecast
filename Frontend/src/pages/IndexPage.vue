<template>
  <q-select
    standout
    v-model="selectedOrgId"
    :options="organizations"
    option-label="name"
    option-value="id"
    label="Выберите организацию"
    emit-value
    map-options
    clearable
    style="max-width: 300px;"
    class="q-mb-md"
  />
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  setup() {
    const selectedOrgId = ref(null)
    const organizations = ref([])

    const fetchOrganizations = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8001/organization/all', {
          method: 'GET',
          headers: {
            'accept': 'application/json'
          }
        })

        if (!response.ok) {
          throw new Error('Ошибка при загрузке организаций')
        }

        organizations.value = await response.json()
      } catch (error) {
        console.error('Ошибка:', error)
      }
    }

    onMounted(() => {
      fetchOrganizations()
    })

    return {
      selectedOrgId,
      organizations
    }
  }
}
</script>