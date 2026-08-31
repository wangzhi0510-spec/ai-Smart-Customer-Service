import { createApp, h } from "vue";
import { createPinia } from "pinia";
import { router } from "./router";
import "./styles/theme.css";
import { RouterView } from "vue-router";

const Root = {
  components: { RouterView },
  render: () => h(RouterView),
};

createApp(Root).use(createPinia()).use(router).mount("#app");
