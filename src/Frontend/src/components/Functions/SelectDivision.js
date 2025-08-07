import { ref, onMounted, watch } from 'vue';
import { useFilterStore } from '../Functions/FilterStoreAcceptButton';
import { api } from "../../boot/axios.js";

export function DivisionFuctionSelect() {
  const { selectedDivId } = useFilterStore();
  const divisions = ref([]);

  watch(selectedDivId, (newValue) => {
    console.log('Selected Division ID:', newValue);
  });

  const fetchDivision = async () => {
    try {
      const response = await api.get('/organization/with_vehicles');
      divisions.value = response.data; // Axios автоматически парсит JSON
    } catch (error) {
      console.error('Ошибка при загрузке организаций:', error);
      // Можно добавить обработку ошибки, например:
      divisions.value = []; // Очищаем список в случае ошибки
    }
  };

  onMounted(() => {
    fetchDivision();
  });

  return {
    selectedDivId,
    divisions,
  };
}