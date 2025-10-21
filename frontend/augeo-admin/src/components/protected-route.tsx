import { useEffect, type ReactNode } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useAuthStore } from '@/stores/auth-store'

interface ProtectedRouteProps {
  children: ReactNode
}

/**
 * ProtectedRoute component that checks authentication status.
 * Redirects to sign-in page if user is not authenticated.
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const navigate = useNavigate()
  const { auth } = useAuthStore()

  useEffect(() => {
    // Check if user is authenticated
    if (!auth.isAuthenticated) {
      // Redirect to sign-in with return URL
      navigate({
        to: '/sign-in',
        search: { redirect: window.location.pathname },
        replace: true,
      })
    }
  }, [auth.isAuthenticated, navigate])

  // If not authenticated, don't render children (will redirect)
  if (!auth.isAuthenticated) {
    return null
  }

  // Render protected content
  return <>{children}</>
}
