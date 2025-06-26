<template>
  <div class="car-card-container">
    <q-card class="car-card">
      <q-card-section horizontal>
        <q-img
          src="your-image-path-here"
          class="car-image"
        />

        <q-card-section class="car-content">
          <div class="characteristic-subtitle">Характеристики</div>
          <div class="car-grz">{{ grz }}</div>
          <div class="row items-center">
            <div class="additional-info">Доп.инфо</div>
            <div class="car-value">123</div>
          </div>
        </q-card-section>
      </q-card-section>
    </q-card>
  </div>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'CarCard',
  props: {
    grz: {
      type: String,
      required: true
    }
  }
})
</script>

<style scoped>
.car-card-container {
  margin-bottom: 10px;
}

.car-card {
  width: 212px;
  height: 80px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.car-image {
  width: 38px;
  height: 38px;
  margin: 21px 0 0 16px;
}

.car-content {
  padding: 8px 0 0 8px;
}

.characteristic-subtitle {
  width: 125px;
  height: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 200;
  font-size: 10px;
  line-height: 100%;
  margin-bottom: 6px;
}

.car-grz {
  width: 150px;
  height: 22px;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 18px;
  line-height: 100%;
  margin-bottom: 12px;
}

.additional-info {
  width: 39px;
  height: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  font-size: 10px;
  line-height: 100%;
  text-align: right;
}

.car-value {
  width: 22px;
  height: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  font-size: 10px;
  line-height: 100%;
  text-align: right;
  margin-left: 5px;
}
</style>