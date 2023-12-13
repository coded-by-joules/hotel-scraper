<template>
  <div v-if="hotelFound">
    <h1 class="text-2xl font-bold">Hotels for "{{ hotelName }}"</h1>
    <p v-if="savedInDB">This is saved in DB</p>
  </div>
  <div v-else>
    <h1 class="text-2xl font-bold">
      "{{ hotelName }}" is not found. Please search for this first.
    </h1>
  </div>
</template>

<script>
import axios from "axios";

export default {
  inject: ["locations"],
  data() {
    return {
      hotelName: this.$route.query.key,
      savedInDB: false,
      hotelFound: false,
    };
  },
  computed: {
    getLocations() {
      return this.locations();
    },
  },
  methods: {
    loadHotels(search_key) {
      axios
        .get("http://localhost:7000/api/get-hotels?key=" + search_key)
        .then((response) => {
          console.log(response.data);
        });
    },
    updatePage(newHotel) {
      this.hotelName = newHotel;
      this.savedInDB = false;
      this.hotelFound = false;

      const locationIndex = this.getLocations.findIndex((item) => {
        return item["search_key"] === newHotel;
      });

      if (locationIndex >= 0) {
        const locationItem = this.getLocations[locationIndex];

        this.hotelFound = true;
        if (locationItem["savedInDB"]) this.savedInDB = true;
      } else {
        this.hotelFound = false;
      }
    },
  },
  watch: {
    $route(newRoute) {
      this.updatePage(newRoute.query.key);
    },
  },
  created() {
    if (this.hotelName) {
      this.updatePage(this.hotelName);
    }
  },
};
</script>
