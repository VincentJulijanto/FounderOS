export async function exportBoardMemoPdf(
  element: HTMLElement,
  filename: string,
): Promise<void> {
  const { default: html2pdf } = await import('html2pdf.js')

  // html2pdf re-clones the source into its own A4-width container; an
  // absolutely-positioned source collapses that container to height 0 and the
  // capture comes out blank. So: hand it a STATIC clone, parked in an invisible
  // holder behind the app (opaque canvas background hides it), removed after.
  // A4 inner width with 12mm margins = 186mm ≈ 703px @96dpi. The clone must
  // match it exactly or the right edge clips out of the page.
  const A4_INNER_PX = 703
  const holder = document.createElement('div')
  holder.style.cssText =
    `position:absolute;left:0;top:0;z-index:-1000;pointer-events:none;width:${A4_INNER_PX}px`
  const clone = element.cloneNode(true) as HTMLElement
  clone.style.position = 'static'
  clone.style.left = '0'
  clone.style.width = `${A4_INNER_PX}px`
  holder.appendChild(clone)
  document.body.appendChild(holder)

  try {
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
      .from(clone)
      .save()
  } finally {
    holder.remove()
  }
}
