import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  // 2FA state
  pendingEmail: string | null;
  devOtp: string | null;
  requires2FA: boolean;

  setAuth: (user: User, token: string, refreshToken?: string | null) => void;
  logout: () => Promise<void>;
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
      refreshToken: null,
      isAuthenticated: false,

      // 2FA state
      pendingEmail: null,
      devOtp: null,
      requires2FA: false,

      setAuth: (user, token, refreshToken = null) => {
        localStorage.setItem('access_token', token);
        localStorage.setItem('token', token);
        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken);
        }
        set({
          user,
          token,
          refreshToken,
          isAuthenticated: true,
          // Clear 2FA state on successful auth
          pendingEmail: null,
          devOtp: null,
          requires2FA: false,
        });
      },

      logout: async () => {
        const token = localStorage.getItem('access_token');
        if (token) {
          try {
            await fetch('/api/v1/auth/logout', {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}` },
            });
          } catch {
            // Ignorar error de red o backend durante logout
          }
        }

        localStorage.removeItem('access_token');
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('auth-storage');
        sessionStorage.clear();

        // Reemplazar historial para evitar volver a rutas protegidas con "Atrás"
        window.history.pushState(null, '', '/login');
        window.history.pushState(null, '', '/login');
        window.history.replaceState(null, '', '/login');

        set({
          user: null,
          token: null,
          refreshToken: null,
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
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
