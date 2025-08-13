'use client'

import ReactMarkdown from 'react-markdown'
import { useState } from 'react'

export default function Home() {
  const [userQuery, setUserQuery] = useState("To what extent, if any, does free will exist?")
  const [modelOutput, setModelOutput] = useState("")
  const [relatedDocs, setRelatedDocs] = useState([])

  async function sendQueryToBackend() {
    try {
      console.log(JSON.stringify({ "user_query": userQuery }))

      const response = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ "user_query": userQuery })
      });

      if (!response.ok) {
        console.log(response.statusText)
      }

      const data = await response.json()

      setModelOutput(data.model_output)
      setRelatedDocs(data.related_documents)
    } catch (error) {
      console.log(error)
    }
  }
    

  return (
    <>
      <label>
        What are you curious about?{' '}
        <input
          name="user_query"
          value={userQuery}
          className="w-150"
          onChange={(e) => setUserQuery(e.target.value)}
        />
        <br/>
      </label>

      <button 
        onClick={() => sendQueryToBackend()}
        className="border border-gray-400 px-0.5 rounded cursor-pointer"
      >
        Submit
      </button>


      {modelOutput && 
        <>
          <ReactMarkdown>{modelOutput}</ReactMarkdown>
        </>
      }

      {relatedDocs && (
        <>
          <p>related docs: </p>

          {relatedDocs.map((doc: any, index) => ( // [temp] docs is any - FIXME: should enforce type checking
            <div key={index}>
              <p>title: {doc.title}, link: {doc.link}</p>
              <p>headers: {doc.header_tree}</p>
              <p>original pinecone rank (based on dense embedding sim score): {doc.original_rank}</p>
              <ReactMarkdown>{doc.text}</ReactMarkdown>
            </div>
          ))}
        </>
      )}
    </>
  );
}
