import React from 'react'
import type { BoardResponse } from '@/lib/types'

export async function exportBoardMemoPdf(
  response: BoardResponse,
  companyName: string | undefined,
  question: string | undefined,
  filename: string,
): Promise<void> {
  const [{ pdf }, { default: BoardMemoPdfDoc }] = await Promise.all([
    import('@react-pdf/renderer'),
    import('@/components/BoardMemoPdf'),
  ])

  const blob = await pdf(
    <BoardMemoPdfDoc response={response} companyName={companyName} question={question} />
  ).toBlob()

  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 10_000)
}
