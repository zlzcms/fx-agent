/**
 * Markdown 处理工具函数
 */

/**
 * 处理Markdown内容中的转义字符
 * @param content - 原始Markdown内容
 * @returns 处理后的Markdown内容
 */
export function processMarkdownContent(content: string): string {
  if (!content) return '';

  let processedContent = content.replaceAll(String.raw`\n`, '\n');

  processedContent = processedContent.replaceAll(String.raw`\t`, '\t');

  processedContent = processedContent.replaceAll(String.raw`\"`, '"');
  processedContent = processedContent.replaceAll(String.raw`\'`, "'");

  processedContent = processedContent.replaceAll('\\\\', '\\');

  return processedContent;
}

/**
 * 渲染Markdown内容（处理转义字符）
 * @param content - 原始Markdown内容
 * @returns 处理后的Markdown内容
 */
export function renderMarkdown(content: string): string {
  if (!content) {
    return '';
  }
  return processMarkdownContent(content);
}
