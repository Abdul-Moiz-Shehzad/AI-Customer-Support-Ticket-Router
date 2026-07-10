import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<any | null>(null);

  const fetchTickets = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8000/tickets");
      if (!response.ok) {
        throw new Error("Failed to fetch tickets");
      }
      const data = await response.json();
      setTickets(data);
    } catch (err: any) {
      setError(err.message || "Could not retrieve tickets.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const total = tickets.length;
  const completed = tickets.filter((t) => t.status === "completed").length;
  const pending = tickets.filter((t) => t.status === "pending").length;
  const failed = tickets.filter((t) => t.status === "failed").length;
  const cacheHits = tickets.filter((t) => t.cache_hit === true).length;

  return (
    <div className="app-container">
      <div className="header">
        <div className="header-logo" onClick={() => navigate("/")}>
          <span>AI Ticket Router</span>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button className="btn btn-secondary" onClick={fetchTickets} disabled={loading}>
            Refresh
          </button>
          <button className="btn" onClick={() => navigate("/")}>
            Home
          </button>
        </div>
      </div>

      <div className="content">
        <h2>Support Triage Dashboard</h2>

        <div className="stats-row">
          <div className="stat-card">
            <div className="value">{total}</div>
            <div className="label">Total Tickets</div>
          </div>
          <div className="stat-card">
            <div className="value" style={{ color: "var(--success-color)" }}>{completed}</div>
            <div className="label">Completed</div>
          </div>
          <div className="stat-card">
            <div className="value" style={{ color: "#a855f7" }}>{cacheHits}</div>
            <div className="label">Cache Hits</div>
          </div>
          <div className="stat-card">
            <div className="value" style={{ color: "var(--pending-color)" }}>{pending}</div>
            <div className="label">Pending</div>
          </div>
          <div className="stat-card">
            <div className="value" style={{ color: "var(--danger-color)" }}>{failed}</div>
            <div className="label">Failed</div>
          </div>
        </div>

        {error && (
          <div style={{ color: "var(--danger-color)", margin: "20px 0", fontWeight: 500 }}>
            Error: {error}
          </div>
        )}

        {loading ? (
          <div>
            <div className="spinner"></div>
            <div style={{ textAlign: "center", color: "var(--text-secondary)" }}>Loading tickets...</div>
          </div>
        ) : tickets.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)" }}>
            No tickets found. Submit a ticket from the homepage to see it here!
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Subscription</th>
                  <th>Status</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Escalation</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr
                    key={ticket.ticket_id}
                    className="interactive-row"
                    onClick={() => setSelectedTicket(ticket)}
                  >
                    <td>
                      <div style={{ fontWeight: 600 }}>{ticket.customer_name}</div>
                      <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                        {ticket.customer_email}
                      </div>
                    </td>
                    <td>{ticket.subscription}</td>
                    <td>
                      <span className={`badge badge-${ticket.status}`}>
                        {ticket.status}
                      </span>
                      {ticket.cache_hit && (
                        <span className="badge badge-cached" style={{ marginLeft: "8px" }}>
                          Cached
                        </span>
                      )}
                    </td>
                    <td>{ticket.category || "—"}</td>
                    <td>
                      {ticket.priority ? (
                        <span className={`badge badge-${ticket.priority.toLowerCase()}`}>
                          {ticket.priority}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>
                      {ticket.status === "completed" ? (
                        ticket.escalation_required ? (
                          <span style={{ color: "var(--danger-color)", fontWeight: 500 }}>Human</span>
                        ) : (
                          <span style={{ color: "var(--success-color)", fontWeight: 500 }}>Auto-Reply</span>
                        )
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedTicket && (
        <div className="modal-overlay" onClick={() => setSelectedTicket(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedTicket(null)}>
              &times;
            </button>
            <h3>Ticket Details</h3>
            
            <div className="result-grid" style={{ marginTop: "20px" }}>
              <div className="result-item">
                <div className="result-label">Ticket ID</div>
                <div className="result-value" style={{ fontSize: "0.85rem", wordBreak: "break-all" }}>
                  {selectedTicket.ticket_id}
                </div>
              </div>
              <div className="result-item">
                <div className="result-label">Date Submitted</div>
                <div className="result-value">
                  {selectedTicket.created_at
                    ? new Date(selectedTicket.created_at).toLocaleString()
                    : "Unknown"}
                </div>
              </div>
              <div className="result-item">
                <div className="result-label">Customer Name</div>
                <div className="result-value">{selectedTicket.customer_name}</div>
              </div>
              <div className="result-item">
                <div className="result-label">Customer Email</div>
                <div className="result-value">{selectedTicket.customer_email}</div>
              </div>
              <div className="result-item">
                <div className="result-label">Subscription Tier</div>
                <div className="result-value">{selectedTicket.subscription}</div>
              </div>
              <div className="result-item">
                <div className="result-label">Processing Status</div>
                <div className="result-value">
                  <span className={`badge badge-${selectedTicket.status}`}>{selectedTicket.status}</span>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <div className="result-label">Original Customer Message</div>
              <div className="reply-draft" style={{ backgroundColor: "rgba(0,0,0,0.02)" }}>
                {selectedTicket.message}
              </div>
            </div>

            {selectedTicket.status === "completed" && (
              <>
                <h4 style={{ borderTop: "1px solid var(--border-color)", paddingTop: "20px", marginTop: "20px" }}>
                  AI Analysis & Routing
                </h4>
                <div className="result-grid">
                  <div className="result-item">
                    <div className="result-label">Category</div>
                    <div className="result-value">{selectedTicket.category || "Unassigned"}</div>
                  </div>
                  <div className="result-item">
                    <div className="result-label">Priority</div>
                    <div className="result-value">
                      <span className={`badge badge-${(selectedTicket.priority || "low").toLowerCase()}`}>
                        {selectedTicket.priority || "Low"}
                      </span>
                    </div>
                  </div>
                  <div className="result-item">
                    <div className="result-label">Assigned Department</div>
                    <div className="result-value">{selectedTicket.department || "General"}</div>
                  </div>
                  <div className="result-item">
                    <div className="result-label">Escalation Status</div>
                    <div className="result-value">
                      {selectedTicket.escalation_required ? "Human Intervention Required" : "AI Handled"}
                    </div>
                  </div>
                  <div className="result-item">
                    <div className="result-label">Resolution Mode</div>
                    <div className="result-value">
                      {selectedTicket.cache_hit ? (
                        <span className="badge badge-cached">Semantic Cache Hit</span>
                      ) : (
                        <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>LLM LangGraph</span>
                      )}
                    </div>
                  </div>
                </div>

                {selectedTicket.reply_message && (
                  <div style={{ marginTop: "15px" }}>
                    <div className="result-label">Drafted Auto-Reply</div>
                    <div className="reply-draft">{selectedTicket.reply_message}</div>
                  </div>
                )}
              </>
            )}

            {selectedTicket.status === "failed" && (
              <div className="result-box" style={{ borderColor: "var(--danger-color)", backgroundColor: "rgba(239, 68, 68, 0.05)" }}>
                <h3 style={{ color: "var(--danger-color)" }}>Processing Failure</h3>
                <p style={{ margin: 0, fontSize: "0.95rem" }}>
                  This ticket failed during classification or queueing and is marked for manual triage fallback.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="footer">
        <p>&copy; {new Date().getFullYear()} TechEase Cloud. All rights reserved.</p>
      </div>
    </div>
  );
}

export default Dashboard;