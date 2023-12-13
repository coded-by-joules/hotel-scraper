<template>
  <div class="border-gray-400 border-b-2 p-4">
    <form @submit.prevent="formSubmit" class="flex justify-between">
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
    <p
      class="mt-3 p-2 border-green-300 bg-green-200 rounded border-2"
      v-if="message !== ''"
    >
      {{ message }}
    </p>
  </div>
</template>

<script>
export default {
  props: ["message"],
  data() {
    return {
      searchStr: "",
    };
  },
  methods: {
    formSubmit() {
      if (this.searchStr !== "") {
        this.$emit("onSearchHotel", this.searchStr);
        this.searchStr = "";
      }
    },
  },
};
</script>
