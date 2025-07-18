import { defineStore, acceptHMRUpdate } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    isAuthenticated: false
  }),

  getters: {
    getUser: (state) => state.user,
    getToken: (state) => state.token,
    isAuth: (state) => state.isAuthenticated
  },

  actions: {
    initializeStore() {
      const user = localStorage.getItem("user");
      const token = localStorage.getItem("token");
      if (user && token) {
        this.isAuthenticated = true;
        this.user = JSON.parse(user);
        this.token = token;
      }
    },
    setAuthData(data) {
      this.user = data.user || null;
      this.token = data.access_token || null;
      this.isAuthenticated = true;
    },
    clearAuthData() {
      this.user = null;
      this.token = null;
      this.isAuthenticated = false;
    }
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot))
}