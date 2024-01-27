<template>
  <div class="border-gray-400 border-b-2 p-4" id="top">
    <form
      @submit.prevent="formSubmit"
      class="flex justify-between"
      autocomplete="off"
    >
      <input
        type="text"
        id="searchBox"
        class="border-gray-700 border-solid border-b-2 p-2 rounded w-3/4 outline-none text-white bg-transparent"
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
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchStr: "",
    };
  },
  methods: {
    formSubmit() {
      if (this.searchStr !== "") {
        this.$emit("onStartSearch", this.searchStr);
        this.searchStr = "";
      }
    },
  },
};
</script>
