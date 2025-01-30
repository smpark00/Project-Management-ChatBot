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
import { Link } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";
import fileimage from "../assets/images/file.png";

const MainPage = () => {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

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
                        sx={{ flexGrow: 1 }}
                    />
                    <Button variant="contained" color="secondary" sx={{ mt: { xs: 2, sm: 0 } }}>
                        Load Project
                    </Button>
                </Box>

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
                                                    height: 80, // 원하는 높이 (픽셀 단위)
                                                    width: "auto", // 비율을 유지하면서 너비 자동 조정
                                                    objectFit: "cover", // 이미지의 비율을 유지하며 박스에 맞게 자르기
                                                    margin: "0 auto", // 이미지를 중앙 정렬
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
