import { useSearchParams } from 'react-router-dom'
import { ComparisonMatrixLanding } from './ComparisonMatrixLanding'
import { ComparisonMatrixViewer } from './ComparisonMatrixViewer'

export function ComparisonMatrixPage() {
  const [searchParams] = useSearchParams()
  const taskId = searchParams.get('task_id')

  if (taskId) {
    return <ComparisonMatrixViewer taskId={taskId} />
  }

  return <ComparisonMatrixLanding />
}
