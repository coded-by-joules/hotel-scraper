<template>
  <div class="border-b-2 border-black pt-3">
    <nav class="flex flex-row justify-start grow">
      <key-item
        v-for="searchKey in searchKeys"
        :key="searchKey.id"
        :location="searchKey['search_key']"
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
    loadKeys() {},
  },
};
</script>
