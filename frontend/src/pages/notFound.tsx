import { useNavigate } from "react-router-dom";

function NotFound() {
  const navigate = useNavigate();
  return (
    <div className="app-container" style={{ textAlign: "center", paddingTop: "80px" }}>
      <h1 style={{ fontSize: "5rem", color: "var(--primary-color)", margin: 0 }}>404</h1>
      <h2 style={{ marginBottom: "20px" }}>Page Not Found</h2>
      <p style={{ color: "var(--text-secondary)", marginBottom: "30px" }}>
        The page you are looking for does not exist or has been moved.
      </p>
      <button className="btn" onClick={() => navigate("/")}>
        Go Home
      </button>
    </div>
  );
}

export default NotFound;