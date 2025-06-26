<template>
  <q-card class="custom-card" style="width: 212px; height: 66px;">
    <q-card-section horizontal>
      <!-- Место для картинки -->
      <q-img
        src="your-image-path-here"
        style="width: 38px; height: 38px;"
      />

      <q-card-section>
        <!-- Текст с характеристиками -->
        <div style="width: 125px; height: 12px; font-family: Inter; font-weight: 200; font-size: 10px; line-height: 100%; letter-spacing: 0%; vertical-align: middle;">
          Характеристики товара
        </div>

        <!-- Основной текст -->
        <div style="width: 150px; height: 22px; font-family: Inter; font-weight: 700; font-size: 18px; line-height: 100%; letter-spacing: 0%; vertical-align: middle;">
          {{ grz }}
        </div>

        <div class="row items-center">
          <!-- Дополнительный текст -->
          <div style="width: 39px; height: 12px; font-family: Inter; font-weight: 400; font-size: 10px; line-height: 100%; letter-spacing: 0%; text-align: right; vertical-align: middle;">
            Доп.инфо
          </div>

          <!-- Еще один текст -->
          <div style="width: 22px; height: 12px; font-family: Inter; font-weight: 400; font-size: 10px; line-height: 100%; letter-spacing: 0%; text-align: right; vertical-align: middle; margin-left: 5px;">
            123
          </div>
        </div>
      </q-card-section>
    </q-card-section>
  </q-card>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ProductCard',
  props: {
    grz: {
      type: String,
      required: true
    }
  }
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;400;700&display=swap');

.custom-card {
  font-family: 'Inter', sans-serif;
  margin-bottom: 10px;
}
</style>