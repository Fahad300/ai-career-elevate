import React from "react";
import {
    Box,
    Flex,
    Heading,
    Button,
    HStack,
    VStack,
    Icon,
    useColorModeValue,
} from "@chakra-ui/react";
import { FiMenu, FiUser, FiBell, FiSettings } from "react-icons/fi";

interface NavigationProps {
    onNavigate: (page: string) => void;
    currentPage: string;
}

export function Navigation({ onNavigate, currentPage }: NavigationProps) {
    const bgColor = useColorModeValue("white", "gray.800");
    const borderColor = useColorModeValue("gray.200", "gray.700");

    return (
        <Box bg={bgColor} borderBottom="1px" borderColor={borderColor} px={6} py={4}>
            <Flex justify="space-between" align="center">
                <VStack align="start" spacing={0}>
                    <Heading size="lg" color="brand.500" cursor="pointer" onClick={() => onNavigate("welcome")}>
                        🚀 AI Career Elevate
                    </Heading>
                    <HStack spacing={4} mt={2}>
                        <Button
                            variant={currentPage === "welcome" ? "solid" : "ghost"}
                            colorScheme="brand"
                            size="sm"
                            onClick={() => onNavigate("welcome")}
                        >
                            Home
                        </Button>
                        <Button
                            variant={currentPage === "tools" ? "solid" : "ghost"}
                            colorScheme="brand"
                            size="sm"
                            onClick={() => onNavigate("tools")}
                        >
                            Tools
                        </Button>
                        <Button
                            variant={currentPage === "dashboard" ? "solid" : "ghost"}
                            colorScheme="brand"
                            size="sm"
                            onClick={() => onNavigate("dashboard")}
                        >
                            Dashboard
                        </Button>
                    </HStack>
                </VStack>

                <HStack spacing={4}>
                    <Button variant="ghost" size="sm">
                        <Icon as={FiBell} />
                    </Button>
                    <Button variant="ghost" size="sm">
                        <Icon as={FiSettings} />
                    </Button>
                    <Button colorScheme="brand" size="sm" leftIcon={<FiUser />}>
                        Profile
                    </Button>
                </HStack>
            </Flex>
        </Box>
    );
}
