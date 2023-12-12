<template>
  <the-header></the-header>
  <main class="container mx-auto p-5 max-w-screen-lg">
    <search-box
      :search-text="searchText"
      @onSearchHotel="fetchHotels"
    ></search-box>
    <div class="mt-3 flex" v-if="searchLocations.length > 0">
      <keys-list :search-keys="searchLocations"></keys-list>
      <div class="border-l-2 border-black w-4/5 p-3">
        <router-view></router-view>
      </div>
    </div>
    <div class="mt-3 text-center" v-else>
      <p>Please start searching locations.</p>
    </div>
  </main>
</template>

<script>
import TheHeader from "./components/TheHeader.vue";
import SearchBox from "./components/SearchBox/SearchBox.vue";
import KeysList from "./components/SearchKeys/KeysList.vue";
import axios from "axios";

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
      searchLocations: [],
    };
  },
  created() {
    this.fetchHotels();
  },
  methods: {
    fetchHotels() {
      axios.get("http://localhost:7000/api/get-locations").then((response) => {
        if (response.status === 200) {
          this.searchLocations = response.data["locations"];
        }
      });
    },
  },
};
</script>
