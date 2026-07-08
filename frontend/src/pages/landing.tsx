import { useNavigate } from "react-router-dom";

function Landing() {
  const navigate = useNavigate();
  return (
    <div>
      <div className="header">
        <h1>AI Customer Support Ticket Router</h1>
        <button className="login-btn" onClick={() => navigate("/dashboard")}>Login</button>
      </div>
      <div className="content">
        <h2>Welcome to AI Customer Support Ticket Router</h2>
        <p>This is a web application that helps customers to create and manage their support tickets. It uses AI to analyze customer queries and provide relevant support solutions.</p>
        <button className="btn" onClick={() => navigate("/tickets")}>Get Started</button>
      </div>
      <div className="footer">
        <p>AI Customer Support Ticket Router</p>
      </div>
    </div>
  )
}

export default Landing;