<template>
  <div v-if="show" class="window-overlay" @click.self="close">
    <div class="window-container">
      <div class="window-header">
        <h3>Перевод в статус 'завершено'</h3>
        <button class="close-btn" @click="close"></button>
      </div>

      <div class="window-content">
        <p>Подтверждаю, что работы выполнены, ТС принято с сервиса</p>
      </div>

      <div class="window-footer">
        <button class="complete-btn" @click="complete">Да</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';
import { useAuthStore } from 'src/stores/useAuthStore';
import { api } from '../../boot/axios.js';

const authStore = useAuthStore();

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  serviceWorkId: {
    type: [Number, String],
    required: true
  },
  onSubmitSuccess: {
    type: Function,
    default: () => {}
  },
});

const emit = defineEmits(['update:show', 'close', 'submitted']);

const close = () => {
  emit('update:show', false);
  emit('close');
};

const complete = async () => {
  try {
    await api.patch(
      `/service_work/de_facto_completed?service_work_id=${props.serviceWorkId}`,
      null,
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
          'accept': 'application/json'
        }
      }
    );

    emit('submitted');
    props.onSubmitSuccess()  // Вызываем переданную функцию
    close();
  } catch (error) {
    console.error('Ошибка:', error);
    // Можно добавить уведомление об ошибке
  }
};
</script>

<style scoped>
.window-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.window-container {
  width: 500px;
  height: 200px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.window-header {
  padding: 10px 15px;
  background-color: #f0f0f0;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.window-header h3 {
  margin: 0;
  font-size: 16px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 0 5px;
}

.window-content {
  flex: 1;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.window-content p {
  text-align: center;
  margin: 0;
}

.window-footer {
  padding: 15px;
  border-top: 1px solid #ddd;
  text-align: center;
}

.complete-btn {
  padding: 8px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.complete-btn:hover {
  background-color: #45a049;
}
</style>