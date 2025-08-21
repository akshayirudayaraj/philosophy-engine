import ReactMarkdown, { Components, MarkdownHooks } from 'react-markdown';
import remarkGfm from "remark-gfm";
import remarkMath from 'remark-math'
import React from 'react';
import rehypeKatex from 'rehype-katex';

interface RendererProps {
  children: string
}

function MarkdownRenderer({ children }: RendererProps) {
  const markdownComponents: Components = {
    h1: (props) => <h1 {...props} />,
    h2: (props) => <h2 {...props} />,
    h3: (props) => <h3 {...props} />,
    h4: (props) => <h4 {...props} />,
    h5: (props) => <h5 {...props} />,
    h6: (props) => <h6 {...props} />,
    
    p: (props) => <p {...props} />,
    ul: (props) => <ul {...props} />,
    ol: (props) => <ol {...props} />,
    li: (props) => <li {...props} />,
    blockquote: (props) => <blockquote {...props} />,
    pre: (props) => <pre {...props} />,
    a: (props) => <a {...props} />,
    strong: (props) => <strong {...props} />,
    em: (props) => <em {...props} />,
    hr: (props) => <hr {...props} />,
    
    table: (props) => (
      <div className="overflow-x-auto">
        <table {...props} />
      </div>
    ),
    
    th: (props) => <th {...props} />,
    td: (props) => <td {...props} />,
  }

  return (
    <ReactMarkdown
      components={markdownComponents}
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex]} // FIXME: katex doesn't work well
    >
      {children}
    </ReactMarkdown>
  )
}

export default MarkdownRenderer;