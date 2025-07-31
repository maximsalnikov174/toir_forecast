import { api } from "../../boot/axios.js";

export const registerPerson = async (formData) => {
  try {
    const response = await api.post('/auth/register', {
      email: formData.email,
      password: formData.password,
      is_active: true,
      is_superuser: false,
      is_verified: formData.is_verified || false,
      name: formData.name,
      surname: formData.surname,
      organization_id: parseInt(formData.organization) || 0,
      role_id: parseInt(formData.role_id) || 2
    }, {
      headers: {
        'accept': 'application/json',
        'Content-Type': 'application/json',
      }
    });

    if (!response.data) {
      throw new Error('Не удалось получить ответ от сервера');
    }

    // В axios response.data уже содержит распарсенный JSON
    const data = response.data;

    // В axios статус проверяется через response.status
    if (response.status < 200 || response.status >= 300) {
      throw {
        status: response.status,
        message: data.detail || 'Ошибка при регистрации',
        errors: data.errors || null
      };
    }

    return data;
  } catch (error) {
    console.error('Ошибка при регистрации:', error);

    let errorMessage = 'Произошла ошибка при регистрации';
    if (error.response?.data?.errors) {
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