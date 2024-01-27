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
import { socket } from "./socket";
import axios from "axios";

const getLocationById = (arr, id) => {
  const locationItem = arr.findIndex((item) => item.id === id);

  return locationItem;
};

const getLocationByQueueID = (arr, queue_id) => {
  const locationIndex = arr.findIndex((item) => item["queue_id"] === queue_id);

  return locationIndex;
};
const host_url = import.meta.env.DEV ? "http://localhost:5000" : "";

export default {
  components: {
    "the-header": TheHeader,
    "search-box": SearchBox,
    "location-list": LocationList,
  },
  emits: ["onStartSearch"],
  provide() {
    return {
      refreshLocation: (item) => this.reScrape(item),
      deleteLocation: (item) => this.deleteItem(item),
      host_url: () => host_url,
    };
  },
  data() {
    return {
      searchLocations: [],
    };
  },
  methods: {
    startSraping: async (item) => {
      try {
        const resp = await axios.post(`${host_url}/api/start-scraping`, {
          "search-text": item.location,
        });

        return resp;
      } catch (err) {
        console.log(err);
        return false;
      }
    },
    addSearch(item) {
      const existingItem = this.searchLocations.findIndex(
        (loc) => item === loc.location
      );

      if (existingItem < 0) {
        const id = Math.random() * (99999, 10000) + 10000; // temp id
        const newItem = {
          status: "ongoing",
          location: item,
          count: "0",
          id: id,
          queue_id: null,
          progress: 0,
        };

        const locationList = this.searchLocations;
        locationList.push(newItem);

        this.startSraping(newItem).then((response) => {
          const itemIndex = getLocationById(locationList, newItem.id);

          if (response === false) {
            locationList[itemIndex].status = "error";
          } else {
            if (response.status === 200) {
              const fetchedItem = response.data;

              locationList[itemIndex]["queue_id"] = fetchedItem["queue_id"];
              locationList[itemIndex]["progress"] = 0;
            }
          }
        });
      } else {
        alert("Search key already exists.");
      }
    },
    reScrape(item) {
      const locationList = this.searchLocations;
      const locationIndex = getLocationById(locationList, item.id);

      if (locationIndex >= 0) {
        const locationItem = locationList[locationIndex];

        locationItem.status = "ongoing";
        this.startSraping(locationItem).then((response) => {
          if (response === false) {
            locationItem.status = "error_retain";
          } else {
            const fetchedItem = response.data;

            locationItem.status = "ongoing";
            locationItem.queue_id = fetchedItem["queue_id"];
            locationItem.progress = 0;
          }
        });
      }
    },
    deleteItem(item) {
      const locationList = this.searchLocations;
      const locationIndex = getLocationById(locationList, item.id);
      const locationItem = locationList[locationIndex];

      locationItem.status = "deleting";
      const commenceDelete = async (item) => {
        try {
          console.log(item.location);
          const response = await axios.post(`${host_url}/api/delete-location`, {
            search_text: item.location,
          });
          return response;
        } catch (err) {
          console.log(err);
          return false;
        }
      };

      commenceDelete(locationItem).then((response) => {
        if (response === false) {
          locationItem.status = "error_delete";
        } else {
          if (response.status === 200) locationList.splice(locationIndex, 1);
        }
      });
    },
    loadLocations() {
      const getData = async () => {
        try {
          const resp = await axios.get(`${host_url}/api/get-locations`);
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
            locations.forEach(({ count, id, search_key, queue_code }) => {
              let status_message = "ongoing";

              if (queue_code === null) {
                status_message = "loaded";
              }

              this.searchLocations.push({
                id: id,
                location: search_key,
                count: count,
                status: status_message,
                queue_id: queue_code,
                progress: 0,
              });
            });
          }
        }
      });
    },
    messageReceived(count, queue_id, status) {
      const locationIndex = getLocationByQueueID(
        this.searchLocations,
        queue_id
      );
      const locationItem = this.searchLocations[locationIndex];
      let status_message = "loaded";

      if (status === "ERROR") {
        if (locationItem.count > 0) status_message = "error_retain";
        else status_message = "error";
      }

      locationItem.status = status_message;
      locationItem.count = count;
      locationItem.queue_id = null;
      locationItem.progress = 0;
    },
    updateProgressBar(queue_id, progress) {
      const locationIndex = getLocationByQueueID(
        this.searchLocations,
        queue_id
      );
      const locationItem = this.searchLocations[locationIndex];

      locationItem.progress = progress;
    },
  },
  created() {
    this.loadLocations();
  },
  mounted() {
    socket.on("message", this.messageReceived);
    socket.on("progress", this.updateProgressBar);
  },
};
</script>
