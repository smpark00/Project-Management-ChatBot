import React from "react";
import { Box, Typography } from "@mui/material";
import footerImage from "../assets/images/SELAB2.png"; // 이미지 import
import footerImage2 from "../assets/images/SPID.png"; // 이미지 import

const Footer = () => {
    return (
        <Box
            component="footer"
            sx={{
                width: "100%",
                height: "60px", // Footer 높이 고정
                textAlign: "center",
                backgroundColor: "white",
                color: "black",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                position: "relative",
                boxSizing: "border-box",
            }}
        >
            <Typography variant="body2">
                © 2025 SPID x Kyonggi University SELAB
            </Typography>

            {/* ✅ 오른쪽 하단에 두 개의 이미지 정렬 */}
            <Box
                sx={{
                    position: "absolute",
                    right: "20px",
                    bottom: "10px",
                    display: "flex", // 가로 정렬
                    gap: "10px", // 두 이미지 사이 간격
                }}
            >
                <Box
                    component="img"
                    src={footerImage2}
                    alt="Footer Image2"
                    sx={{ height: "40px" }}
                />
                <Box
                    component="img"
                    src={footerImage}
                    alt="Footer Image"
                    sx={{ height: "40px" }}
                />
            </Box>
        </Box>
    );
};

export default Footer;
