import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/landing";
import Tickets from "./pages/tickets";
import Dashboard from "./pages/dashboard";
import NotFound from "./pages/notFound";

function MainApp() {
  return (
    document.title = "TechEase Cloud Support Ticket Router",
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/tickets" element={<Tickets />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <MainApp />
    </BrowserRouter>
  )
}


export default App;
