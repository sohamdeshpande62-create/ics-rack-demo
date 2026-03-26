import { useState, useEffect, useCallback } from 'react'
import { getLockStatus, updateLockStatus } from '../api/client.js'

export function useRack(rackId) {
  const [locked, setLocked] = useState(null)
  const [error, setError] = useState(null)

  const fetchLockStatus = useCallback(async () => {
    try {
      const status = await getLockStatus(rackId)
      setLocked(status)
    } catch (e) {
      setError(e.message)
    }
  }, [rackId])

  useEffect(() => {
    fetchLockStatus()
  }, [fetchLockStatus])

  const lock = useCallback(async () => {
    await updateLockStatus(rackId, true)
    setLocked(true)
  }, [rackId])

  const unlock = useCallback(async () => {
    await updateLockStatus(rackId, false)
    setLocked(false)
  }, [rackId])

  return { locked, lock, unlock, refetch: fetchLockStatus, error }
}
