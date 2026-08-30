import { createApp } from "vue";
import { createPinia } from "pinia";
import { router } from "./router";

const Root = {
  template: "<main><h1>AI 智能客服</h1></main>",
};

createApp(Root).use(createPinia()).use(router).mount("#app");
