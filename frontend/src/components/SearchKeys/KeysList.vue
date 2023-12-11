<template>
  <div class="border-r-2 border-black w-1/5 pt-3 pl-3 pb-3">
    <nav class="flex flex-col text-right justify-end">
      <key-item
        v-for="searchKey in searchKeys"
        :key="searchKey.id"
        :location="searchKey.location"
        :active="isActive(searchKey.id)"
        @click="setActiveItem(searchKey.id)"
      ></key-item>
    </nav>
  </div>
</template>

<script>
import KeyItem from "./KeyItem.vue";
export default {
  components: {
    "key-item": KeyItem,
  },
  props: ["searchKeys"],
  data() {
    return {
      activeKey: "",
    };
  },
  methods: {
    setActiveItem(item) {
      this.activeKey = item;
    },
    isActive(item) {
      return this.activeKey == item;
    },
  },
};
</script>
