<template>
  <q-dialog v-model="showDialog" >
    <q-card style="min-width: 400px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Цвета сервисных центров</div>
        <q-space />
      </q-card-section>

      <q-card-section>
        <div class="color-info">
          <div class="color-box turquoise"></div>
          <span>Сторона </span>
        </div>
        <div class="color-info">
          <div class="color-box purple"></div>
          <span>Урла </span>
        </div>
        <div class="color-info">
          <div class="color-box orange"></div>
          <span>Урга </span>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref } from 'vue'

const showDialog = ref(false)

const open = () => {
  showDialog.value = true
}

defineExpose({ open })
</script>

<style scoped>
.color-info {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.color-box {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  margin-right: 12px;
  border: 1px solid #ddd;
}

.turquoise {
  background-color: turquoise;
}

.purple {
  background-color: purple;
}

.orange {
  background-color: orange;
}
</style>