// Markdown-it 相关模块声明
declare module 'markdown-it' {
  interface MarkdownIt {
    render(src: string): string;
    use(plugin: any, ...args: any[]): MarkdownIt;
    set(options: any): MarkdownIt;
    utils: {
      escapeHtml(str: string): string;
    };
    renderer: {
      rules: Record<string, any>;
    };
  }
  
  interface MarkdownItConstructor {
    new (options?: any): MarkdownIt;
  }
  
  const MarkdownIt: MarkdownItConstructor;
  export = MarkdownIt;
}

declare module 'highlight.js' {
  interface HighlightResult {
    value: string;
    language?: string;
  }
  
  interface HLJS {
    highlight(code: string, options: { language: string; ignoreIllegals?: boolean }): HighlightResult;
    getLanguage(name: string): any;
  }
  
  const hljs: HLJS;
  export = hljs;
}

declare module 'highlight.js/styles/github-dark.css';