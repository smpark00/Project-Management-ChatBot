import os
import csv
import requests
import zipfile
from fastapi import FastAPI, HTTPException, Query
from pathlib import Path
from fastapi import APIRouter
from dotenv import load_dotenv

router = APIRouter()

# .env 파일 로드
load_dotenv("../../.env")

# 저장 경로 설정
BASE_DIRECTORY = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage")))
BASE_DIRECTORY.mkdir(parents=True, exist_ok=True)

# GitHub Personal Access Token (환경 변수에서 가져오기)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}


def fetch_all_data(url, params=None):
    """페이징을 처리하여 모든 데이터를 가져오기"""
    all_data = []
    page = 1
    while True:
        if params is None:
            params = {}
        params.update({"per_page": 100, "page": page})  # 페이지 번호 추가

        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            data = response.json()
            if not data:  # 더 이상 데이터가 없으면 종료
                break
            all_data.extend(data)
            page += 1
        else:
            print(f"Error fetching data from {url}: {response.status_code}")
            break
    return all_data


def get_project_details(owner, repo):
    """특정 프로젝트의 상세 데이터 가져오기"""
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    # 리포지토리 기본 정보
    repo_info = requests.get(base_url, headers=HEADERS).json()

    # 모든 커밋 데이터
    commits = fetch_all_data(f"{base_url}/commits")

    # 모든 Pull Requests 데이터
    pull_requests = fetch_all_data(f"{base_url}/pulls", params={"state": "all"})

    # 모든 이슈 데이터
    issues = fetch_all_data(f"{base_url}/issues")

    return {
        "repo_info": repo_info,
        "commits": commits,
        "pull_requests": pull_requests,
        "issues": issues
    }


def save_to_csv(data, repo_name):
    """데이터를 CSV 파일로 저장"""
    repo_info = data["repo_info"]

    # 📌 프로젝트마다 디렉토리 생성 후, 그 안에 csv 디렉토리 생성
    project_path = BASE_DIRECTORY / repo_name / "csv"
    project_path.mkdir(parents=True, exist_ok=True)

    # 프로젝트 기본 정보 저장
    with open(project_path / f"{repo_name}_info.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Name", "Description", "Stars", "Forks", "Language", "Last Updated", "Owner"])
        writer.writerow([
            repo_info.get("id", ""),
            repo_info.get("name", ""),
            repo_info.get("description", ""),
            repo_info.get("stargazers_count", 0),
            repo_info.get("forks_count", 0),
            repo_info.get("language", ""),
            repo_info.get("updated_at", ""),
            repo_info.get("owner", {}).get("login", "")
        ])

    # 커밋 정보 저장
    with open(project_path / f"{repo_name}_commits.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Author", "Date", "Message"])
        for commit in data["commits"]:
            author_login = commit.get("author", {}).get("login") if commit.get("author") else "Unknown"
            writer.writerow([
                commit.get("sha", ""),
                author_login,
                commit["commit"]["author"]["date"],
                commit["commit"].get("message", "")
            ])

    # Pull Requests 정보 저장
    with open(project_path / f"{repo_name}_pull_requests.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Title", "Author", "State", "Created At", "Merged At", "Closed At"])
        for pr in data["pull_requests"]:
            writer.writerow([
                pr.get("id", ""),
                pr.get("title", ""),
                pr["user"]["login"],
                pr.get("state", ""),
                pr.get("created_at", ""),
                pr.get("merged_at", ""),
                pr.get("closed_at", "")
            ])

    # 이슈 정보 저장
    with open(project_path / f"{repo_name}_issues.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Title", "State", "Created At", "Closed At"])
        for issue in data["issues"]:
            writer.writerow([
                issue.get("id", ""),
                issue.get("title", ""),
                issue.get("state", ""),
                issue.get("created_at", ""),
                issue.get("closed_at", "")
            ])


@router.post("/download")
async def download_repository(repo_url: str = Query(...)):
    """
    GitHub 저장소를 다운로드하고 로컬에 저장한 후, 데이터를 CSV로 저장
    """
    try:
        if not repo_url.startswith("https://github.com/"):
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")

        repo_parts = repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid GitHub repository format")
        owner, repo = repo_parts[0], repo_parts[1]
        repo = repo.replace(".git", "")

        # GitHub API에서 데이터 가져오기
        repo_data = get_project_details(owner, repo)

        # CSV 저장
        save_to_csv(repo_data, repo)

        return {
            "message": "Repository data successfully saved.",
            "repository_name": repo,
            "csv_directory": str(BASE_DIRECTORY / repo / "csv"),
            "csv_files": [str(file) for file in (BASE_DIRECTORY / repo / "csv").glob("*.csv")]
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {repr(e)}")
