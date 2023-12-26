<template>
  <the-header></the-header>
  <main class="container mx-auto p-5 max-w-screen-lg">
    <search-box @onStartSearch="addSearch"></search-box>
    <div class="mt-3" v-if="searchLocations.length > 0">
      <location-list :locations="searchLocations"></location-list>
    </div>
  </main>
</template>

<script>
import TheHeader from "./components/TheHeader.vue";
import SearchBox from "./components/SearchBox.vue";
import LocationList from "./components/LocationItems/LocationList.vue";

export default {
  components: {
    "the-header": TheHeader,
    "search-box": SearchBox,
    "location-list": LocationList,
  },
  emits: ["onStartSearch"],
  data() {
    return {
      searchLocations: [],
    };
  },
  methods: {
    addSearch(item) {
      this.searchLocations.push({ status: "loaded", location: item });
    },
  },
};
</script>
