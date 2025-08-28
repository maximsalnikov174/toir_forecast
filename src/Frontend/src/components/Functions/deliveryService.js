import { api } from 'boot/axios';

class DeliveryService {
  /**
    Получить данные о доставке по ID сервисной работы
   @param {number} serviceWorkId - ID сервисной работы
   *@returns {Promise<Array>} - Массив данных о доставках
   */
  async getDeliveryData(serviceWorkId) {
    try {
      const response = await api.get(`/service_work/${serviceWorkId}/unit_of_bom`);

      // Если ответ - массив, возвращаем его, иначе оборачиваем в массив
      return Array.isArray(response.data) ? response.data : [response.data || {}];
    } catch (error) {
      console.error('Ошибка при загрузке данных о доставке:', error);
      throw new Error('Не удалось загрузить данные о доставке');
    }
  }
}

// Создаем и экспортируем экземпляр сервиса
export const deliveryService = new DeliveryService();