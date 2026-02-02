import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;

  // 2FA state
  pendingEmail: string | null;
  devOtp: string | null;
  requires2FA: boolean;

  setAuth: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;

  // 2FA actions
  setPending2FA: (email: string, devOtp?: string | null) => void;
  clear2FA: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      // 2FA state
      pendingEmail: null,
      devOtp: null,
      requires2FA: false,

      setAuth: (user, token) => {
        localStorage.setItem('access_token', token);
        set({
          user,
          token,
          isAuthenticated: true,
          // Clear 2FA state on successful auth
          pendingEmail: null,
          devOtp: null,
          requires2FA: false,
        });
      },

      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth-storage');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          pendingEmail: null,
          devOtp: null,
          requires2FA: false,
        });
      },

      updateUser: (userData) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        }));
      },

      setPending2FA: (email, devOtp = null) => {
        set({
          requires2FA: true,
          pendingEmail: email,
          devOtp: devOtp || null,
        });
      },

      clear2FA: () => {
        set({
          requires2FA: false,
          pendingEmail: null,
          devOtp: null,
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
