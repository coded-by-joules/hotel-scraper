<template>
  <div class="border-r-2 border-black w-1/5 pt-3 pl-3 pb-3">
    <nav class="flex flex-col text-right justify-end">
      <div
        :class="[
          'listItem',
          { active: activeKey === 'item1', regular: activeKey !== 'item1' },
        ]"
        @click="setActiveItem('item1')"
      >
        Alaska
      </div>
      <div
        :class="[
          'listItem',
          { active: activeKey === 'item2', regular: activeKey !== 'item2' },
        ]"
        @click="setActiveItem('item2')"
      >
        Colorado
      </div>
      <div
        :class="[
          'listItem',
          { active: activeKey === 'item3', regular: activeKey !== 'item3' },
        ]"
        @click="setActiveItem('item3')"
      >
        Alabama
      </div>
      <div
        :class="[
          'listItem',
          { active: activeKey === 'item4', regular: activeKey !== 'item4' },
        ]"
        @click="setActiveItem('item4')"
      >
        California
      </div>
      <div
        :class="[
          'listItem',
          { active: activeKey === 'item5', regular: activeKey !== 'item5' },
        ]"
        @click="setActiveItem('item5')"
      >
        Washington
      </div>
    </nav>
  </div>
</template>

<script>
export default {
  data() {
    return {
      activeKey: "",
    };
  },
  methods: {
    setActiveItem(item) {
      this.activeKey = item;
    },
  },
};
</script>

<style scoped>
.listItem {
  @apply truncate pl-2 py-2 pr-3 mb-3 rounded-tl rounded-br border-r-0 shadow text-sm cursor-pointer;
}

.active {
  @apply bg-green-500 font-bold text-white;
}

.regular {
  @apply bg-green-300 font-bold;
}
</style>
