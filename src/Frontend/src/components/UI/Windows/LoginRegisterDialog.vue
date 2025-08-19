<template>
  <div class="dialog-overlay" v-if="isOpen" @click.self="close">
    <div class="dialog-content">
      <button class="close-button" @click="close">×</button>

      <!-- Toast-уведомления -->
      <transition-group name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['toast', toast.type]"
          @click="removeToast(toast.id)"
        >
          {{ toast.message }}
        </div>
      </transition-group>

      <h2>{{ isLoginMode ? 'Вход' : 'Регистрация' }}</h2>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            type="email"
            v-model="form.email"
            @blur="convertEmailToLowercase"
            @input="validateEmail"
            :class="{ invalid: emailError }"
            required
          />
          <span v-if="emailError" class="error-message">{{ emailError }}</span>
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input
            id="password"
            type="password"
            v-model="form.password"
            @input="handlePasswordInput"
            :class="{ invalid: !isLoginMode && (passwordError || russianCharWarning) }"
            required
          />
          <span v-if="!isLoginMode && passwordError" class="error-message">{{
            passwordError
          }}</span>
          <span v-if="!isLoginMode && russianCharWarning" class="warning-message">
            Русские символы автоматически удалены из пароля
          </span>

          <div v-if="!isLoginMode && form.password && !passwordError" class="password-hints">
            <p class="hint-valid">✓ Пароль соответствует требованиям</p>
          </div>
          <div v-else-if="!isLoginMode && form.password" class="password-hints">
            <p :class="{ 'hint-invalid': !hasMinLength, 'hint-valid': hasMinLength }">
              {{ hasMinLength ? '✓' : '•' }} Минимум 8 символов
            </p>
            <p :class="{ 'hint-invalid': !hasUpperLower, 'hint-valid': hasUpperLower }">
              {{ hasUpperLower ? '✓' : '•' }} Буквы верхнего и нижнего регистра
            </p>
            <p :class="{ 'hint-invalid': !hasNumber, 'hint-valid': hasNumber }">
              {{ hasNumber ? '✓' : '•' }} Хотя бы одна цифра
            </p>
            <p :class="{ 'hint-invalid': !hasSpecialChar, 'hint-valid': hasSpecialChar }">
              {{ hasSpecialChar ? '✓' : '•' }} Хотя бы один спецсимвол (!@%^*-_+=)
            </p>
            <p :class="{ 'hint-invalid': !hasNoRussian, 'hint-valid': hasNoRussian }">
              {{ hasNoRussian ? '✓' : '•' }} Без русских символов
            </p>
          </div>
        </div>

        <div v-if="!isLoginMode" class="form-group">
          <label for="name">Имя</label>
          <input id="name" type="text" v-model="form.name" required />
        </div>

        <div v-if="!isLoginMode" class="form-group">
          <label for="surname">Фамилия</label>
          <input id="surname" type="text" v-model="form.surname" required />
        </div>

        <div v-if="!isLoginMode" class="form-group">
          <label for="organization">Выберите цех</label>
          <select id="organization" v-model="form.organization" required>
            <option value="" disabled selected>Выберите цех</option>
            <option v-for="division in divisions" :key="division.id" :value="division.id">
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
import { ref, reactive, computed } from 'vue'
import { DivisionFuctionSelect } from '../../Functions/ButtonSelectDivision.js'
import { registerPerson } from '../../Functions/RegistrationPerson.js'
import { LoginPerson } from '../../Functions/LoginPerson.js'

const emit = defineEmits(['login', 'register', 'close'])

const isOpen = ref(false)
const isLoginMode = ref(true)
const toasts = ref([])
let toastId = 0

const { divisions } = DivisionFuctionSelect()

const emailError = ref('')
const passwordError = ref('')
const russianCharWarning = ref(false)

const form = reactive({
  email: '',
  password: '',
  name: '',
  surname: '',
  organization: '',
  role_id: 2,
  is_verified: false,
})

const passwordRequirements = {
  minLength: 8,
  hasUpper: /[A-Z]/,
  hasLower: /[a-z]/,
  hasNumber: /[0-9]/,
  hasSpecial: /[!@%^*\-_+=]/,
  noRussian: /^[^а-яА-Я]*$/,
}

const hasMinLength = computed(() => form.password.length >= passwordRequirements.minLength)
const hasUpper = computed(() => passwordRequirements.hasUpper.test(form.password))
const hasLower = computed(() => passwordRequirements.hasLower.test(form.password))
const hasUpperLower = computed(() => hasUpper.value && hasLower.value)
const hasNumber = computed(() => passwordRequirements.hasNumber.test(form.password))
const hasSpecialChar = computed(() => passwordRequirements.hasSpecial.test(form.password))
const hasNoRussian = computed(() => passwordRequirements.noRussian.test(form.password))

const convertEmailToLowercase = () => {
  form.email = form.email.toLowerCase()
  validateEmail()
}

const showToast = (message, type = 'success') => {
  const id = toastId++
  toasts.value.push({ id, message, type })

  setTimeout(() => {
    removeToast(id)
  }, 5000)
}

const removeToast = (id) => {
  toasts.value = toasts.value.filter((toast) => toast.id !== id)
}

const open = () => {
  isOpen.value = true
}

const close = () => {
  isOpen.value = false
  emit('close')
}

const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value
  emailError.value = ''
  passwordError.value = ''
}

const validateEmail = () => {
  const emailRegex = /^[a-zA-Z0-9]+\.[a-zA-Z]{2}@(?:atu\.)?mmk\.ru$/i
  if (!form.email) {
    emailError.value = ''
    return false
  }
  if (!emailRegex.test(form.email)) {
    emailError.value = 'Разрешены только рабочие Email (ivanov.av@atu.mmk.ru или ivanov.av@mmk.ru)'
    return false
  }
  emailError.value = ''
  return true
}

const handlePasswordInput = (e) => {
  const originalValue = e.target.value
  form.password = originalValue.replace(/[а-яА-Я]/g, '')

  russianCharWarning.value = originalValue !== form.password

  if (russianCharWarning.value) {
    setTimeout(() => {
      russianCharWarning.value = false
    }, 6000)
  }

  if (!isLoginMode.value) {
    validatePassword()
  }
}

const validatePassword = () => {
  if (isLoginMode.value) return true

  if (!form.password) {
    passwordError.value = ''
    return false
  }

  const errors = []

  if (!hasNoRussian.value) {
    errors.push('русские символы запрещены')
  }
  if (!hasMinLength.value) {
    errors.push('минимум 8 символов')
  }
  if (!hasUpperLower.value) {
    errors.push('буквы верхнего и нижнего регистра')
  }
  if (!hasNumber.value) {
    errors.push('хотя бы одна цифра')
  }
  if (!hasSpecialChar.value) {
    errors.push('хотя бы один спецсимвол (!@%^*-_+=)')
  }

  if (errors.length > 0) {
    passwordError.value = `Пароль должен содержать: ${errors.join(', ')}`
    return false
  }

  passwordError.value = ''
  return true
}

const resetForm = () => {
  form.email = ''
  form.password = ''
  form.name = ''
  form.surname = ''
  form.organization = ''
}

const handleSubmit = async () => {
  if (!validateEmail()) {
    showToast('Пожалуйста, введите корректный email', 'error')
    return
  }

  if (!isLoginMode.value && !validatePassword()) {
    showToast('Пароль не соответствует требованиям', 'error')
    return
  }

  if (isLoginMode.value) {
    try {
      const response = await LoginPerson({
        email: form.email,
        password: form.password,
      })

      showToast('Успешный вход! Перенаправляем...', 'success')

      setTimeout(() => {
        emit('login', response)
        close()
      }, 2000)
    } catch (error) {
      showToast(error.message || 'Ошибка входа. Проверьте данные', 'error')
    }
  } else {
    try {
      await registerPerson(form)

      showToast('Регистрация прошла успешно! Теперь вы можете войти', 'success')

      setTimeout(() => {
        isLoginMode.value = true
        resetForm()
      }, 3000)
    } catch (error) {
      showToast(error.message || 'Ошибка регистрации. Пожалуйста, попробуйте снова', 'error')
    }
  }
}

defineExpose({
  open,
  close,
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

input,
select {
  width: 100%;
  padding: 8px;
  border: 1px solid #000000;
  border-radius: 4px;
  box-sizing: border-box;
}

.invalid {
  border-color: #ff4444 !important;
}

.error-message {
  color: #ff4444;
  font-size: 0.8em;
  margin-top: 5px;
  display: block;
}

.warning-message {
  color: #ff9800;
  font-size: 0.8em;
  margin-top: 5px;
  display: block;
  font-style: italic;
}

.password-hints {
  margin-top: 5px;
  font-size: 0.8em;
}

.hint-valid {
  color: #4caf50;
  margin: 2px 0;
}

.hint-invalid {
  color: #757575;
  margin: 2px 0;
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

/* Стили для toast-уведомлений */
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 4px;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  z-index: 1001;
  transition: all 0.3s ease;
  max-width: 300px;
}

.toast.success {
  background-color: #4caf50;
}

.toast.error {
  background-color: #f44336;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
