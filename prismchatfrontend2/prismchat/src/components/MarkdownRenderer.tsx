"use client";

import { FC } from "react";
import { marked } from "marked";
import DOMPurify from "dompurify";

// Configure once per module
marked.setOptions({
  gfm: true,
  breaks: true, // respect single newlines
  async: false, // ensure marked.parse returns string
});

const MarkdownRenderer: FC<{ content: string }> = ({ content }) => {
  const normalized = (content ?? "").replace(/\\n/g, "\n");
  const html = marked.parse(normalized) as string;
  const safe = DOMPurify.sanitize(html);

  return (
    <div
      className="prose prose-invert prose-sm md:prose-base max-w-none whitespace-pre-wrap leading-relaxed"
      dangerouslySetInnerHTML={{ __html: safe }}
    />
  );
};

export default MarkdownRenderer;
