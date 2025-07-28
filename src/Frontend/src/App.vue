<template>
  <router-view />
</template>

<script>
import { useAuthStore } from 'src/stores/useAuthStore';

export default {
  setup() {
    const authStore = useAuthStore();
    authStore.initializeStore();
    // ...
  }
}
</script>
