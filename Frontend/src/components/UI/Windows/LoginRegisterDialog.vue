<template>
  <div class="dialog-overlay" v-if="isOpen" @click.self="close">
    <div class="dialog-content">
      <button class="close-button" @click="close">×</button>

      <h2>{{ isLoginMode ? 'Вход' : 'Регистрация' }}</h2>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            type="email"
            v-model="form.email"
            required
          >
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input
            id="password"
            type="password"
            v-model="form.password"
            required
          >
        </div>

        <div v-if="!isLoginMode" class="form-group">
          <label for="name">Имя</label>
          <input
            id="name"
            type="text"
            v-model="form.name"
            required
          >
        </div>

        <div v-if="!isLoginMode" class="form-group">
          <label for="surname">Фамилия</label>
          <input
            id="surname"
            type="text"
            v-model="form.surname"
            required
          >
        </div>

        <div v-if="!isLoginMode" class="form-group">
          <label for="organization">Выберите цех</label>
          <select
            id="organization"
            v-model="form.organization"
            required
          >
            <option value="" disabled selected>Выберите цех</option>
            <option
              v-for="division in divisions"
              :key="division.id"
              :value="division.id"
            >
              {{ division.normal_name }}
            </option>
          </select>
        </div>


        <button type="submit" class="submit-button">
          {{ isLoginMode ? 'Войти' : 'Зарегистрироваться' }}
        </button>
      </form>
      <div class="mode-switch">
        <button @click="toggleMode" class="switch-button">
          {{ isLoginMode ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { DivisionFuctionSelect } from '../../Functions/ButtonSelectDivision.js'
import { registerPerson } from '../../Functions/RegistrationPerson.js'


const emit = defineEmits(['login', 'register', 'close'])

const isOpen = ref(false)
const isLoginMode = ref(true)

const { divisions } = DivisionFuctionSelect();

const form = reactive({
  email: '',
  password: '',
  name: '',
  surname:'',
  organization:'',
  role_id: 2,
  is_verified: false,
})

const open = () => {
  isOpen.value = true
}

const close = () => {
  isOpen.value = false
  emit('close')
}

const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value
}

const handleSubmit = async () => {
  if (isLoginMode.value) {
    emit('login', {
      email: form.email,
      password: form.password
    });
  } else {
    try {
      const response = await registerPerson(form);
      console.log('Успешная регистрация:', response);
      emit('register', response);

      // Очистка формы после успешной регистрации
      form.email = '';
      form.password = '';
      form.name = '';
      form.surname = '';
      form.organization = '';
      close();
    } catch (error) {
      // Показываем сообщение об ошибке пользователю
      alert(error.message); // Или используйте красивый toast/модальное окно
      console.error('Ошибка регистрации:', error);
    }
  }
}

defineExpose({
  open,
  close
})
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog-content {
  background-color: white;
  padding: 25px;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
  position: relative;
}

.close-button {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  text-align: center;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.submit-button {
  width: 100%;
  padding: 10px;
  background-color: #4a76a8;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  margin-top: 10px;
}

.submit-button:hover {
  background-color: #3a5f8a;
}

.mode-switch {
  margin-top: 15px;
  text-align: center;
}

.switch-button {
  background: none;
  border: none;
  color: #4a76a8;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
}

.switch-button:hover {
  color: #3a5f8a;
}

select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
  background-color: white;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 1em;
}

select:focus {
  outline: none;
  border-color: #4a76a8;
}
</style>