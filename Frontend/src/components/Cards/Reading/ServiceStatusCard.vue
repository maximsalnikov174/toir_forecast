<template>
  <div class="q-pa-md">
    <q-card class="service-status-card">
      <q-card-section class="card-content">
        <div class="characteristic-title">Характеристики</div>
        <div class="other-text">другая</div>
      </q-card-section>
    </q-card>
  </div>
</template>

<style scoped>
.service-status-card {
  width: 118px;
  height: 68px;
  background-color: #FFFFFF;
  position: relative;
}

.characteristic-title {
  position: absolute;
  width: 88px;
  height: 22px;
  top: 23px;
  left: 22px;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 18px;
  line-height: 100%;
  letter-spacing: 0%;
  text-align: right;
}

.other-text {
  position: absolute;
  width: 51px;
  height: 12px;
  top: 9px;
  left: 13px;
  font-family: 'Inter', sans-serif;
  font-weight: 200;
  font-size: 10px;
  line-height: 100%;
  letter-spacing: 0%;
}
</style>