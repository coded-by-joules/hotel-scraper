<template>
  <router-link
    :class="['listItem', changeClass]"
    :to="showLocation"
    class="block"
    >{{ location }}</router-link
  >
</template>

<script>
export default {
  props: ["location", "active"],
  computed: {
    changeClass() {
      return { active: this.active, regular: !this.active };
    },
    showLocation() {
      return {
        name: "location",
        query: { key: this.location },
      };
    },
  },
  methods: {},
};
</script>

<style scoped>
.listItem {
  @apply block truncate pl-2 py-2 pr-3 mb-3 rounded-tl rounded-br border-r-0 shadow text-sm cursor-pointer;
}

.active {
  @apply bg-green-500 font-bold text-white;
}

.regular {
  @apply bg-green-300 font-bold;
}
</style>
