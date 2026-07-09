import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Tickets() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [subscription, setSubscription] = useState("Free");
  const [message, setMessage] = useState("");

  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [ticketResult, setTicketResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !message) {
      setError("Please fill in all fields.");
      return;
    }

    setLoading(true);
    setStatus("Submitting ticket...");
    setError(null);
    setTicketResult(null);

    try {
      const response = await fetch("http://localhost:8000/classify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          customer_name: name,
          customer_email: email,
          subscription: subscription,
          message: message,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to submit ticket");
      }

      const data = await response.json();
      const ticketId = data.ticket_id;
      setStatus("Ticket queued. Processing query...");
      pollTicketStatus(ticketId, 2000);
    } catch (err: any) {
      setError(err.message || "Something went wrong during submission.");
      setLoading(false);
      setStatus(null);
    }
  };

  const pollTicketStatus = (ticketId: string, currentDelay: number = 2000) => {
    setTimeout(async () => {
      try {
        const response = await fetch(`http://localhost:8000/ticket/${ticketId}`);
        if (!response.ok) {
          throw new Error("Failed to fetch ticket status");
        }

        const ticket = await response.json();

        if (ticket.status === "completed") {
          setTicketResult(ticket);
          setLoading(false);
          setStatus(null);
        } else if (ticket.status === "failed") {
          setError("AI processing failed. Ticket sent to fallback queue.");
          setLoading(false);
          setStatus(null);
        } else {
          setStatus("AI is analyzing your ticket... (polling status)");
          const nextDelay = Math.min(currentDelay + 1500, 10000);
          pollTicketStatus(ticketId, nextDelay);
        }
      } catch (err) {
        console.error("Polling error:", err);
        pollTicketStatus(ticketId, currentDelay);
      }
    }, currentDelay);
  };

  return (
    <div className="app-container">
      <div className="header">
        <div className="header-logo" onClick={() => navigate("/")}>
          <span>AI Ticket Router</span>
        </div>
        <button className="btn btn-secondary" onClick={() => navigate("/")}>
          Home
        </button>
      </div>

      <div className="content">
        <div className="card">
          <h2>Submit Support Ticket</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Name</label>
              <input
                type="text"
                className="form-control"
                placeholder="Your Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                className="form-control"
                placeholder="your.email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>Subscription Tier</label>
              <select
                className="form-control"
                value={subscription}
                onChange={(e) => setSubscription(e.target.value)}
                disabled={loading}
              >
                <option value="Free">Free</option>
                <option value="Starter">Starter</option>
                <option value="Pro">Pro</option>
                <option value="Enterprise">Enterprise</option>
              </select>
            </div>
            <div className="form-group">
              <label>How can we help?</label>
              <textarea
                className="form-control"
                placeholder="Explain your issue in detail..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                disabled={loading}
              />
            </div>

            {error && <div style={{ color: "var(--danger-color)", marginBottom: "15px", fontWeight: 500 }}>{error}</div>}
            {status && (
              <div style={{ marginBottom: "15px" }}>
                <div className="spinner"></div>
                <div style={{ textAlign: "center", color: "var(--text-secondary)", fontWeight: 500 }}>{status}</div>
              </div>
            )}

            <button type="submit" className="btn" style={{ width: "100%" }} disabled={loading}>
              {loading ? "Processing..." : "Submit Ticket"}
            </button>
          </form>

          {ticketResult && (
            <div className="result-box">
              <h3>AI Processing Results</h3>
              <div className="result-grid">
                <div className="result-item">
                  <div className="result-label">Ticket ID</div>
                  <div className="result-value" style={{ fontSize: "0.85rem", wordBreak: "break-all" }}>{ticketResult.ticket_id}</div>
                </div>
                <div className="result-item">
                  <div className="result-label">Status</div>
                  <div className="result-value">
                    <span className="badge badge-completed">{ticketResult.status}</span>
                  </div>
                </div>
                <div className="result-item">
                  <div className="result-label">Category</div>
                  <div className="result-value">{ticketResult.category || "Unassigned"}</div>
                </div>
                <div className="result-item">
                  <div className="result-label">Priority</div>
                  <div className="result-value">
                    <span className={`badge badge-${(ticketResult.priority || "low").toLowerCase()}`}>
                      {ticketResult.priority || "Low"}
                    </span>
                  </div>
                </div>
                <div className="result-item">
                  <div className="result-label">Department</div>
                  <div className="result-value">{ticketResult.department || "General"}</div>
                </div>
                <div className="result-item">
                  <div className="result-label">Escalation</div>
                  <div className="result-value">
                    {ticketResult.escalation_required ? "Human Needed" : "Auto-Resolved"}
                  </div>
                </div>
              </div>

              {ticketResult.reply_message && (
                <div>
                  <div className="result-label">Draft Reply Message</div>
                  <div className="reply-draft">{ticketResult.reply_message}</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="footer">
        <p>&copy; {new Date().getFullYear()} TechEase Cloud. All rights reserved.</p>
      </div>
    </div>
  );
}

export default Tickets;