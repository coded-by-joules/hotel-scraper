<template>
  <div :class="setupClass" :key="location.id">
    <div class="px-3">
      <span class="font-semibold">{{ location.location }}</span> |
      <span class="text-sm font-normal">{{ hotelStatus }}</span>
    </div>
    <div class="flex justify-end">
      <a
        href="#"
        class="flex items-center justify-center hover:bg-blue-500 w-8"
        v-if="location.status === 'loaded' || location.status === 'error' || location.status === 'error_retain'"
        @click="refreshLoc()"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="w-6 h-6"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
          />
        </svg>
      </a>
      <a
        href="#"
        class="flex items-center justify-center hover:bg-green-800 w-8"
        @click="downloadData()"
        v-if="location.status === 'loaded'"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          class="w-6 h-6"
        >
          <path
            fill-rule="evenodd"
            d="M12 2.25a.75.75 0 0 1 .75.75v11.69l3.22-3.22a.75.75 0 1 1 1.06 1.06l-4.5 4.5a.75.75 0 0 1-1.06 0l-4.5-4.5a.75.75 0 1 1 1.06-1.06l3.22 3.22V3a.75.75 0 0 1 .75-.75Zm-9 13.5a.75.75 0 0 1 .75.75v2.25a1.5 1.5 0 0 0 1.5 1.5h13.5a1.5 1.5 0 0 0 1.5-1.5V16.5a.75.75 0 0 1 1.5 0v2.25a3 3 0 0 1-3 3H5.25a3 3 0 0 1-3-3V16.5a.75.75 0 0 1 .75-.75Z"
            clip-rule="evenodd"
          />
        </svg>
      </a>
      <a
        href="#"
        class="flex items-center justify-center text-center hover:bg-red-800 w-8"
        @click="deleteItem()"
        v-if="location.status === 'loaded'"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          class="w-6 h-6"
        >
          <path
            fill-rule="evenodd"
            d="M16.5 4.478v.227a48.816 48.816 0 0 1 3.878.512.75.75 0 1 1-.256 1.478l-.209-.035-1.005 13.07a3 3 0 0 1-2.991 2.77H8.084a3 3 0 0 1-2.991-2.77L4.087 6.66l-.209.035a.75.75 0 0 1-.256-1.478A48.567 48.567 0 0 1 7.5 4.705v-.227c0-1.564 1.213-2.9 2.816-2.951a52.662 52.662 0 0 1 3.369 0c1.603.051 2.815 1.387 2.815 2.951Zm-6.136-1.452a51.196 51.196 0 0 1 3.273 0C14.39 3.05 15 3.684 15 4.478v.113a49.488 49.488 0 0 0-6 0v-.113c0-.794.609-1.428 1.364-1.452Zm-.355 5.945a.75.75 0 1 0-1.5.058l.347 9a.75.75 0 1 0 1.499-.058l-.346-9Zm5.48.058a.75.75 0 1 0-1.498-.058l-.347 9a.75.75 0 0 0 1.5.058l.345-9Z"
            clip-rule="evenodd"
          />
        </svg>
      </a>
    </div>
  </div>
</template>

<script>
export default {
  props: ["location"],
  inject: ["refreshLocation", "deleteLocation", "host_url"],
  data() {
    return {
      progressBar: 0
    };
  },
  computed: {
    hotelStatus() {
      if (this.location.status === "loaded") {
        return `${this.location.count} hotel(s)`;
      } else if (this.location.status === "error") {
        return "error occured while scraping this location";
      } else if (this.location.status === "error_retain") {
        return `${this.location.count} hotel(s) | an error occured while rescraping, no new hotels were added`;
      } else if (this.location.status === "deleting") {
        return "deleting...";
      } else if (this.location.status === "error_delete") {
        return `an error occured while deleting this item`;
      } else {
        return "scraping...";
      }
    },
    setupClass() {
      const progress = this.location.progress;
      const status = this.location.status;

      console.log("Current progress: " + progress);
      if (status != "ongoing")
        return ["item", status];
      else {
        const progressPercents = ["after:w-0", 
        "after:w-1/6", 
        "after:w-1/3", 
        "after:w-1/2", 
        "after:w-2/3", 
        "after:w-5/6", 
        "after:w-full"];
        return ["item", status, progressPercents[progress]];
      }
    },
  },
  methods: {
    
    refreshLoc() {
      this.refreshLocation(this.location);
    },
    downloadData() {
      window.open(
        `${this.host_url()}/api/download-file?key=${encodeURIComponent(
          this.location.location
        )}`
      );
    },
    deleteItem() {
      this.deleteLocation(this.location);
    },
  },
};
</script>

<style scoped>
.item {
  @apply my-3 text-white border-4 border-transparent flex justify-between h-12 leading-10 align-middle relative;
}
.ongoing {
  @apply border-white;
}

.ongoing:after {
    content:'\A';
    background-color: rgb(22, 163, 74);
    top:0; 
    bottom:0;
    position: absolute;
    left:0; 
    opacity: 0.3;
    transition: all 2s;
}


.loaded {
  @apply bg-green-600;
}


.error,
.error_retain,
.deleting,
.error_delete {
  @apply bg-red-700;
}
</style>
