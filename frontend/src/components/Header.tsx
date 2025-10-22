import React from "react";
import {
    Box,
    Flex,
    HStack,
    VStack,
    Button,
    Icon,
    Text,
    Avatar,
    Menu,
    MenuButton,
    MenuList,
    MenuItem,
    useColorModeValue,
    useColorMode,
    Badge,
} from "@chakra-ui/react";
import {
    FiSun,
    FiMoon,
    FiUser,
    FiSettings,
    FiChevronDown,
    FiBell,
    FiMenu,
} from "react-icons/fi";

export function Header() {
    const bgColor = useColorModeValue("white", "gray.800");
    const borderColor = useColorModeValue("gray.200", "gray.700");
    const textColor = useColorModeValue("gray.600", "gray.300");
    const { colorMode, toggleColorMode } = useColorMode();

    const navLinks = [
        { label: "Dashboard", href: "#dashboard" },
        { label: "Tools", href: "#tools" },
        { label: "Analytics", href: "#analytics" },
        { label: "Support", href: "#support" },
    ];

    return (
        <Box
            bg={bgColor}
            borderBottom="1px"
            borderColor={borderColor}
            px={6}
            py={4}
            position="sticky"
            top={0}
            zIndex={100}
            boxShadow="sm"
        >
            <Flex justify="space-between" align="center">
                {/* Left Side - Logo and Navigation */}
                <HStack spacing={8}>
                    {/* Logo */}
                    <HStack spacing={3}>
                        <Box
                            w="40px"
                            h="40px"
                            bgGradient="linear(to-br, brand.500, purple.500)"
                            borderRadius="lg"
                            display="flex"
                            alignItems="center"
                            justifyContent="center"
                        >
                            <Icon as={FiUser} boxSize={6} color="white" />
                        </Box>
                        <VStack align="start" spacing={0}>
                            <Text fontSize="lg" fontWeight="bold" color="gray.800">
                                AI Career Elevate
                            </Text>
                            <Text fontSize="xs" color={textColor}>
                                Powered by AI
                            </Text>
                        </VStack>
                    </HStack>

                    {/* Navigation Links */}
                    <HStack spacing={6} display={{ base: "none", md: "flex" }}>
                        {navLinks.map((link) => (
                            <Button
                                key={link.label}
                                variant="ghost"
                                size="sm"
                                color={textColor}
                                _hover={{ color: "brand.500", bg: "brand.50" }}
                                fontWeight="medium"
                            >
                                {link.label}
                            </Button>
                        ))}
                    </HStack>
                </HStack>

                {/* Right Side - Actions and Profile */}
                <HStack spacing={4}>
                    {/* Notifications */}
                    <Button variant="ghost" size="sm" position="relative">
                        <Icon as={FiBell} boxSize={5} color={textColor} />
                        <Badge
                            position="absolute"
                            top="-1"
                            right="-1"
                            colorScheme="red"
                            borderRadius="full"
                            fontSize="xs"
                            w="18px"
                            h="18px"
                            display="flex"
                            alignItems="center"
                            justifyContent="center"
                        >
                            3
                        </Badge>
                    </Button>

                    {/* Theme Toggle */}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={toggleColorMode}
                        color={textColor}
                        _hover={{ color: "brand.500", bg: "brand.50" }}
                    >
                        <Icon as={colorMode === "light" ? FiMoon : FiSun} boxSize={5} />
                    </Button>

                    {/* Settings */}
                    <Button
                        variant="ghost"
                        size="sm"
                        color={textColor}
                        _hover={{ color: "brand.500", bg: "brand.50" }}
                    >
                        <Icon as={FiSettings} boxSize={5} />
                    </Button>

                    {/* Mobile Menu */}
                    <Button
                        variant="ghost"
                        size="sm"
                        display={{ base: "flex", md: "none" }}
                        color={textColor}
                        _hover={{ color: "brand.500", bg: "brand.50" }}
                    >
                        <Icon as={FiMenu} boxSize={5} />
                    </Button>

                    {/* Profile Menu */}
                    <Menu>
                        <MenuButton as={Button} variant="ghost" size="sm">
                            <HStack spacing={3}>
                                <Avatar size="sm" name="John Doe" src="" />
                                <VStack align="start" spacing={0} display={{ base: "none", lg: "flex" }}>
                                    <Text fontSize="sm" fontWeight="medium" color="gray.800">
                                        John Doe
                                    </Text>
                                    <Text fontSize="xs" color={textColor}>
                                        Admin
                                    </Text>
                                </VStack>
                                <Icon as={FiChevronDown} boxSize={4} color={textColor} />
                            </HStack>
                        </MenuButton>
                        <MenuList>
                            <MenuItem icon={<FiUser />}>
                                Profile
                            </MenuItem>
                            <MenuItem icon={<FiSettings />}>
                                Settings
                            </MenuItem>
                            <MenuItem icon={<FiBell />}>
                                Notifications
                            </MenuItem>
                        </MenuList>
                    </Menu>
                </HStack>
            </Flex>
        </Box>
    );
}
