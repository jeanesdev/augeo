import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import apiClient from '@/lib/axios'

interface AuthUser {
  id: string
  email: string
  first_name: string
  last_name: string
  role: string
  npo_id: string | null
}

interface LoginRequest {
  email: string
  password: string
}

interface RegisterRequest {
  email: string
  password: string
  first_name: string
  last_name: string
  phone?: string
}

interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: AuthUser
}

interface RegisterResponse {
  user: {
    id: string
    email: string
    first_name: string
    last_name: string
    phone: string | null
    email_verified: boolean
    is_active: boolean
    role: string
    created_at: string
  }
  message: string
}

interface AuthState {
  auth: {
    user: AuthUser | null
    accessToken: string
    refreshToken: string
    isAuthenticated: boolean
    isLoading: boolean
    error: string | null

    // Actions
    setUser: (user: AuthUser | null) => void
    setAccessToken: (accessToken: string) => void
    setRefreshToken: (refreshToken: string) => void
    setError: (error: string | null) => void
    setLoading: (loading: boolean) => void
    reset: () => void

    // API methods
    login: (credentials: LoginRequest) => Promise<LoginResponse>
    register: (data: RegisterRequest) => Promise<RegisterResponse>
    logout: () => Promise<void>
    getUser: () => AuthUser | null
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      auth: {
        user: null,
        accessToken: '',
        refreshToken: '',
        isAuthenticated: false,
        isLoading: false,
        error: null,

        // Setters
        setUser: (user) =>
          set((state) => ({
            ...state,
            auth: {
              ...state.auth,
              user,
              isAuthenticated: !!user,
            },
          })),

        setAccessToken: (accessToken) =>
          set((state) => ({
            ...state,
            auth: { ...state.auth, accessToken },
          })),

        setRefreshToken: (refreshToken) =>
          set((state) => ({
            ...state,
            auth: { ...state.auth, refreshToken },
          })),

        setError: (error) =>
          set((state) => ({
            ...state,
            auth: { ...state.auth, error },
          })),

        setLoading: (loading) =>
          set((state) => ({
            ...state,
            auth: { ...state.auth, isLoading: loading },
          })),

        reset: () =>
          set((state) => ({
            ...state,
            auth: {
              ...state.auth,
              user: null,
              accessToken: '',
              refreshToken: '',
              isAuthenticated: false,
              error: null,
            },
          })),

        // API methods
        login: async (credentials: LoginRequest): Promise<LoginResponse> => {
          const { auth } = get()
          auth.setLoading(true)
          auth.setError(null)

          try {
            const response = await apiClient.post<LoginResponse>(
              '/auth/login',
              credentials
            )

            const { access_token, refresh_token, user } = response.data

            // Update store
            auth.setAccessToken(access_token)
            auth.setRefreshToken(refresh_token)
            auth.setUser(user)

            return response.data
          } catch (error: unknown) {
            const errorMessage =
              (error as { response?: { data?: { error?: { message?: string } } }; message?: string }).response?.data?.error?.message ||
              (error as { message?: string }).message ||
              'Login failed'
            auth.setError(errorMessage)
            throw error
          } finally {
            auth.setLoading(false)
          }
        },

        register: async (
          data: RegisterRequest
        ): Promise<RegisterResponse> => {
          const { auth } = get()
          auth.setLoading(true)
          auth.setError(null)

          try {
            const response = await apiClient.post<RegisterResponse>(
              '/auth/register',
              data
            )

            return response.data
          } catch (error: unknown) {
            const errorMessage =
              (error as { response?: { data?: { error?: { message?: string } } }; message?: string }).response?.data?.error?.message ||
              (error as { message?: string }).message ||
              'Registration failed'
            auth.setError(errorMessage)
            throw error
          } finally {
            auth.setLoading(false)
          }
        },

        logout: async (): Promise<void> => {
          const { auth } = get()
          const { accessToken } = auth

          try {
            // Call logout endpoint if token exists
            if (accessToken) {
              await apiClient.post('/auth/logout')
            }
          } catch (_error) {
            // Silently fail - we still want to clear local state
            // Error is expected if token is already invalid
          } finally {
            // Always clear local state
            auth.reset()
          }
        },

        getUser: (): AuthUser | null => {
          const { auth } = get()
          return auth.user
        },
      },
    }),
    {
      name: 'augeo-auth-storage',
      partialize: (state) => ({
        auth: {
          user: state.auth.user,
          accessToken: state.auth.accessToken,
          refreshToken: state.auth.refreshToken,
          isAuthenticated: state.auth.isAuthenticated,
        },
      }),
    }
  )
)
