import { useAuthStore } from 'src/stores/useAuthStore';

export default () => {
  const authStore = useAuthStore();
  authStore.initializeStore();
};