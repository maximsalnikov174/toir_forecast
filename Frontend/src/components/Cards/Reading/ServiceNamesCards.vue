<template>
  <div class="ServiceNamesCard">
    <div class="card-text">Текст</div>
  </div>
</template>

<style scoped>
.ServiceNamesCard {
  width: 118px;
  height: 41px;
  background-color: #555555;
  position: relative; /* Для позиционирования текста внутри */
}

.card-text {
  width: 29px;
  height: 15px;
  position: absolute;
  top: 13px;
  left: 45px;

  font-family: Inter, sans-serif;
  font-weight: 400;
  font-size: 12px;
  line-height: 100%;
  letter-spacing: 0%;
  text-align: center;
  vertical-align: middle;

  color: white; /* Белый текст на темном фоне */
}
</style>