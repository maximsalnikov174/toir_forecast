import { api } from 'boot/axios';
import { useAuthStore } from 'src/stores/useAuthStore';

export const useFileUploadService = () => {
  const authStore = useAuthStore();

  const uploadFiles = async (files, serviceWorkId) => {
    const maxSize = 10 * 1024 * 1024; // 10MB

    // Проверяем размер каждого файла
    for (const file of files) {
      if (file.size > maxSize) {
        throw new Error(`Файл "${file.name}" слишком большой (максимум 10MB)`);
      }
    }

    try {
      const formData = new FormData();

      // Добавляем все файлы в FormData с именем поля 'files'
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await api.post(
        `/service_work/unit_of_bom?service_work_id=${serviceWorkId}`,
        formData,
        {
          headers: {
            'accept': 'application/json',
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${authStore.token}`
          }
        }
      );

      return {
        success: true,
        data: response.data,
        message: files.length === 1
          ? 'Файл успешно загружен'
          : `${files.length} файлов успешно загружено`
      };

    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Ошибка при загрузке файлов';

      return {
        success: false,
        error: errorMessage,
        originalError: error
      };
    }
  };

  // Метод для обратной совместимости с одним файлом
  const uploadFile = async (file, serviceWorkId) => {
    return uploadFiles([file], serviceWorkId);
  };

  return {
    uploadFile,
    uploadFiles
  };
};