import React from "react";
import { Box } from "@chakra-ui/react";
import { Header } from "./components/Header";
import { HomePage } from "./pages/HomePage";

export function App(): JSX.Element {
  return (
    <Box minH="100vh" bg="gray.50">
      <Header />
      <HomePage />
    </Box>
  );
}