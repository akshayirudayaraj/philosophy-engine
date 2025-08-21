import MarkdownRenderer from "./markdown_renderer";

export interface DocumentProps {
  link: string,
  title: string,
  header_tree: string,
  original_rank: number,
  text: string,
}

function RelatedDocument({ link, title, header_tree, original_rank, text }: DocumentProps) {
  return (
    <>
      <h2>
        <a href={link}>
          {title}
        </a>
      </h2>
      <h3>headers: {header_tree}</h3>
      {/* <h3>original pinecone rank (based on dense embedding sim score): {original_rank}</h3> */}
      <MarkdownRenderer>
        {text}
      </MarkdownRenderer>
      <br/>
    </>
  )
}

export default RelatedDocument;