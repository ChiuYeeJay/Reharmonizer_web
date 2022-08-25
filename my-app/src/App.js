import * as React from "react";
import { Routes, Route, Link } from "react-router-dom";
import Entry from "./entry"
import Result from "./result"

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<Entry />} />
        <Route path="second" element={<Result />} />
      </Routes>
    </div>
  );
}

export default App