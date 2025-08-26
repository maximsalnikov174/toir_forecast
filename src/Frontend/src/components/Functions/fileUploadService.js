// src/services/fileUploadService.js
import { api } from 'boot/axios';
import { useAuthStore } from 'src/stores/useAuthStore';

export const useFileUploadService = () => {
  const authStore = useAuthStore();

  const uploadFile = async (file, serviceWorkId) => {
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      throw new Error('Файл слишком большой (максимум 10MB)');
    }

    try {
      const formData = new FormData();
      formData.append('bom_file', file);

      const response = await api.post(
        `/api/service_works/${serviceWorkId}/bom`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${authStore.token}`
          }
        }
      );

      return {
        success: true,
        data: response.data,
        message: 'Файл успешно загружен'
      };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Ошибка при загрузке файла';

      return {
        success: false,
        error: errorMessage,
        originalError: error
      };
    }
  };

  return {
    uploadFile
  };
};