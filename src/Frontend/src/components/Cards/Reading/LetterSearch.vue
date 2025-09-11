<template>
  <div class="search-container">
    <!-- Поиск по буквам -->
    <div class="search-group">
      <div class="buttons-row">
        <button
          v-for="letter in availableLetters"
          :key="'letter-' + letter"
          @click="toggleFilter('letter', letter)"
          :class="['filter-btn', { active: activeLetters.includes(letter) }]"
        >
          {{ letter }}
        </button>

      </div>
    </div>

    <!-- Поиск по цифрам -->
    <div class="search-group">
      <div class="buttons-row">
        <button
          v-for="digit in availableDigits"
          :key="'digit-' + digit"
          @click="toggleFilter('digit', digit)"
          :class="['filter-btn', { active: activeDigits.includes(digit) }]"
        >
          {{ digit }}
        </button>

      </div>
    </div>
<!-- Кнопка очистки -->
<button
      v-if="activeLetters.length > 0 || activeDigits.length > 0"
      @click="clearFilters"
      class="clear-filter-btn"
    >X
    </button>

  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue'

const props = defineProps({
  cars: {
    type: Array,
    required: true,
    default: () => []
  },
  activeLetters: {
    type: Array,
    required: true,
    default: () => []
  },
  activeDigits: {
    type: Array,
    required: true,
    default: () => []
  }
})

const emit = defineEmits(['update:activeLetters', 'update:activeDigits', 'filter-change'])

// Получаем доступные буквы из GRZ автомобилей
const availableLetters = computed(() => {
  const letters = new Set()
  props.cars.forEach(car => {
    const firstChar = car.grz?.replace(/\s+/g, '').charAt(0) || ''
    if (firstChar && /[А-ЯA-Z]/.test(firstChar)) {
      letters.add(firstChar.toUpperCase())
    }
  })
  return Array.from(letters).sort()
})

// Получаем доступные цифры из GRZ автомобилей
const availableDigits = computed(() => {
  const digits = new Set()
  props.cars.forEach(car => {
    const grzWithoutSpaces = car.grz?.replace(/\s+/g, '') || ''
    const firstDigit = grzWithoutSpaces.match(/\d/)?.[0]
    if (firstDigit) {
      digits.add(firstDigit)
    }
  })
  return Array.from(digits).sort()
})

// Функция для управления фильтрами
const toggleFilter = (type, value) => {
  if (type === 'letter') {
    const newActiveLetters = [...props.activeLetters]
    const index = newActiveLetters.indexOf(value)

    if (index === -1) {
      newActiveLetters.push(value)
    } else {
      newActiveLetters.splice(index, 1)
    }

    emit('update:activeLetters', newActiveLetters)
  } else if (type === 'digit') {
    const newActiveDigits = [...props.activeDigits]
    const index = newActiveDigits.indexOf(value)

    if (index === -1) {
      newActiveDigits.push(value)
    } else {
      newActiveDigits.splice(index, 1)
    }

    emit('update:activeDigits', newActiveDigits)
  }

  emit('filter-change', {
    letters: props.activeLetters,
    digits: props.activeDigits
  })
}

const clearFilters = () => {
  emit('update:activeLetters', [])
  emit('update:activeDigits', [])
  emit('filter-change', { letters: [], digits: [] })
}
</script>

<style scoped>

.search-container {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.search-group {
  display: flex;
  flex-direction: column;

}

.buttons-row {
  display: flex;
  gap: 2px;
}

.filter-btn {
  min-width: 16px;
  height: 16px;
  border: 1px solid #ccc;
  background: white;
  border-radius: 2px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  
}

.filter-btn:hover {
  background-color: #e3f2fd;
  border-color: #2196f3;
}

.filter-btn.active {
  background-color: #2196f3;
  color: white;
  border-color: #2196f3;
}

.clear-filter-btn {
  border: 1px solid #ff6b6b;
  background: white;
  color: #ff6b6b;
  border-radius: 3px;
  cursor: pointer;
  font-size: 8px;
  align-self: flex-start;
}

.clear-filter-btn:hover {
  background-color: #ff6b6b;
  color: white;
}

/* Адаптивность для маленьких экранов */
@media (max-width: 768px) {
  .filter-btn {
    min-width: 16px;
    height: 16px;
    font-size: 9px;
  }

}
</style>