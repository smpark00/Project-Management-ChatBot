import React, { useEffect, useState } from "react";
import {
    Container,
    Box,
    Grid,
    TextField,
    Button,
    Card,
    CardContent,
    CardMedia,
    Typography,
} from "@mui/material";
import CircularProgress from "@mui/material/CircularProgress";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { Link } from "react-router-dom";
import fileimage from "../assets/images/file.png";

function CircularProgressWithLabel({ value }) {
    return (
        <Box sx={{ position: "relative", display: "inline-flex" }}>
            <CircularProgress variant="determinate" value={value} size={80} />
            <Box
                sx={{
                    top: 0,
                    left: 0,
                    bottom: 0,
                    right: 0,
                    position: "absolute",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                }}
            >
                <Typography variant="caption" component="div" sx={{ color: "text.secondary" }}>
                    {`${Math.round(value)}%`}
                </Typography>
            </Box>
        </Box>
    );
}

const MainPage = () => {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [urlInput, setUrlInput] = useState(""); // URL 입력 상태
    const [feedback, setFeedback] = useState(""); // 사용자 피드백 메시지
    const [progress, setProgress] = useState(0); // 진행률 상태
    const [status, setStatus] = useState(""); // 작업 상태 메시지
    const [isProcessing, setIsProcessing] = useState(false); // 작업 진행 여부

    const fetchProjects = async () => {
        try {
            setLoading(true);
            const response = await fetch("http://localhost:8000/projectslist");
            if (!response.ok) {
                throw new Error("Failed to fetch projects");
            }
            const data = await response.json();
            setProjects(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleLoadProject = async () => {
        if (!urlInput.trim()) {
            setFeedback("Please enter a valid URL.");
            return;
        }

        setProgress(0); // 진행률 초기화
        setStatus("Starting process...");
        setIsProcessing(true); // 작업 시작

        const eventSource = new EventSource(`http://localhost:8000/progress?repo_url=${encodeURIComponent(urlInput)}`);

        eventSource.onmessage = (event) => {
            console.log("Received event:", event.data); // 🛠 디버깅: 받은 데이터 콘솔 출력
            try {
                const cleanData = event.data.replace("data: ", "").trim();
                const data = JSON.parse(cleanData);

                if (data.progress !== undefined) {
                    setProgress(data.progress); // 진행률 업데이트
                }
                if (data.status) {
                    setStatus(data.status); // 상태 메시지 업데이트
                }

                if (data.progress >= 100) {
                    eventSource.close();
                    setFeedback("Repository processed successfully!");
                    setIsProcessing(false); // 작업 완료
                    fetchProjects(); // 프로젝트 목록 새로고침
                }
            } catch (error) {
                console.error("Error parsing event data:", error); // 🛠 JSON 파싱 에러 확인
            }
        };

        eventSource.onerror = (error) => {
            console.error("EventSource error:", error); // 🛠 오류 로그
            setStatus("Error: Unable to retrieve progress.");
            eventSource.close();
            setIsProcessing(false);
        };
    };



    useEffect(() => {
        fetchProjects();
    }, []);

    return (
        <>
            <Header />
            <Container
                maxWidth={false}
                disableGutters
                sx={{
                    width: "100vw",
                    height: "100vh",
                    display: "flex",
                    flexDirection: "column",
                    boxSizing: "border-box",
                    alignItems: "center",
                }}
            >
                <Box
                    sx={{
                        width: "100%",
                        maxWidth: "800px",
                        display: "flex",
                        flexDirection: { xs: "column", sm: "row" },
                        justifyContent: "center",
                        alignItems: "center",
                        gap: 2,
                        mt: 6,
                        boxSizing: "border-box",
                    }}
                >
                    <TextField
                        label="Insert GitHub Project Repository URL"
                        variant="outlined"
                        fullWidth
                        value={urlInput}
                        onChange={(e) => setUrlInput(e.target.value)}
                        sx={{ flexGrow: 1 }}
                    />
                    <Button
                        variant="contained"
                        color="secondary"
                        onClick={handleLoadProject}
                        sx={{ mt: { xs: 2, sm: 0 } }}
                        disabled={isProcessing} // 처리 중 버튼 비활성화
                    >
                        {isProcessing ? "Processing..." : "Load Project"}
                    </Button>
                </Box>

                {/* 진행률 표시 */}
                {isProcessing && (
                    <Box sx={{ mt: 4, display: "flex", flexDirection: "column", alignItems: "center" }}>
                        <Typography variant="body1">{status}</Typography>
                        <CircularProgressWithLabel value={progress} />
                    </Box>
                )}

                <Box
                    sx={{
                        flex: 1,
                        minHeight: 0,
                        width: "100%",
                        maxWidth: "1200px",
                        mx: "auto",
                        overflowY: "auto",
                        overflowX: "hidden",
                        px: 2,
                        boxSizing: "border-box",
                        mt: 4,
                    }}
                >
                    <Typography variant="h5" align="center" sx={{ mb: 2 }}>
                        Project Overview
                    </Typography>

                    {loading ? (
                        <Typography align="center">Loading projects...</Typography>
                    ) : error ? (
                        <Typography color="error" align="center">
                            {error}
                        </Typography>
                    ) : (
                        <Grid container spacing={3}>
                            {projects.map((project, index) => (
                                <Grid item xs={12} sm={6} md={4} key={index}>
                                    <Link
                                        to={`/projects/${project.name}`}
                                        style={{ textDecoration: "none" }}
                                    >
                                        <Card
                                            sx={{
                                                cursor: "pointer",
                                                transition: "transform 0.2s",
                                                "&:hover": { transform: "scale(1.05)" },
                                            }}
                                        >
                                            <CardMedia
                                                component="img"
                                                src={fileimage}
                                                alt={project.name}
                                                sx={{
                                                    height: 80,
                                                    width: "auto",
                                                    objectFit: "cover",
                                                    margin: "0 auto",
                                                }}
                                            />
                                            <CardContent>
                                                <Typography variant="body1" align="center">
                                                    {project.name}
                                                </Typography>
                                            </CardContent>
                                        </Card>
                                    </Link>
                                </Grid>
                            ))}
                        </Grid>
                    )}
                </Box>
                <Footer />
            </Container>
        </>
    );
};

export default MainPage;
