/**
 * Markdown 和 HTML 转换工具
 * 用于 Tiptap 编辑器与 Markdown 格式之间的转换
 */

/**
 * 将 Markdown 转换为 HTML（用于初始化编辑器）
 */
export function markdownToHTML(markdown: string): string {
  if (!markdown) return ''

  let html = markdown

  // 标题
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')

  // 加粗和斜体
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/___(.+?)___/g, '<strong><em>$1</em></strong>')
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>')
  html = html.replace(/_(.+?)_/g, '<em>$1</em>')

  // 行内代码
  html = html.replace(/`(.+?)`/g, '<code>$1</code>')

  // 链接
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')

  // 图片
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />')

  // 无序列表
  html = html.replace(/^\* (.+)$/gim, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')

  // 有序列表
  html = html.replace(/^\d+\. (.+)$/gim, '<li>$1</li>')

  // 引用
  html = html.replace(/^> (.+)$/gim, '<blockquote><p>$1</p></blockquote>')

  // 水平线
  html = html.replace(/^---$/gim, '<hr />')

  // 单个换行转换为 <br>（在处理段落之前）
  html = html.replace(/\n/g, '<br />')

  // 段落（双换行）
  html = html.replace(/<br \/><br \/>/g, '</p><p>')
  html = `<p>${html}</p>`

  // 清理多余的 <p> 标签
  html = html.replace(/<p><\/p>/g, '')
  html = html.replace(/<p>(<h[1-6]>)/g, '$1')
  html = html.replace(/(<\/h[1-6]>)<\/p>/g, '$1')
  html = html.replace(/<p>(<ul>)/g, '$1')
  html = html.replace(/(<\/ul>)<\/p>/g, '$1')
  html = html.replace(/<p>(<blockquote>)/g, '$1')
  html = html.replace(/(<\/blockquote>)<\/p>/g, '$1')
  html = html.replace(/<p>(<hr \/>)<\/p>/g, '$1')

  // 清理标题和列表中的 <br /> 标签
  html = html.replace(/(<h[1-6]>[^<]*)<br \/>/g, '$1')
  html = html.replace(/<br \/>(<\/h[1-6]>)/g, '$1')
  html = html.replace(/(<li>[^<]*)<br \/>/g, '$1')
  html = html.replace(/<br \/>(<\/li>)/g, '$1')

  return html
}

/**
 * 将 HTML 转换为 Markdown（保存时使用）
 */
export function htmlToMarkdown(html: string): string {
  if (!html) return ''

  console.debug('htmlToMarkdown input:', html.substring(0, 200))

  let markdown = html

  // 标题
  markdown = markdown.replace(/<h1>(.*?)<\/h1>/gi, '# $1\n\n')
  markdown = markdown.replace(/<h2>(.*?)<\/h2>/gi, '## $1\n\n')
  markdown = markdown.replace(/<h3>(.*?)<\/h3>/gi, '### $1\n\n')
  markdown = markdown.replace(/<h4>(.*?)<\/h4>/gi, '#### $1\n\n')
  markdown = markdown.replace(/<h5>(.*?)<\/h5>/gi, '##### $1\n\n')
  markdown = markdown.replace(/<h6>(.*?)<\/h6>/gi, '###### $1\n\n')

  // 加粗和斜体
  markdown = markdown.replace(/<strong><em>(.*?)<\/em><\/strong>/gi, '***$1***')
  markdown = markdown.replace(/<em><strong>(.*?)<\/strong><\/em>/gi, '***$1***')
  markdown = markdown.replace(/<strong>(.*?)<\/strong>/gi, '**$1**')
  markdown = markdown.replace(/<b>(.*?)<\/b>/gi, '**$1**')
  markdown = markdown.replace(/<em>(.*?)<\/em>/gi, '*$1*')
  markdown = markdown.replace(/<i>(.*?)<\/i>/gi, '*$1*')

  // 行内代码
  markdown = markdown.replace(/<code>(.*?)<\/code>/gi, '`$1`')

  // 链接
  markdown = markdown.replace(/<a\s+href="([^"]+)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)')

  // 图片
  markdown = markdown.replace(/<img\s+src="([^"]+)"\s+alt="([^"]*)"[^>]*>/gi, '![$2]($1)')

  // 列表
  markdown = markdown.replace(/<ul[^>]*>(.*?)<\/ul>/gis, (match, content) => {
    const items = content.match(/<li[^>]*>(.*?)<\/li>/gis)
    if (items) {
      return (
        items.map((item: string) => `* ${item.replace(/<\/?li[^>]*>/gi, '').trim()}`).join('\n') +
        '\n\n'
      )
    }
    return match
  })

  markdown = markdown.replace(/<ol[^>]*>(.*?)<\/ol>/gis, (match, content) => {
    const items = content.match(/<li[^>]*>(.*?)<\/li>/gis)
    if (items) {
      return (
        items
          .map(
            (item: string, index: number) =>
              `${index + 1}. ${item.replace(/<\/?li[^>]*>/gi, '').trim()}`
          )
          .join('\n') + '\n\n'
      )
    }
    return match
  })

  // 引用
  markdown = markdown.replace(/<blockquote[^>]*>(.*?)<\/blockquote>/gis, (_match, content) => {
    const lines = content.replace(/<\/?p[^>]*>/gi, '').split('\n')
    return lines.map((line: string) => `> ${line.trim()}`).join('\n') + '\n\n'
  })

  // 水平线
  markdown = markdown.replace(/<hr\s*\/?>/gi, '---\n\n')

  // 段落
  markdown = markdown.replace(/<p[^>]*>(.*?)<\/p>/gis, '$1\n\n')

  // 换行
  markdown = markdown.replace(/<br\s*\/?>/gi, '\n')

  // 清理 HTML 标签（但保留文本内容和空格）
  markdown = markdown.replace(/<[^>]+>/g, '')

  // 解码 HTML 实体（保留特殊空格）
  markdown = markdown.replace(/&nbsp;/g, ' ')
  markdown = markdown.replace(/&lt;/g, '<')
  markdown = markdown.replace(/&gt;/g, '>')
  markdown = markdown.replace(/&amp;/g, '&')
  markdown = markdown.replace(/&quot;/g, '"')

  // 清理多余空行
  markdown = markdown.replace(/\n{3,}/g, '\n\n')

  // 清理首尾空白
  markdown = markdown.trim()

  console.debug('htmlToMarkdown output:', markdown.substring(0, 200))

  return markdown
}
