// composables/useDeliveryActions.js
import { ref } from 'vue'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'

export function useDeliveryActions() {
  const $q = useQuasar()
  const isMarkingAsEntered = ref(false)
  const enteredDeliveries = ref(new Set())

  // Функция для показа уведомлений
  const showNotify = (options) => {
    $q.notify(options)
  }

  // Отметка доставки как внесенной
  const markAsEntered = async (delivery) => {
    if (delivery.to_insert === true) return

    if (delivery.id) {
      isMarkingAsEntered.value = true
      try {
        // Отправляем POST запрос к API
        const response = await api.post(`/service_work/unit_of_bom/${delivery.id}`, {}, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
          }
        })

        if (response.status === 201) {
          enteredDeliveries.value.add(delivery.delivery)
          showNotify({
            type: 'positive',
            message: `Доставка №${delivery.delivery} отмечена как внесенная`,
            timeout: 3000,
          })
          return true // Успех
        } else {
          throw new Error('Ошибка при отправке данных')
        }
      } catch (error) {
        console.error('Ошибка при отметке доставки как внесенной:', error)
        showNotify({
          type: 'negative',
          message: 'Не удалось отметить доставку как внесенную',
          timeout: 3000,
        })
        return false // Ошибка
      } finally {
        isMarkingAsEntered.value = false
      }
    }
    return false
  }

  // Проверка, была ли доставка уже отмечена
  const isDeliveryEntered = (deliveryNumber) => {
    return enteredDeliveries.value.has(deliveryNumber)
  }

  // Сброс состояния отмеченных доставок
  const resetEnteredDeliveries = () => {
    enteredDeliveries.value.clear()
  }

  return {
    isMarkingAsEntered,
    markAsEntered,
    isDeliveryEntered,
    resetEnteredDeliveries,
    enteredDeliveries
  }
}