import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/landing";
import Tickets from "./pages/tickets";
import Dashboard from "./pages/dashboard";
import NotFound from "./pages/notFound";

function Main_app() {
  return (
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
      <Main_app />
    </BrowserRouter>
  )
}

export default App;
