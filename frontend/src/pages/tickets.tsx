import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Tickets() {
  const [text, setText] = useState("");
  const navigate = useNavigate();
  function handleSubmit() {
    console.log(text);
    // fetch("http://localhost:5000/process_ticket", {
    //   method: "POST",
    //   headers: {
    //     "Content-Type": "application/json"
    //   },
    //   body: JSON.stringify({
    //     "text": text
    //   })
    // })
    // .then(response => response.json())
    // .then(data => console.log(data))
  }
  return (
    <div>
      <div className="header">
        <img src="asda" alt="Home" onClick={() => navigate("/")} />
      </div>
      <div className="content">
        <input type="text" placeholder="Enter your query here..." onChange={(e) => setText(e.target.value)} />
        <button className="btn" onClick={() => handleSubmit()}>Submit</button>
      </div>
      <div className="footer">
        <p>AI Customer Support Ticket Router</p>
      </div>
    </div>
  )
}

export default Tickets;