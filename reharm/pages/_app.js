import '../styles/globals.css'
import * as React from "react";
import { Routes, Route, Link } from "react-router-dom";
import Entry from "./entry"
import Second from "./second"

function myApp({ Component, pageProps }) {
  return <Component {...pageProps} />
}
export default myApp
