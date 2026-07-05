import { create } from "zustand";

const getLocalStorageItem = (key) => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  } catch (error) {
    console.error(`Error reading ${key} from localStorage:`, error);
    return null;
  }
};

const setLocalStorageItem = (key, value) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error writing ${key} to localStorage:`, error);
  }
};

const removeLocalStorageItem = (key) => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error(`Error removing ${key} from localStorage:`, error);
  }
};

export const useAuthStore = create((set) => ({
  token: getLocalStorageItem("token"),
  user: getLocalStorageItem("user"),
  isAuthenticated: !!getLocalStorageItem("token"),

  login: (token, user) => {
    setLocalStorageItem("token", token);
    setLocalStorageItem("user", user);
    set({ token, user, isAuthenticated: true });
  },

  logout: () => {
    removeLocalStorageItem("token");
    removeLocalStorageItem("user");
    set({ token: null, user: null, isAuthenticated: false });
  },

  updateUser: (updatedUser) => {
    set((state) => {
      const newUser = { ...state.user, ...updatedUser };
      setLocalStorageItem("user", newUser);
      return { user: newUser };
    });
  },
}));
