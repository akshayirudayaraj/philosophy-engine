'use client'

import Markdown, { Components } from 'react-markdown';
import remarkGfm from "remark-gfm";
import { useEffect, useState } from 'react';

export default function Home() {
  const [userQuery, setUserQuery] = useState("");
  const [modelOutput, setModelOutput] = useState("");
  const [relatedDocs, setRelatedDocs] = useState([]);
  const [loadingState, setLoadingState] = useState(false);
  const [dots, setDots] = useState(0);

  async function queryBackend() {
    setLoadingState(true);
    try {
      console.log(JSON.stringify({ "user_query": userQuery }));

      const response = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ "user_query": userQuery })
      });

      if (!response.ok) {
        console.log(response.statusText);
      }

      const data = await response.json();

      setModelOutput(data.model_output);
      setRelatedDocs(data.related_documents);
    } catch (error) {
      console.log(error);
    } finally {
      setLoadingState(false);
      setDots(0);
    }
  }
  
  useEffect(() => { // AI code
    let interval: NodeJS.Timeout;
    if (loadingState) {
      interval = setInterval(() => {
        setDots(prev => (prev === 3 ? 0 : prev + 1));
      }, 500); // every half second
    }
    return () => clearInterval(interval); // cleanup
  }, [loadingState]);

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
  `;

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

  // TODO: move into separate MD Renderer component
  const markdownComponents: Components = {
    // headers use global styles
    h1: ({ ...props }) => <h1 {...props} />,
    h2: ({ ...props }) => <h2 {...props} />,
    h3: ({ ...props }) => <h3 {...props} />,
    h4: ({ ...props }) => <h4 {...props} />,
    h5: ({ ...props }) => <h5 {...props} />,
    h6: ({ ...props }) => <h6 {...props} />,
    
    // Text elements use global styles
    p: ({ ...props }) => <p {...props} />,
    ul: ({ ...props }) => <ul {...props} />,
    ol: ({ ...props }) => <ol {...props} />,
    li: ({ ...props }) => <li {...props} />,
    blockquote: ({ ...props }) => <blockquote {...props} />,
    pre: ({ ...props }) => <pre {...props} />,
    a: ({ ...props }) => <a {...props} />,
    strong: ({ ...props }) => <strong {...props} />,
    em: ({ ...props }) => <em {...props} />,
    hr: ({ ...props }) => <hr {...props} />,
    
    // table wrapper for responsive scrolling
    table: ({ ...props }) => (
      <div className="overflow-x-auto">
        <table {...props} />
      </div>
    ),
    
    // table cells use global styles
    th: ({ ...props }) => <th {...props} />,
    td: ({ ...props }) => <td {...props} />,
  }

  return (
    <div className="container mx-auto px-2">
      <div className="flex justify-center pt-4">
        <label className="">
          <input
            name="user_query"
            value={userQuery}
            placeholder="What are you curious about?"
            className="w-150 border border-gray-400 px-0.5 rounded placeholder-gray-400"
            onChange={(e) => setUserQuery(e.target.value)}
          />
          <br/>
        </label>

        <button 
          onClick={() => queryBackend()}
          className="border border-gray-400 px-0.5 rounded cursor-pointer"
        >
          Submit
        </button>
      </div>

      {loadingState &&
        <div className="pt-10 text-center">
          <p>Thinking{".".repeat(dots)}</p>
          <p>Est. time: ~3-5 minutes</p> {/* TODO: actually calculate somehow or do rough time est. */}
        </div>
      }

      <br/>

      {modelOutput && 
        <>
          <Markdown
						components={markdownComponents}
						remarkPlugins={[remarkGfm]}
					>
            {modelOutput}
					</Markdown>
        </>
      }

      {relatedDocs.length > 0 && (
        <> 
          <br/>
          <hr className="border-gray-300"/>
          <br/>
          <h1>Sources</h1>
          {relatedDocs.map((doc: any, index) => ( // [temp] docs is any - FIXME: should enforce type checking
            <div key={index}>
              <h2>
                <a href={doc.link}>
                  {doc.title}
                </a>
                </h2>
              <h3>headers: {doc.header_tree}</h3>
              <h3>original pinecone rank (based on dense embedding sim score): {doc.original_rank}</h3>
              <Markdown
                components={markdownComponents}
                remarkPlugins={[remarkGfm]}
              >
                {doc.text}
              </Markdown>
              <br/>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
