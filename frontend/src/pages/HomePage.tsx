import React, { useState, useMemo, useRef } from "react";
import {
    Box,
    Container,
    Heading,
    Text,
    Button,
    VStack,
    HStack,
    Grid,
    GridItem,
    Card,
    CardBody,
    Icon,
    Badge,
    Flex,
    useColorModeValue,
    Input,
    InputGroup,
    InputLeftElement,
    Stack,
    InputRightElement,
    Alert,
    AlertIcon,
    AlertTitle,
    AlertDescription,
    Progress,
    useToast,
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalFooter,
    ModalBody,
    ModalCloseButton,
    useDisclosure,
} from "@chakra-ui/react";
import {
    FiUsers,
    FiFileText,
    FiSearch,
    FiEdit,
    FiMessageSquare,
    FiMonitor,
    FiCpu,
    FiArrowRight,
    FiCheckCircle,
    FiPhone,
    FiX,
    FiUpload,
    FiFile,
} from "react-icons/fi";

export function HomePage() {
    const textColor = useColorModeValue("gray.600", "gray.300");
    const [searchQuery, setSearchQuery] = useState("");
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [uploadResult, setUploadResult] = useState<any>(null);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const toast = useToast();
    const { isOpen, onOpen, onClose } = useDisclosure();

    const tools = [
        {
            id: "resume-analyzer",
            title: "Resume Analyzer",
            subtitle: "ATS Score + Fixes",
            icon: FiFileText,
            color: "blue",
        },
        {
            id: "jd-matcher",
            title: "JD Matcher",
            subtitle: "Similarity & Keywords",
            icon: FiSearch,
            color: "green",
        },
        {
            id: "cover-letter",
            title: "Cover Letter",
            subtitle: "Role-Tailored Generation",
            icon: FiEdit,
            color: "purple",
        },
        {
            id: "skill-gap",
            title: "Skill Gap",
            subtitle: "Learning Path",
            icon: FiUsers,
            color: "orange",
        },
        {
            id: "interview-prep",
            title: "Interview Prep",
            subtitle: "Auto Q&A Generation",
            icon: FiMessageSquare,
            color: "teal",
        },
        {
            id: "portfolio",
            title: "Portfolio",
            subtitle: "UX/UI Feedback",
            icon: FiMonitor,
            color: "pink",
        },
    ];

    // Filter tools based on search query
    const filteredTools = useMemo(() => {
        if (!searchQuery.trim()) return tools;

        return tools.filter(tool =>
            tool.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            tool.subtitle.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }, [searchQuery, tools]);

    // File upload functions
    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Validate file type
            const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
            if (!allowedTypes.includes(file.type)) {
                toast({
                    title: "Invalid file type",
                    description: "Please upload a PDF or DOCX file.",
                    status: "error",
                    duration: 5000,
                    isClosable: true,
                });
                return;
            }

            // Validate file size (10MB)
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {
                toast({
                    title: "File too large",
                    description: "Please upload a file smaller than 10MB.",
                    status: "error",
                    duration: 5000,
                    isClosable: true,
                });
                return;
            }

            setUploadFile(file);
            setUploadError(null);
            setUploadResult(null);
        }
    };

    const handleUpload = async () => {
        if (!uploadFile) return;

        setIsUploading(true);
        setUploadProgress(0);
        setUploadError(null);
        setUploadResult(null);

        try {
            const formData = new FormData();
            formData.append('file', uploadFile);

            const response = await fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                setUploadResult(result);
                toast({
                    title: "Upload successful!",
                    description: `File uploaded with session ID: ${result.session_id}`,
                    status: "success",
                    duration: 5000,
                    isClosable: true,
                });
            } else {
                throw new Error(result.detail || 'Upload failed');
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Upload failed';
            setUploadError(errorMessage);
            toast({
                title: "Upload failed",
                description: errorMessage,
                status: "error",
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsUploading(false);
            setUploadProgress(0);
        }
    };

    const clearUpload = () => {
        setUploadFile(null);
        setUploadResult(null);
        setUploadError(null);
        setUploadProgress(0);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const openResumeAnalyzer = () => {
        onOpen();
    };

    return (
        <Box bg="gray.50">
            {/* Compact Hero Section */}
            <Box bgGradient="linear(to-br, brand.50, purple.50, pink.50)" py={12}>
                <Container maxW="container.xl">
                    <VStack spacing={6} textAlign="center">
                        <VStack spacing={4}>
                            <Heading size="2xl" color="gray.800" fontWeight="bold">
                                Elevate Your Career with{" "}
                                <Text as="span" bgGradient="linear(to-r, brand.500, purple.500)" bgClip="text">
                                    AI Power
                                </Text>
                            </Heading>
                            <Text fontSize="lg" color="gray.600" maxW="2xl">
                                Transform your job search with our suite of AI-powered tools.
                                Get ATS-optimized resumes, personalized cover letters, and interview preparation.
                            </Text>
                        </VStack>

                        {/* Search Bar */}
                        <Box w="full" maxW="2xl">
                            <InputGroup size="lg">
                                <InputLeftElement pointerEvents="none" h="60px">
                                    <Icon as={FiSearch} color="gray.400" boxSize={6} />
                                </InputLeftElement>
                                <Input
                                    placeholder="Search tools..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    bg="white"
                                    borderRadius="full"
                                    borderColor="gray.200"
                                    h="60px"
                                    fontSize="lg"
                                    _focus={{
                                        borderColor: "brand.500",
                                        boxShadow: "0 0 0 1px var(--chakra-colors-brand-500)",
                                    }}
                                />
                                {searchQuery && (
                                    <InputRightElement h="60px">
                                        <Button
                                            size="md"
                                            variant="ghost"
                                            onClick={() => setSearchQuery("")}
                                            p={0}
                                            minW="auto"
                                            h="auto"
                                            borderRadius="full"
                                        >
                                            <Icon as={FiX} color="gray.400" boxSize={5} />
                                        </Button>
                                    </InputRightElement>
                                )}
                            </InputGroup>
                        </Box>


                        {/* Tools Grid */}
                        {filteredTools.length > 0 ? (
                            <Grid templateColumns={{ base: "repeat(2, 1fr)", md: "repeat(3, 1fr)", lg: "repeat(6, 1fr)" }} gap={6}>
                                {filteredTools.map((tool) => (
                                    <GridItem key={tool.id}>
                                        <VStack spacing={3} align="center">
                                            <Box
                                                w="80px"
                                                h="80px"
                                                bg={`${tool.color}.100`}
                                                borderRadius="full"
                                                display="flex"
                                                alignItems="center"
                                                justifyContent="center"
                                                cursor="pointer"
                                                transition="all 0.3s"
                                                _hover={{
                                                    transform: "translateY(-4px)",
                                                    boxShadow: "lg",
                                                    bg: `${tool.color}.200`,
                                                }}
                                                onClick={() => tool.id === "resume-analyzer" && openResumeAnalyzer()}
                                            >
                                                <Icon as={tool.icon} boxSize={8} color={`${tool.color}.500`} />
                                            </Box>
                                            <VStack spacing={1} textAlign="center">
                                                <Text fontSize="sm" fontWeight="semibold" color="gray.800">
                                                    {tool.title}
                                                </Text>
                                                <Text fontSize="xs" color={textColor}>
                                                    {tool.subtitle}
                                                </Text>
                                            </VStack>
                                        </VStack>
                                    </GridItem>
                                ))}
                            </Grid>
                        ) : (
                            <VStack spacing={4} py={8}>
                                <Icon as={FiSearch} boxSize={12} color="gray.400" />
                                <Text fontSize="lg" color="gray.500">
                                    No tools found for "{searchQuery}"
                                </Text>
                                <Button
                                    variant="ghost"
                                    onClick={() => setSearchQuery("")}
                                    size="sm"
                                >
                                    Clear search
                                </Button>
                            </VStack>
                        )}
                    </VStack>
                </Container>
            </Box>

            {/* Resume Analyzer Modal */}
            <Modal isOpen={isOpen} onClose={onClose} size="xl">
                <ModalOverlay />
                <ModalContent>
                    <ModalHeader>
                        <HStack spacing={3}>
                            <Icon as={FiFileText} color="blue.500" boxSize={6} />
                            <Text>Resume Analyzer - ATS Score + Fixes</Text>
                        </HStack>
                    </ModalHeader>
                    <ModalCloseButton />
                    <ModalBody>
                        <VStack spacing={6}>
                            <Text fontSize="sm" color={textColor} textAlign="center">
                                Upload your resume to get an ATS score and receive AI-powered suggestions for improvement.
                            </Text>

                            <VStack spacing={4} w="full">
                                {/* File Input */}
                                <Box w="full">
                                    <Input
                                        ref={fileInputRef}
                                        type="file"
                                        accept=".pdf,.docx"
                                        onChange={handleFileSelect}
                                        display="none"
                                    />
                                    <Button
                                        onClick={() => fileInputRef.current?.click()}
                                        leftIcon={<Icon as={FiUpload} />}
                                        variant="outline"
                                        w="full"
                                        py={6}
                                        borderStyle="dashed"
                                        borderWidth="2px"
                                        _hover={{ bg: "gray.50" }}
                                    >
                                        {uploadFile ? uploadFile.name : "Choose Resume File"}
                                    </Button>
                                </Box>

                                {/* File Info */}
                                {uploadFile && (
                                    <HStack spacing={4} w="full" justify="space-between">
                                        <HStack spacing={2}>
                                            <Icon as={FiFile} color="blue.500" />
                                            <VStack spacing={0} align="start">
                                                <Text fontSize="sm" fontWeight="medium">
                                                    {uploadFile.name}
                                                </Text>
                                                <Text fontSize="xs" color="gray.500">
                                                    {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                                                </Text>
                                            </VStack>
                                        </HStack>
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={clearUpload}
                                            color="gray.500"
                                        >
                                            <Icon as={FiX} />
                                        </Button>
                                    </HStack>
                                )}

                                {/* Upload Progress */}
                                {isUploading && (
                                    <Box w="full">
                                        <Text fontSize="sm" mb={2}>Analyzing Resume...</Text>
                                        <Progress value={uploadProgress} size="sm" colorScheme="brand" />
                                    </Box>
                                )}

                                {/* Success Result */}
                                {uploadResult && (
                                    <Alert status="success" borderRadius="md" w="full">
                                        <AlertIcon />
                                        <Box>
                                            <AlertTitle>Upload Successful!</AlertTitle>
                                            <AlertDescription fontSize="sm">
                                                Session ID: {uploadResult.session_id}
                                                <br />
                                                File: {uploadResult.filename}
                                                <br />
                                                Size: {(uploadResult.file_size / 1024).toFixed(2)} KB
                                                <br />
                                                <Text fontWeight="bold" mt={2}>
                                                    Your resume is now being analyzed...
                                                </Text>
                                            </AlertDescription>
                                        </Box>
                                    </Alert>
                                )}

                                {/* Error Result */}
                                {uploadError && (
                                    <Alert status="error" borderRadius="md" w="full">
                                        <AlertIcon />
                                        <Box>
                                            <AlertTitle>Upload Failed</AlertTitle>
                                            <AlertDescription fontSize="sm">
                                                {uploadError}
                                            </AlertDescription>
                                        </Box>
                                    </Alert>
                                )}
                            </VStack>
                        </VStack>
                    </ModalBody>
                    <ModalFooter>
                        <HStack spacing={3}>
                            <Button variant="ghost" onClick={onClose}>
                                Close
                            </Button>
                            <Button
                                onClick={handleUpload}
                                colorScheme="blue"
                                isDisabled={!uploadFile || isUploading}
                                isLoading={isUploading}
                                loadingText="Analyzing..."
                            >
                                Analyze Resume
                            </Button>
                        </HStack>
                    </ModalFooter>
                </ModalContent>
            </Modal>
        </Box>
    );
}