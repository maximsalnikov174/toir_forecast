import { api } from 'boot/axios';

class DeliveryService {
  /**
    Получить данные о доставке по ID сервисной работы
   @param {number} serviceWorkId - ID сервисной работы
   *@returns {Promise<Object>} - Данные о доставке
   */
  async getDeliveryData(serviceWorkId) {
    try {
      const response = await api.get(`/service_work/${serviceWorkId}/unit_of_bom`);

      return response.data[0] || {};
    } catch (error) {
      console.error('Ошибка при загрузке данных о доставке:', error);
      throw new Error('Не удалось загрузить данные о доставке');
    }
  }

  /**
   * Получить название организации по ID
   * @param {number} organizationId - ID организации
   * @returns {string} - Название организации
   */
  getOrganizationName(organizationId) {
    const organizationMap = {
      6: 'ООО "СНБ"',
    };

    return organizationMap[organizationId] || `Организация №${organizationId}`;
  }
}

// Создаем и экспортируем экземпляр сервиса
export const deliveryService = new DeliveryService();