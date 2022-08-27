import Head from 'next/head'
import Image from 'next/image'
import styles from '../styles/Home.module.css'
import * as React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ChakraProvider } from '@chakra-ui/react'
import App from "./_app";
import Entry from "./entry"
// const root = ReactDOM.createRoot(
//   document.getElementById("root")
// );
function Reharm (){
  return (
    <div>
      <Entry/>
    </div>
  )
}
// root.render(
//   <React.StrictMode>
//     <BrowserRouter>
//       <ChakraProvider>
//         <App />
//       </ChakraProvider>
//     </BrowserRouter>
//   </React.StrictMode>
// );
export default Reharm