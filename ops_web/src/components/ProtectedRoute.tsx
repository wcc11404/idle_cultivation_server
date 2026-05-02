import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { getOpsToken } from '../services/api'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  if (!getOpsToken()) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}
