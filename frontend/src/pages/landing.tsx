import { useNavigate } from "react-router-dom";

function Landing() {
  const navigate = useNavigate();
  return (
    <div className="app-container">
      <div className="header">
        <div className="header-logo" onClick={() => navigate("/")}>
          <span>AI Ticket Router</span>
        </div>
        <button className="btn btn-secondary" onClick={() => navigate("/dashboard")}>
          Staff Dashboard
        </button>
      </div>

      <div className="content">
        <div className="hero-section">
          <h2>Smart Customer Support Triage</h2>
          <p>
            Submit your customer support queries and get instant answers powered by AI. 
            Our intelligent router automatically categorizes, prioritizes, and resolves issues.
          </p>
          <div className="hero-buttons">
            <button className="btn" onClick={() => navigate("/tickets")}>
              Submit a Ticket
            </button>
            <button className="btn btn-secondary" onClick={() => navigate("/dashboard")}>
              View Dashboard
            </button>
          </div>
        </div>
      </div>

      <div className="footer">
        <p>&copy; {new Date().getFullYear()} TechEase Cloud. All rights reserved.</p>
      </div>
    </div>
  );
}

export default Landing;