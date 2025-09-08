import { boot } from "quasar/wrappers";
import axios from "axios";

// Be careful when using SSR for cross-request state pollution
// due to creating a Singleton instance here;
// If any client changes this (global) instance, it might be a
// good idea to move this instance creation inside of the
// "export default () => {}" function below (which runs individually
// for each client)

const api = axios.create({ baseURL: 'http://127.0.0.1:8001' });
//const api = axios.create({ baseURL: 'http://toir.atu.mmk.ru:8877' });


const token = localStorage.getItem("token");
if (token) {
  api.defaults.headers["Authorization"] = token;
}

export default boot(({ app, router }) => {
  app.config.globalProperties.$axios = axios;
  app.config.globalProperties.$api = api;

  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if ([401, 403].includes(error.response?.status)) {
        localStorage.removeItem("token");
        delete api.defaults.headers["Authorization"];
        router.push({ name: "Authorization" });
      }
    }
  );
});

export { api, axios }
