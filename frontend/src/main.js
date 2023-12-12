import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import "./style.css";

import App from "./App.vue";

import NotFound from "./components/NotFound.vue";
import HotelLoad from "./components/HotelsList/HotelLoad.vue";
import HotelView from "./components/HotelsList/HotelView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: HotelLoad },
    {
      name: "hotel",
      path: "/hotel/:hotelName",
      component: HotelView,
      props: true,
    },
    { path: "/:notFound(.*)", component: NotFound },
  ],
});

const app = createApp(App);

app.use(router);
app.mount("#app");
