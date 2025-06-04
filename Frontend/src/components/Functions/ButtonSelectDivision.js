import { ref, onMounted, watch } from 'vue';  // Добавляем watch
import { useFilterStore } from '../Functions/FilterStoreAcceptButton';

export function DivisionFuctionSelect() {
  const { selectedDivId } = useFilterStore();
  const divisions = ref([]);

  // Вотчер для отслеживания изменений selectedDivId
  watch(selectedDivId, (newValue) => {
    console.log('Selected Division ID:', newValue);
  });

  const fetchDivision = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8001/organization/all', {
        headers: {
          'accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Ошибка при загрузке организаций');
      }

      divisions.value = await response.json();
    } catch (error) {
      console.error('Ошибка:', error);
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