import html2canvas from 'html2canvas-pro'
import { jsPDF } from 'jspdf'

/**
 * 将 DOM 元素导出为 PDF
 * @param element 要导出的 DOM 元素
 * @param filename 文件名（不含扩展名）
 * @param watermark 是否添加水印
 */
export async function exportToPdf(
  element: HTMLElement,
  filename: string,
  watermark: boolean = false
): Promise<void> {
  // 截图时不碰 DOM，水印在 canvas 上绘制
  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    logging: false,
    backgroundColor: '#ffffff',
  })

  // 在 canvas 上绘制水印（纯像素操作，不影响页面）
  if (watermark) {
    const ctx = canvas.getContext('2d')!
    ctx.save()
    ctx.font = `${Math.round(canvas.width * 0.025)}px sans-serif`
    ctx.fillStyle = 'rgba(0,0,0,0.06)'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'

    for (let i = 0; i < 5; i++) {
      for (let j = 0; j < 8; j++) {
        const x = canvas.width * (0.12 + i * 0.2)
        const y = canvas.height * (0.08 + j * 0.13)
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(-35 * Math.PI / 180)
        ctx.fillText('Danmo Scholar', 0, 0)
        ctx.restore()
      }
    }
    ctx.restore()
  }

  const imgWidth = 210 // A4 宽度 mm
  const pageHeight = 297 // A4 高度 mm
  const imgHeight = (canvas.height * imgWidth) / canvas.width
  let heightLeft = imgHeight

  const pdf = new jsPDF('p', 'mm', 'a4')
  let position = 0

  pdf.addImage(canvas.toDataURL('image/jpeg', 0.95), 'JPEG', 0, position, imgWidth, imgHeight)
  heightLeft -= pageHeight

  while (heightLeft > 0) {
    position = heightLeft - imgHeight
    pdf.addPage()
    pdf.addImage(canvas.toDataURL('image/jpeg', 0.95), 'JPEG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight
  }

  pdf.save(`${filename}.pdf`)
}
