<template>
  <div v-if="hotelFound">
    <h1 class="text-2xl font-bold">Hotels for "{{ hotelName }}"</h1>

    <p v-if="!savedInDB || hotelList.length == 0" class="mt-4 text-sm">
      The server is still scraping data for this search key. If you still see
      this message for a while, you can
      <a
        class="text-blue-700 underline cursor-pointer"
        href="#"
        @click="retrySearch"
        >click here</a
      >
      to search it again.
    </p>

    <img
      v-if="loadingData"
      src="../../assets/loading.gif"
      class="w-20 mx-auto mt-5"
    />
    <div v-else-if="!loadingData && hotelList.length > 0" class="mt-5">
      <table
        class="table-fixed text-sm items-center border-collapse overflow-x-auto"
      >
        <thead class="border-b-2 border-black">
          <tr>
            <th
              class="px-6 bg-blueGray-50 text-blueGray-500 align-middle border border-solid border-blueGray-100 py-3 text-xs uppercase border-l-0 border-r-0 whitespace-nowrap font-semibold text-left"
            >
              Hotel Name
            </th>
            <th
              class="px-6 bg-blueGray-50 text-blueGray-500 align-middle border border-solid border-blueGray-100 py-3 text-xs uppercase border-l-0 border-r-0 whitespace-nowrap font-semibold text-left"
            >
              Address
            </th>
            <th
              class="px-6 bg-blueGray-50 text-blueGray-500 align-middle border border-solid border-blueGray-100 py-3 text-xs uppercase border-l-0 border-r-0 whitespace-nowrap font-semibold text-left"
            >
              Phone
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="hotel in hotelList">
            <td
              class="font-bold underline text-blue-500 border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-nowrap p-4 text-left text-blueGray-700"
            >
              <a :href="hotel['url']" target="_blank">{{
                hotel["hotel_name"]
              }}</a>
            </td>
            <td
              class="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-nowrap p-4"
            >
              {{ hotel["address"] }}
            </td>
            <td
              class="border-t-0 px-6 align-middle border-l-0 border-r-0 text-xs whitespace-nowrap p-4"
            >
              {{ hotel["phone"] }}
            </td>
          </tr>
        </tbody>
      </table>
      <a
        href="#top"
        class="inline-block mt-3 px-3 py-2 rounded text-white text-sm bg-green-500"
      >
        Back to top
      </a>
    </div>

    <div class="mt-5" v-else></div>
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
  inject: ["locations", "printMessage"],
  data() {
    return {
      hotelName: this.$route.query.key,
      savedInDB: false,
      hotelFound: false,
      loadingData: true,
      hotelList: [],
    };
  },
  computed: {
    getLocations() {
      return this.locations();
    },
  },
  methods: {
    loadHotels() {
      const search_key = encodeURIComponent(this.hotelName);
      this.loadingData = true;
      this.hotelList = [];

      axios
        .get(
          "http://localhost:7000/api/get-hotels?key=" +
            encodeURIComponent(search_key)
        )
        .then((response) => {
          this.hotelList = response.data["hotels"];
          console.log(this.hotelList);
          this.loadingData = false;
        })
        .catch((error) => {
          this.loadingData = false;
          if (this.savedInDB) {
            this.printMessage(
              "Hotel list for this key was not found. Please add a new search"
            );
          }
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

        this.loadHotels();
      } else {
        this.hotelFound = false;
      }
    },
    retrySearch() {
      this.$emit("onSearchHotel", this.hotelName);
      router.push({ name: "main" });
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
