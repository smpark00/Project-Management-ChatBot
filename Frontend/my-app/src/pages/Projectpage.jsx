import React, { useState } from "react";
import { useParams } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { Container, Box, Typography, TextField, Button, Paper, CircularProgress } from "@mui/material";

const ProjectPage = () => {
    const { projectName } = useParams();
    const [messages, setMessages] = useState([
        { sender: "bot", text: "프로젝트에 관한 질문을 해주세요!" },
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false); // 로딩 상태 추가

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = { sender: "user", text: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLoading(true); // 응답 대기 상태

        try {
            const response = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: input,
                    project_name: projectName,
                }),
            });

            const data = await response.json();
            const botMessage = { sender: "bot", text: data.response || "오류가 발생했습니다." };

            setMessages((prev) => [...prev, botMessage]);
        } catch (error) {
            setMessages((prev) => [...prev, { sender: "bot", text: "서버 응답에 실패했습니다." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <Header />
            <Container
                sx={{
                    height: "100vh",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    alignItems: "center",
                    py: 2,
                }}
            >
                <Typography variant="h4" align="center" gutterBottom>
                    Project - {projectName}
                </Typography>

                <Paper
                    elevation={3}
                    sx={{
                        flex: 1,
                        width: "100%",
                        maxWidth: "1000px",
                        overflowY: "auto",
                        display: "flex",
                        flexDirection: "column",
                        p: 2,
                        mb: 2,
                        bgcolor: "#f9f9f9",
                    }}
                >
                    {messages.map((message, index) => (
                        <Box
                            key={index}
                            sx={{
                                display: "flex",
                                justifyContent: message.sender === "user" ? "flex-end" : "flex-start",
                                mb: 2,
                            }}
                        >
                            <Box
                                sx={{
                                    maxWidth: "70%",
                                    p: 1.5,
                                    borderRadius: 2,
                                    bgcolor: message.sender === "user" ? "#d1e7ff" : "#e9ecef",
                                    color: "#333",
                                    boxShadow: 1,
                                }}
                            >
                                <Typography variant="body1">{message.text}</Typography>
                            </Box>
                        </Box>
                    ))}
                    {loading && (
                        <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
                            <CircularProgress size={24} />
                        </Box>
                    )}
                </Paper>

                <Box
                    sx={{
                        display: "flex",
                        width: "100%",
                        maxWidth: "1000px",
                        gap: 2,
                        alignItems: "center",
                    }}
                >
                    <TextField
                        fullWidth
                        variant="outlined"
                        placeholder="텍스트를 입력해주세요"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                    />
                    <Button
                        variant="contained"
                        color="primary"
                        onClick={handleSend}
                        disabled={loading} // 로딩 중에는 버튼 비활성화
                    >
                        {loading ? "응답 대기..." : "전송"}
                    </Button>
                </Box>
            </Container>
            <Footer />
        </>
    );
};

export default ProjectPage;
