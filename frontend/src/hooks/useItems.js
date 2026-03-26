import { useState, useEffect, useCallback } from 'react'
import { getAllItems } from '../api/client.js'

export function useItems(rackId) {
  const [items, setItems] = useState([])
  const [error, setError] = useState(null)

  const refetch = useCallback(async () => {
    try {
      const data = await getAllItems(rackId)
      setItems(data)
    } catch (e) {
      // 404 means no items yet — treat as empty list
      if (e.message === 'Item not found') {
        setItems([])
      } else {
        setError(e.message)
      }
    }
  }, [rackId])

  useEffect(() => {
    refetch()
  }, [refetch])

  return { items, setItems, refetch, error }
}
