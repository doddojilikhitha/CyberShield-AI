import React from 'react';

// Simple markdown formatter
function formatMarkdown(text: string) {
  let html = text;
  
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold mt-4 mb-2 text-primary">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-5 mb-3 text-primary border-b border-border pb-1">$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-6 mb-4 text-primary">$1</h1>');
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Code blocks
  html = html.replace(/```([\s\S]*?)```/g, '<pre class="bg-muted p-3 rounded-md my-3 overflow-x-auto text-sm font-mono border border-border border-l-4 border-l-primary"><code>$1</code></pre>');
  
  // Inline code
  html = html.replace(/`(.*?)`/g, '<code class="bg-muted px-1.5 py-0.5 rounded text-primary text-sm font-mono">$1</code>');
  
  // Lists
  html = html.replace(/^\s*\n\*/gm, '<ul>\n*');
  html = html.replace(/^(\* .*)\n([^\*])/gm, '$1\n</ul>\n$2');
  html = html.replace(/^\* (.*$)/gim, '<li class="ml-5 list-disc mb-1">$1</li>');
  
  html = html.replace(/^\s*\n-/gm, '<ul>\n-');
  html = html.replace(/^(- .*)\n([^-])/gm, '$1\n</ul>\n$2');
  html = html.replace(/^- (.*$)/gim, '<li class="ml-5 list-disc mb-1">$1</li>');
  
  // Paragraphs
  html = html.replace(/^\s*(\n)?(.+)/gim, function(m, p1, p2) {
    if (/<(\/)?(h1|h2|h3|ul|li|pre|code|strong)/.test(p2)) return m;
    return '<p class="mb-3 text-muted-foreground leading-relaxed">' + p2 + '</p>';
  });

  return html;
}

export default function MarkdownRenderer({ content, className = "" }: { content: string, className?: string }) {
  if (!content) return null;
  
  const html = formatMarkdown(content);
  
  return (
    <div 
      className={`prose prose-invert max-w-none ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
