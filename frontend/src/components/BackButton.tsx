import React from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

interface BackButtonProps {
  to?: string
  label?: string
  className?: string
}

const BackButton: React.FC<BackButtonProps> = ({ to, label = '返回', className = '' }) => {
  const navigate = useNavigate()

  const handleClick = () => {
    if (to) {
      navigate(to)
    } else {
      navigate(-1)
    }
  }

  return (
    <button
      onClick={handleClick}
      className={`inline-flex items-center space-x-1.5 px-3 py-1.5 text-sm text-slate-600 transition-colors hover:text-slate-900 ${className}`}
    >
      <ArrowLeft className="h-4 w-4" />
      <span>{label}</span>
    </button>
  )
}

export default BackButton
