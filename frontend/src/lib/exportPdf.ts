export async function exportBoardMemoPdf(
  element: HTMLElement,
  filename: string,
): Promise<void> {
  const { default: html2pdf } = await import('html2pdf.js')

  await html2pdf()
    .set({
      margin: [12, 12, 12, 12] as [number, number, number, number],
      filename,
      image: { type: 'jpeg' as const, quality: 0.97 },
      html2canvas: {
        scale: 2,
        useCORS: true,
        letterRendering: true,
        backgroundColor: '#ffffff',
      } as object,
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' as const },
      // pagebreak is a valid runtime option not reflected in the shipped types
      ...(({ pagebreak: { mode: ['avoid-all', 'css'] } }) as object),
    })
    .from(element)
    .save()
}
