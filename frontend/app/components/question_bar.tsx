interface QuestionBarProps {
  question: string,
  onQuestionChange: (value: string) => void,
  submitRequest: () => void,
  submissionAvailable: boolean,
}

function QuestionBar({ question, onQuestionChange, submitRequest, submissionAvailable }: QuestionBarProps) {
  return (
    <>
      <label>
        <input
          name="user_query"
          value={question}
          placeholder="What are you curious about?"
          className="w-150 border border-gray-400 px-0.5 rounded placeholder-gray-400"
          onChange={(e) => {
            onQuestionChange(e.target.value)
          }}
        />
        <br/>
      </label>

      <button 
        onClick={() => submitRequest()}
        className={submissionAvailable ? 
          "border border-gray-400 px-0.5 rounded cursor-pointer" :
          "border border-gray-400 px-0.5 rounded cursor-not-allowed bg-gray-400 text-gray-700 opacity-60"}
        disabled={!submissionAvailable}
      >
        Submit
      </button>
    </>
  )
}

export default QuestionBar;