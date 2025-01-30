import React from "react";
import { useParams } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";
import { Container, Typography, Box } from "@mui/material";

const ProjectPage = () => {
    const { projectName } = useParams(); // URL 파라미터에서 프로젝트 이름 가져오기

    return (
        <>
            <Header />
            <Container
                sx={{
                    height: "100vh",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "center",
                    alignItems: "center",
                }}
            >
                <Box>
                    <Typography variant="h4" align="center" gutterBottom>
                        {projectName}
                    </Typography>
                    <Typography variant="body1" align="center">
                        This is the detailed page for project: {projectName}
                    </Typography>
                </Box>
            </Container>
            <Footer />
        </>
    );
};

export default ProjectPage;
