'use client'

import { useEffect, useState } from 'react';

import MarkdownRenderer from './components/markdown_renderer'
import Documents from './components/documents'
import QuestionBar from './components/question_bar'
import { DocumentProps } from './components/related_document';

export default function Home() {
  const [userQuery, setUserQuery] = useState<string>("");

  const [modelOutput, setModelOutput] = useState<string>("");
  const [relatedDocs, setRelatedDocs] = useState<DocumentProps[]>([]);

  const [status, setStatus] = useState<'empty' | 'typing' | 'submitted' | 'result' | 'error' | 'testing'>('empty');
  const [dots, setDots] = useState<number>(0);

  const submitEnabled = status === 'typing' || status === 'result' || status === 'error'

  function handleQuestionChange(newQuestion: string) {
    setUserQuery(newQuestion)

    if (newQuestion.length === 0) {
      setStatus('empty')
    } else {
      setStatus('typing')
    }
  }

  async function queryBackend() {
    setStatus('submitted')

    try {
      console.log(JSON.stringify({ "user_query": userQuery }));

      const response = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ "user_query": userQuery })
      });

      if (!response.ok) {
        setStatus('error')
        console.log(response.statusText);
        return;
      }

      const data = await response.json();

      setModelOutput(data.model_output);
      setRelatedDocs(data.related_documents);

    } catch (error) {
      setStatus('error')
      console.log(error);

    } finally {
      setStatus('result');
      setDots(0);
    }
  }
  
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (status === 'submitted') {
      interval = setInterval(() => {
        setDots(prev => (prev === 3 ? 0 : prev + 1));
      }, 500); // every half second
    }
    return () => clearInterval(interval); // cleanup
  }, [status]);

  function renderContent() {
    switch (status) {
      case 'empty':
        return <></>
      case 'typing':
        return <></>
      case 'submitted':
        return (
          <div className="pt-10 text-center">
            <p>Thinking{".".repeat(dots)}</p>
            <p>Est. time: ~3-5 minutes</p> {/* TODO: actually calculate somehow instead of hard-coding */}
          </div>
        )
      case 'result':
        return (
          <>
            <MarkdownRenderer>
              {modelOutput}
            </MarkdownRenderer>

            {relatedDocs.length > 0 && (
              <Documents documents={relatedDocs}/>
            )}
          </>
        )
      case 'error':
        return (
          <div className="pt-10 text-center">
            <p>Sorry, there's been an error. Please contact me at akshay [dot] irudayaraj [at] gmail [dot] com and try again later!</p>
          </div>
        )
      case 'testing':
        return (
          <>
            <MarkdownRenderer>{testModelOutput}</MarkdownRenderer>
            <Documents documents={testRelatedDocs}/>
          </>
        )
    }
  }

  const testModelOutput = `
  # heading 1
  ## heading 2
  ### heading 3
  #### heading 4
  sample paragraph text. sample paragraph text. sample paragraph text. sample paragraph text. sample paragraph text.
  sample paragraph text. sample paragraph text. sample paragraph text. sample paragraph text. sample paragraph text. 
  ~~strikethrough~~  

  > Blockquote  

  **strong**  
  *italics*  
  ***
  [Gmail](https://gmail.com)  
  ***
  1. ordered list
  2. ordered list
  - unordered list
  - unordered list  
  
  | Syntax      | Description |
  | ----------- | ----------- |
  | Header      | Title       |
  | Paragraph   | Text        |

  graph TD
    A[Start] --> B{Is it raining?};
    B -- Yes --> C[Take an umbrella];
    B -- No --> D[Go outside];
    C --> E[End];
    D --> E;

  This sentence uses delimiters to show math inline: $\sqrt{3x-1}+(1+x)^2$

  Lift($$L$$) can be determined by Lift Coefficient ($$C_L$$) like the following equation.

  $$ L = \frac{1}{2} \rho v^2 S C_L $$
  `; // FIXME: math and mermaid graphs not rendering nicely

  const testRelatedDocs = [
    {
      title: "Introduction to React Hooks",
      header_tree: "Getting Started > React Basics > Hooks",
      link: "https://reactjs.org/docs/hooks-intro.html",
      original_rank: 1,
      text: `sample paragraph text. sample paragraph text. sample paragraph text. sample paragraph text. sample paragraph text.
        sample paragraph text. sample paragraph text. sample paragraph text. sample paragraph text. sample paragraph text.`,
    },
    {
      title: "Advanced State Management",
      header_tree: "Advanced Topics > State > Management Patterns",
      link: "https://reactjs.org/docs/state-management.html",
      original_rank: 2,
      text: `sample text`,
    }
  ]

  return (
    <div className="container mx-auto px-2">
      <div className="flex justify-center pt-4">
        <QuestionBar
          question={userQuery}
          onQuestionChange={handleQuestionChange}
          submitRequest={queryBackend}
          submissionAvailable={submitEnabled}
        />
      </div>

      <br/>

      {renderContent()}
    </div>
  );
}