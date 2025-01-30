import React, { useEffect, useState } from "react";
import {
    Container,
    Box,
    Grid,
    TextField,
    Button,
    Card,
    CardContent,
    Typography,
} from "@mui/material";
import Header from "../components/Header";
import Footer from "../components/Footer";

const MainPage = () => {
    // 프로젝트 데이터를 관리하는 상태
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true); // 로딩 상태
    const [error, setError] = useState(null); // 에러 상태

    // 백엔드에서 데이터를 가져오는 함수
    const fetchProjects = async () => {
        try {
            setLoading(true); // 로딩 시작
            const response = await fetch("http://localhost:8000/projectslist"); // API 엔드포인트
            if (!response.ok) {
                throw new Error("Failed to fetch projects");
            }
            const data = await response.json(); // JSON 데이터 파싱
            setProjects(data); // 상태 업데이트
        } catch (err) {
            setError(err.message); // 에러 상태 저장
        } finally {
            setLoading(false); // 로딩 종료
        }
    };

    // 컴포넌트가 마운트될 때 API 호출
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
                {/* ✅ 상단 검색 섹션 */}
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
                        sx={{ flexGrow: 1 }}
                    />
                    <Button
                        variant="contained"
                        color="secondary"
                        sx={{ mt: { xs: 2, sm: 0 } }}
                    >
                        Load Project
                    </Button>
                </Box>

                {/* ✅ 프로젝트 개요 섹션 */}
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
                                    <Card>
                                        <CardContent>
                                            <Typography variant="body1" align="center">
                                                {project.name}
                                            </Typography>
                                        </CardContent>
                                    </Card>
                                </Grid>
                            ))}
                        </Grid>
                    )}
                </Box>

                {/* ✅ Footer */}
                <Footer />
            </Container>
        </>
    );
};

export default MainPage;
