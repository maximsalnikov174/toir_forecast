import { api } from "../../boot/axios.js";
import { useAuthStore } from "src/stores/useAuthStore.js";

export const LoginPerson = async (formData) => {
  const authStore = useAuthStore();

  try {
    // Шаг 1: Получаем токен
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

    // Сохраняем токен в хранилище
    authStore.setAuthData({
      access_token: data.access_token,
      user: {
        email: formData.email,
        // временно сохраняем только email, остальные данные получим ниже
      }
    });

    // Шаг 2: Получаем данные пользователя с использованием токена
    const userResponse = await api.get('/users/me', {
      headers: {
        'Authorization': `Bearer ${data.access_token}`,
        'accept': 'application/json'
      }
    });

    if (userResponse.data) {
      // Обновляем данные пользователя в хранилище
      authStore.setAuthData({
        access_token: data.access_token,
        user: {
          ...userResponse.data, // все данные пользователя из /users/me
          email: formData.email // сохраняем email из формы, если его нет в ответе
        }
      });
    }

    console.log('Token:', authStore.token);
    console.log('User:', authStore.user);
    console.log('Is authenticated:', authStore.isAuthenticated);

    return {
      token: data.access_token,
      user: authStore.user
    };
  } catch (error) {
    console.error('Ошибка при регистрации:', error);
    authStore.clearAuthData();

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