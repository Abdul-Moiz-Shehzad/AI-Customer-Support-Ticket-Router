import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();

  return (
    <div>
      <div className="header">
        <img src="asda" alt="Home" onClick={() => navigate("/")} />
        <h1>Dashboard Page</h1>
      </div>
      <div className="content">
        <p>This is the dashboard page.</p>
      </div>
      <div className="footer">
        <p>AI Customer Support Ticket Router</p>
      </div>
    </div>
  )
}

export default Dashboard;