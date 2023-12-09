<template>
  <form
    @submit.prevent="formSubmit"
    class="p-4 border-gray-400 border-b-2 flex justify-between"
  >
    <input
      type="text"
      id="searchBox"
      class="border-gray-700 border-solid border-2 p-2 rounded w-3/4"
      name="Search"
      placeholder="Enter a location"
      v-model="searchStr"
    />
    <button
      type="submit"
      class="mx-3 w-1/4 py-2 bg-green-600 font-bold text-white rounded hover:bg-green-500"
    >
      Search
    </button>
  </form>
</template>

<script>
export default {
  props: ["searchText"],
  data() {
    return {
      searchStr: "",
    };
  },
  methods: {
    formSubmit() {
      if (this.searchStr !== "") {
        this.searchText = this.searchStr;
        this.$emit("onSearchHotel");
      }
    },
  },
};
</script>
