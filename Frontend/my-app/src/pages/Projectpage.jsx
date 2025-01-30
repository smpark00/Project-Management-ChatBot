import React, { useState } from "react";
import { useParams } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { Container, Box, Typography, TextField, Button, Paper } from "@mui/material";

const ProjectPage = () => {
    const { projectName } = useParams(); // URL 파라미터에서 프로젝트 이름 가져오기
    const [messages, setMessages] = useState([
        { sender: "bot", text: "프로젝트에 관한 질문을 해주세요!" },
    ]); // 채팅 메시지 목록
    const [input, setInput] = useState(""); // 입력값

    // 채팅 메시지 추가 함수
    const handleSend = () => {
        if (input.trim()) {
            setMessages([...messages, { sender: "user", text: input }]);
            setInput(""); // 입력 필드 초기화

            // 챗봇 응답 추가 (예제용)
            setTimeout(() => {
                setMessages((prev) => [
                    ...prev,
                    { sender: "bot", text: `${input}에 대한 답변을 준비 중입니다.` },
                ]);
            }, 1000);
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
                {/* 제목 */}
                <Typography variant="h4" align="center" gutterBottom>
                    Project - {projectName}
                </Typography>

                {/* 채팅 영역 */}
                <Paper
                    elevation={3}
                    sx={{
                        flex: 1,
                        width: "100%",
                        maxWidth: "1000px", // 가로 길이를 더 넓게 조정
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
                </Paper>

                {/* 입력 영역 */}
                <Box
                    sx={{
                        display: "flex",
                        width: "100%",
                        maxWidth: "1000px", // 입력 영역도 동일한 너비로 조정
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
                        sx={{ flexShrink: 0 }}
                    >
                        전송
                    </Button>
                </Box>
            </Container>
            <Footer />
        </>
    );
};

export default ProjectPage;