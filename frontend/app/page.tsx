'use client'

import Markdown from 'react-markdown';
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
          <p>Est time: ~3-5 minutes</p> {/* TODO: actually calculate somehow or do rough time est. */}
        </div>
      }

      <br/>

      {modelOutput && 
        <>
          <Markdown
						components={{
							a: ({ ...props }) => <a className="text-link" {...props} />,
							p: ({ ...props }) => <p className="pl-5 indent-8" {...props} />,
						}}
						remarkPlugins={[remarkGfm]}
					>
            {modelOutput}
					</Markdown>
        </>
      }

      {relatedDocs.length > 0 && (
        <>
          <br/>
          <br/>
          <p>retrieved docs: </p>
          <br/>
          {relatedDocs.map((doc: any, index) => ( // [temp] docs is any - FIXME: should enforce type checking
            <div key={index}>
              <p>title: {doc.title}, link: {doc.link}</p>
              <p>headers: {doc.header_tree}</p>
              <p>original pinecone rank (based on dense embedding sim score): {doc.original_rank}</p>
              <Markdown
                components={{
                  a: ({ ...props }) => <a className="text-link" {...props} />,
                  p: ({ ...props }) => <p className="pl-5 indent-8" {...props} />,
                }}
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
