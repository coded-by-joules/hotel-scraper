<template>
  <the-header></the-header>
  <main class="container mx-auto p-5 max-w-screen-lg">
    <search-box @onSearchHotel="fetchHotels" :message="messageStr"></search-box>
    <div class="mt-3" v-if="searchLocations.length > 0">
      <keys-list :search-keys="searchLocations"></keys-list>
      <div class="p-3">
        <router-view @onSearchHotel="fetchHotels"></router-view>
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
      searchLocations: [],
      messageStr: "",
      timerMessage: null,
    };
  },
  created() {
    this.loadLocations();
  },
  provide() {
    return {
      locations: () => this.searchLocations,
      printMessage: (msg) => this.setMessage(msg),
    };
  },
  methods: {
    clearMessage() {
      this.messageStr = "";
    },
    setMessage(msg) {
      this.messageStr = msg;
      clearTimeout(this.timerMessage);
      this.timerMessage = setTimeout(this.clearMessage, 5000);
    },
    fetchHotels(searchText) {
      this.setMessage("Scraping started successfully");

      axios
        .post("http://localhost:7000/api/start-scraping", {
          "search-text": encodeURIComponent(searchText),
        })
        .then((response) => {
          if (response.status === 200) {
            const existingLocation = this.searchLocations.findIndex((item) => {
              return searchText === item["search_key"];
            });

            if (existingLocation < 0) {
              this.searchLocations.push({
                id: Math.random() * (99999, 10000) + 10000, // temp id
                search_key: searchText,
                savedInDB: false,
              });
            } else {
              this.searchLocations[existingLocation].id = location["id"];
              this.searchLocations[existingLocation].savedInDB = true;
            }

            this.loadLocations();
          }
        })
        .catch((error) => {
          this.setMessage(error.response.data["message"]);
        });
    },
    loadLocations() {
      axios.get("http://localhost:7000/api/get-locations").then((response) => {
        if (response.status === 200) {
          const locations = response.data["locations"];

          locations.forEach((location) => {
            const existingIndex = this.searchLocations.findIndex((item) => {
              return item["search_key"] === location["search_key"];
            });

            if (existingIndex >= 0) {
              const existingLocation = this.searchLocations[existingIndex];
              existingLocation["id"] = location["id"];
              existingLocation["savedInDB"] = true;
            } else {
              this.searchLocations.push({
                id: location["id"],
                search_key: location["search_key"],
                savedInDB: true,
              });
            }
          });
        }
      });
    },
  },
};
</script>
