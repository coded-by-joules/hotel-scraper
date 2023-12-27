<template>
  <div class="pt-3">
    <location-item
      v-for="location in locations"
      :location="location"
    ></location-item>
  </div>
</template>

<script>
import LocationItem from "./LocationItem.vue";

export default {
  components: {
    "location-item": LocationItem,
  },
  props: ["locations"],
  methods: {
    setupClass(location) {
      return ["item", location.status];
    },
  },
};
</script>
