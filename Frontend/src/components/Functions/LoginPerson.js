import { api } from "../../boot/axios.js";
import { useAuthStore } from "src/stores/useAuthStore.js"; // Укажите правильный путь

export const LoginPerson = async (formData) => {
  const authStore = useAuthStore();

  try {
    const response = await api.post('/auth/jwt/login', {
      username: formData.email,
      password: formData.password,
    }, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      }
    });

    if (!response.data) {
      throw new Error('Не удалось получить ответ от сервера');
    }

    const data = response.data;

    if (response.status < 200 || response.status >= 300) {
      throw {
        status: response.status,
        message: data.detail || 'Ошибка при регистрации',
        errors: data.errors || null
      };
    }

    // Сохраняем данные аутентификации в хранилище
    authStore.setAuthData({
      access_token: data.access_token,
      user: { email: formData.email } // или другие данные пользователя из ответа
    });

    console.log('Token:', authStore.token);
console.log('User:', authStore.user);
console.log('Is authenticated:', authStore.isAuthenticated);

    return data;
  } catch (error) {
    console.error('Ошибка при регистрации:', error);
    authStore.clearAuthData(); // Очищаем хранилище при ошибке

    let errorMessage = 'Произошла ошибка при регистрации';

    if (error.response?.data?.detail?.reason) {
      errorMessage = error.response.data.detail.reason;
    }
    else if (error.response?.data?.errors) {
      errorMessage = Object.entries(error.response.data.errors)
        .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
        .join('; ');
    } else if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    } else if (error.message) {
      errorMessage = error.message;
    }

    throw new Error(errorMessage);
  }
};
