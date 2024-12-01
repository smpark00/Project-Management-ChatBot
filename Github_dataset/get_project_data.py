import requests
import random
import csv
import os
import shutil

from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Get the token from the environment variable
TOKEN = os.getenv("GITHUB_TOKEN")

# 인증 헤더
HEADERS = {
    "Authorization": f"Bearer {TOKEN}"
}

# GitHub Search API URL
SEARCH_URL = "https://api.github.com/search/repositories"

def get_random_project():
    params = {
        "q": "stars:<2000",  # 별 50개 이상 100개 이하
        "sort": "stars",              # 별점 순 정렬
        "order": "desc",              # 내림차순 정렬
        "per_page": 30                # 한 번에 최대 30개의 프로젝트 검색
    }


    response = requests.get(SEARCH_URL, headers=HEADERS, params=params)

    if response.status_code == 200:
        projects = response.json().get("items", [])
        if projects:
            return random.choice(projects)  # 랜덤으로 하나 선택
        else:
            print("No projects found with stars > 100.")
            return None
    else:
        print(f"Error fetching projects: {response.status_code}")
        return None

def fetch_all_data(url, params=None):
    """페이징을 처리하여 모든 데이터를 가져오기"""
    all_data = []
    page = 1
    while True:
        if params is None:
            params = {}
        # 페이지 번호 추가
        params.update({"per_page": 100, "page": page})
        
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

    # 모든 기여자 데이터
    contributors = fetch_all_data(f"{base_url}/contributors")

    # 모든 이슈 데이터
    issues = fetch_all_data(f"{base_url}/issues")

    return {
        "repo_info": repo_info,
        "commits": commits,
        "pull_requests": pull_requests,
        "contributors": contributors,
        "issues": issues
    }

def get_contributor_login(commit_author_name, commit_author_email, contributors):
    """커밋 작성자의 이름/이메일을 기반으로 기여자 아이디(login) 찾기"""
    for contributor in contributors:
        # 기여자의 이름 또는 이메일과 커밋 작성자를 매칭
        if contributor.get("login") and (
            commit_author_email == contributor.get("email", "") or
            commit_author_name == contributor.get("login", "")
        ):
            return contributor["login"]
    return "Unknown"  # 매칭되지 않으면 기본값 반환

def save_to_csv(data, project_directory):
    """데이터를 CSV 파일로 저장"""
    repo_info = data["repo_info"]
    repo_name = repo_info.get("name", "")

    # 공통 프로젝트 목록 CSV 파일 경로
    all_projects_csv = os.path.join(root_directory, "all_projects.csv")

    # 공통 프로젝트 목록 CSV 파일에 추가
    write_header = not os.path.exists(all_projects_csv)  # 파일이 없으면 헤더 작성
    with open(all_projects_csv, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if write_header:
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
    with open(os.path.join(project_directory, f"{repo_name}_commits.csv"), "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Project ID", "Author", "Date", "Message"])
        for commit in data["commits"]:
            author_login = commit.get("author", {}).get("login") if commit.get("author") else "Unknown"
            writer.writerow([
                commit.get("sha", ""),
                repo_info.get("id", ""),
                author_login,
                commit["commit"]["author"]["date"],
                commit["commit"].get("message", "")
            ])

    # Pull Requests 정보 저장
    with open(os.path.join(project_directory, f"{repo_name}_pull_requests.csv"), "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Project ID", "Title", "Author", "State", "Created At", "Merged At", "Closed At"])
        for pr in data["pull_requests"]:
            writer.writerow([
                pr.get("id", ""),
                repo_info.get("id", ""),
                pr.get("title", ""),
                pr["user"]["login"],
                pr.get("state", ""),
                pr.get("created_at", ""),
                pr.get("merged_at", ""),
                pr.get("closed_at", "")
            ])

    # 기여자 정보 저장
    with open(os.path.join(project_directory, f"{repo_name}_contributors.csv"), "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Project ID", "Name", "Commit Count"])
        for contributor in data["contributors"]:
            writer.writerow([
                contributor.get("id", ""),
                repo_info.get("id", ""),
                contributor.get("login", ""),
                contributor.get("contributions", 0)
            ])

    # 이슈 정보 저장
    issues = fetch_all_data(f"https://api.github.com/repos/{repo_info['owner']['login']}/{repo_info['name']}/issues")
    with open(os.path.join(project_directory, f"{repo_name}_issues.csv"), "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Project ID", "Title", "State", "Created At", "Closed At"])
        for issue in issues:
            writer.writerow([
                issue.get("id", ""),
                repo_info.get("id", ""),
                issue.get("title", ""),
                issue.get("state", ""),
                issue.get("created_at", ""),
                issue.get("closed_at", "")
            ])

    print(f"Data saved to CSV files for {repo_name}")



if __name__ == "__main__":
    # 루트 디렉토리에 'data' 디렉토리 생성
    root_directory = os.path.join(os.getcwd(), "data")
    os.makedirs(root_directory, exist_ok=True)

    # 여러 개의 프로젝트를 다운로드하기 위한 실행 흐름
    project_count = 30  # 다운로드할 프로젝트 수
    downloaded_projects = 0
    attempts = 0
    max_attempts_per_project = 5  # 프로젝트당 최대 시도 횟수

    while downloaded_projects < project_count:
        project_attempts = 0  # 특정 프로젝트의 시도 횟수 초기화
        random_project = None

        # 프로젝트를 찾기 위한 루프
        while random_project is None and project_attempts < max_attempts_per_project:
            random_project = get_random_project()
            project_attempts += 1

        # 최대 시도 초과 시 프로젝트를 버리고 다음으로 이동
        if random_project is None:
            print(f"Failed to select a project after {max_attempts_per_project} attempts. Skipping...")
            continue

        owner = random_project["owner"]["login"]
        repo = random_project["name"]

        print(f"Selected Project {downloaded_projects + 1}: {repo} by {owner}")

        # 프로젝트 데이터 다운로드 및 저장
        try:
            # 프로젝트별 디렉토리를 'data' 디렉토리 내에 생성
            project_directory = os.path.join(root_directory, repo)
            os.makedirs(project_directory, exist_ok=True)

            # 프로젝트 세부 정보 가져오기
            project_details = get_project_details(owner, repo)

            # 데이터 저장
            save_to_csv(project_details, project_directory)

            downloaded_projects += 1  # 성공적으로 저장한 프로젝트 수 증가
        except Exception as e:
            print(f"Error processing project {repo}: {e}")
            if os.path.exists(project_directory):
                shutil.rmtree(project_directory)
                print(f"오류가 발생하여 '{project_directory}' 디렉토리를 삭제했습니다.")


    print(f"Successfully downloaded {downloaded_projects} projects!")

