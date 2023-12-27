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
import axios from "axios";

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
      const existingItem = this.searchLocations.findIndex(
        (loc) => item === loc.location
      );

      if (existingItem < 0) {
        const id = Math.random() * (99999, 10000) + 10000; // temp id
        this.searchLocations.push({
          status: "ongoing",
          location: item,
          count: "0",
          id: id,
        });

        setTimeout(() => {
          this.searchLocations.forEach((location) => {
            if (location.id === id) location.status = "loaded";
          });
        }, 3000);
      }
    },
    loadLocations() {
      const getData = async () => {
        try {
          const resp = await axios.get(
            "http://localhost:7000/api/get-locations"
          );
          return resp;
        } catch (err) {
          console.log(err);
          return false;
        }
      };

      getData().then((resp) => {
        if (resp === false) {
          alert("There's an error when fetching locations. Please try again");
        } else {
          if (resp.status === 200) {
            const locations = resp.data["locations"];
            locations.forEach(({ count, id, search_key }) => {
              this.searchLocations.push({
                id: id,
                location: search_key,
                count: count,
                status: "loaded",
              });
            });
          }
        }
      });
    },
  },
  created() {
    this.loadLocations();
  },
};
</script>
