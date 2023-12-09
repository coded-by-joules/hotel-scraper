<template>
  <the-header></the-header>
  <main class="container mx-auto p-5 max-w-screen-lg">
    <search-box
      :search-text="searchText"
      @onSearchHotel="fetchHotels"
    ></search-box>
    <div class="mt-3 flex">
      <keys-list></keys-list>
      <div class="border-l-2 border-black w-4/5 p-3">Right Side</div>
    </div>
  </main>
</template>

<script>
import TheHeader from "./components/TheHeader.vue";
import SearchBox from "./components/SearchBox/SearchBox.vue";
import KeysList from "./components/SearchKeys/KeysList.vue";

export default {
  components: {
    "the-header": TheHeader,
    "search-box": SearchBox,
    "keys-list": KeysList,
  },
  emits: ["onSearchHotel"],
  data() {
    return {
      searchText: "",
    };
  },
  methods: {
    fetchHotels() {},
  },
};
</script>
