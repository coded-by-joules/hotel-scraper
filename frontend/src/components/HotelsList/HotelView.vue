<template>
  <p v-if="hotelName === null">Please select a location on the left side.</p>
  <p v-else>
    {{ hotelName }}
  </p>
</template>

<script>
import axios from "axios";

export default {
  props: ["hotelName"],
  methods: {
    loadHotels(search_key) {
      axios
        .get("http://localhost:7000/api/get-hotels?key=" + search_key)
        .then((response) => {
          console.log(response.data);
        });
    },
  },
  watch: {
    hotelName(new_key) {
      this.loadHotels(new_key);
    },
  },
};
</script>
