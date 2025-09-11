<template>
  <div class="search-by-letter">
    <div class="search-title">Поиск по букве:</div>
    <div class="letter-buttons">
      <button
        v-for="letter in availableLetters"
        :key="letter"
        @click="toggleLetterFilter(letter)"
        :class="['letter-btn', { active: activeLetters.includes(letter) }]"
      >
        {{ letter }}
      </button>
      <button
        v-if="activeLetters.length > 0"
        @click="clearFilters"
        class="clear-filter-btn"
        title="Очистить фильтры"
      >
        ×
      </button>
    </div>
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
  }
})

const emit = defineEmits(['update:activeLetters', 'filter-change'])

// Получаем доступные буквы из GRZ автомобилей
const availableLetters = computed(() => {
  const letters = new Set()
  props.cars.forEach(car => {
    const firstLetter = car.grz?.replace(/\s+/g, '').charAt(0)?.toUpperCase() || ''
    if (firstLetter && /[А-ЯA-Z]/.test(firstLetter)) {
      letters.add(firstLetter)
    }
  })
  return Array.from(letters).sort()
})

// Функции для управления фильтрами
const toggleLetterFilter = (letter) => {
  const newActiveLetters = [...props.activeLetters]
  const index = newActiveLetters.indexOf(letter)

  if (index === -1) {
    newActiveLetters.push(letter)
  } else {
    newActiveLetters.splice(index, 1)
  }

  emit('update:activeLetters', newActiveLetters)
  emit('filter-change', newActiveLetters)
}

const clearFilters = () => {
  emit('update:activeLetters', [])
  emit('filter-change', [])
}
</script>

<style scoped>
.search-by-letter {
  border-radius: 4px;
  margin-bottom: 10px;
}

.search-title {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 1px;
  color: #ffffff;
}

.letter-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 1px;
}

.letter-btn {
  width: 15px;
  height: 15px;
  border: 1px solid #ccc;
  background: white;
  border-radius: 3px;
  cursor: pointer;
  font-size: 10px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.letter-btn:hover {
  background-color: #e3f2fd;
  border-color: #2196f3;
}

.letter-btn.active {
  background-color: #2196f3;
  color: white;
  border-color: #2196f3;
}

.clear-filter-btn {
  width: 15px;
  height: 15px;
  border: 1px solid #ff6b6b;
  background: white;
  color: #ff6b6b;
  border-radius: 3px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-filter-btn:hover {
  background-color: #ff6b6b;
  color: white;
}

/* Адаптивность для маленьких экранов */
@media (max-width: 768px) {
  .letter-btn {
    width: 20px;
    height: 20px;
    font-size: 10px;
  }

  .clear-filter-btn {
    width: 20px;
    height: 20px;
    font-size: 12px;
  }
}
</style>