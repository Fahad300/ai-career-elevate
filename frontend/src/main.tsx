import React from "react";
import { createRoot } from "react-dom/client";
import { ChakraProvider } from "@chakra-ui/react";
import { App } from "./App";
import { theme } from "./theme";
import "./styles.css";

const container = document.getElementById("root");
if (!container) {
  throw new Error("Root container not found");
}
const root = createRoot(container);
root.render(
  <ChakraProvider theme={theme}>
    <App />
  </ChakraProvider>
);