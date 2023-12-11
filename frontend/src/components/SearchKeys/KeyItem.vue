<template>
  <div :class="['listItem', changeClass]">
    {{ location }}
  </div>
</template>

<script>
export default {
  props: ["location", "active"],
  computed: {
    changeClass() {
      return { active: this.active, regular: !this.active };
    },
  },
};
</script>

<style scoped>
.listItem {
  @apply truncate pl-2 py-2 pr-3 mb-3 rounded-tl rounded-br border-r-0 shadow text-sm cursor-pointer;
}

.active {
  @apply bg-green-500 font-bold text-white;
}

.regular {
  @apply bg-green-300 font-bold;
}
</style>
