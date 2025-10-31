import { useCallback, useEffect, useState } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import apiClient from '@/lib/axios'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'

interface SessionExpirationWarningProps {
  /**
   * How many seconds before expiry to show warning
   * Default: 120 (2 minutes)
   */
  warningThresholdSeconds?: number
}

export function SessionExpirationWarning({
  warningThresholdSeconds = 120,
}: SessionExpirationWarningProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [secondsRemaining, setSecondsRemaining] = useState<number | null>(null)
  const [isExtending, setIsExtending] = useState(false)

  const { accessToken, refreshToken, reset } = useAuthStore()

  // Parse JWT to get expiration time
  const getTokenExpiry = useCallback((token: string): number | null => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.exp ? payload.exp * 1000 : null // Convert to milliseconds
    } catch {
      return null
    }
  }, [])

  // Extend session by refreshing the access token
  const handleExtendSession = useCallback(async () => {
    if (!refreshToken) return

    setIsExtending(true)

    try {
      const response = await apiClient.post('/auth/refresh', {
        refresh_token: refreshToken,
      })

      const { access_token } = response.data
      useAuthStore.getState().setAccessToken(access_token)

      // Close dialog on success
      setIsOpen(false)
      setSecondsRemaining(null)
    } catch {
      // If refresh fails, logout user
      // Session extension failed - redirect to login
      reset()
      window.location.href = '/sign-in'
    } finally {
      setIsExtending(false)
    }
  }, [refreshToken, reset])

  // Handle logout
  const handleLogout = useCallback(() => {
    reset()
    window.location.href = '/sign-in'
  }, [reset])

  // Monitor token expiration
  useEffect(() => {
    if (!accessToken) {
      setIsOpen(false)
      setSecondsRemaining(null)
      return
    }

    const expiryTime = getTokenExpiry(accessToken)
    if (!expiryTime) return

    // Check every 5 seconds to avoid rate limits
    const intervalId = setInterval(() => {
      const now = Date.now()
      const timeUntilExpiry = expiryTime - now
      const secondsUntilExpiry = Math.floor(timeUntilExpiry / 1000)

      // Show warning if within threshold
      if (
        secondsUntilExpiry <= warningThresholdSeconds &&
        secondsUntilExpiry > 0
      ) {
        setSecondsRemaining(secondsUntilExpiry)
        setIsOpen(true)
      }

      // Auto-logout if expired
      if (secondsUntilExpiry <= 0) {
        clearInterval(intervalId)
        reset()
        window.location.href = '/sign-in'
      }
    }, 5000) // Check every 5 seconds instead of 1 second

    return () => clearInterval(intervalId)
  }, [accessToken, warningThresholdSeconds, getTokenExpiry, reset])

  // Format seconds as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogContent>
        <AlertDialogHeader className='text-start'>
          <AlertDialogTitle>Session Expiring Soon</AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className='space-y-2'>
              <p>Your session will expire in:</p>
              <p className='text-foreground text-2xl font-bold'>
                {secondsRemaining !== null
                  ? formatTime(secondsRemaining)
                  : '--:--'}
              </p>
              <p className='text-sm'>
                Would you like to extend your session or log out now?
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <Button
            variant='outline'
            onClick={handleLogout}
            disabled={isExtending}
          >
            Log Out
          </Button>
          <Button onClick={handleExtendSession} disabled={isExtending}>
            {isExtending ? 'Extending...' : 'Stay Logged In'}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
