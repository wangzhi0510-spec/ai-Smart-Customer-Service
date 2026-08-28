import { createApp } from "vue";
import { createPinia } from "pinia";

const Root = {
  template: "<main><h1>AI 智能客服</h1></main>",
};

createApp(Root).use(createPinia()).mount("#app");

