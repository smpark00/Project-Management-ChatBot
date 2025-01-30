import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import MainPage from "./pages/main";

const App = () => {
  return (
    <Router>
      <Routes>
        {/* 기본 루트("/")에서 "/main"으로 리디렉트 */}
        <Route path="/" element={<Navigate to="/main" />} />
        <Route path="/main" element={<MainPage />} />
      </Routes>
    </Router>
  );
};

export default App;
