import RelatedDocument, { DocumentProps } from './related_document'

interface DocListProps {
  documents: DocumentProps[],
}

function Documents({ documents }: DocListProps) {

  return (
    <> 
      <br/>
      <hr className="border-gray-300"/>
      <br/>
      <h1>Sources</h1>
      {documents.map((doc: DocumentProps, index: number) => (
        <div key={index}>
          <RelatedDocument
            {...doc}
          />
        </div>
      ))}
    </>
  );
}

export default Documents;