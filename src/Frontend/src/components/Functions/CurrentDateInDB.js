import { api } from "../../boot/axios.js";

export const getCurrentDateInDB = async () => {
  try {
    const response = await api.get('/service_work/current_date_in_db')
    return response.data
  } catch (error) {
    console.error('Ошибка при получении текущей даты из БД:', error)
    return { current_db_status: 'Не удалось загрузить дату' }
  }
}