import React from "react";
import { AppBar, Toolbar, Typography, Box } from "@mui/material";
import { useNavigate } from "react-router-dom"; // useNavigate 훅 import

const Header = () => {
    const navigate = useNavigate(); // navigate 함수 가져오기

    return (
        <AppBar position="static" color="primary" elevation={4}>
            <Toolbar>
                <Typography
                    variant="h6"
                    component="div"
                    sx={{
                        fontWeight: "bold",
                        cursor: "pointer", // 마우스 올리면 클릭 가능하도록 변경
                        "&:hover": { textDecoration: "underline" }, // 마우스 올리면 밑줄 효과
                    }}
                    onClick={() => navigate("/main")} // /main으로 이동
                >
                    GitHub Project Based LLM System
                </Typography>
            </Toolbar>
        </AppBar>
    );
};

export default Header;
