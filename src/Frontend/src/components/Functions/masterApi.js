import { api } from "../../boot/axios.js";

/**
 * API функции для мастера (пользователя с station_id не null)
 */
export const masterApi = {
  /**
   * Получить данные таблицы для мастера
   * @param {string} token - JWT токен
   * @returns {Promise<Array>} - Данные таблицы
   */
  async getTableData(token) {
    const response = await api.post(
      '/service_work/get_table_for_master',
      [],
      {
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      }
    );
    return response.data.filter(item => item !== null);
  },

  /**
   * Получить сервисы для мастера
   * @param {string} token - JWT токен
   * @returns {Promise<Array>} - Список сервисов
   */
  async getServices(token) {
    const response = await api.post(
      '/service_name/all_service_names_for_master',
      [],
      {
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      }
    );
    return response.data;
  },

  /**
   * Получить автомобили для мастера
   * @param {string} token - JWT токен
   * @returns {Promise<Array>} - Список автомобилей
   */
  async getCars(token) {
    const response = await api.post(
      '/car/with_many_statuses_for_master',
      [],
      {
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      }
    );
    return response.data;
  },

  /**
   * Загрузить все данные для мастера
   * @param {string} token - JWT токен
   * @returns {Promise<Object>} - Объект с tableData, services, cars
   */
  async loadAllMasterData(token) {
    try {
      const [tableData, services, cars] = await Promise.all([
        this.getTableData(token),
        this.getServices(token),
        this.getCars(token)
      ]);

      return {
        tableData,
        services,
        cars
      };
    } catch (error) {
      console.error('Ошибка при загрузке данных мастера:', error);
      throw error;
    }
  }
};

export default masterApi;