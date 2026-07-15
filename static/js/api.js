// 공통 API 호출 유틸리티

// 서버 기본 주소 설정
// const BASE_URL = "http://127.0.0.1:8000";
const BASE_URL = "";

// 개발 환경: http://127.0.0.1:8000
// 배포 환경(Railway): https://프로젝트명.up.railway.app

// JWT 토큰 관리 함수 4개

// 로그인 성공 후 JWT 토큰을 localStorage에 저장
// 이후 모든 API 호출의 Authorization 헤더에 자동으로 포함
function saveToken(token) {
     localStorage.setItem("access_token", token);
}

// localStorage에서 JWT 토큰을 읽어온다, 토큰이 없으면 null을 반환
function getToken() {
    return localStorage.getItem("access_token");
}

// 로그아웃 시 localStorage에서 JWT 토큰을 삭제
function removeToken() {
    localStorage.removeItem("access_token");
}

// 로그인 여부를 확인
// localStorage에 access_token이 있으면 true, 없으면 false를 반환
// getToken()이 null이면 → false (비로그인), 토큰이 있으면  → true (로그인)
function isLoggedIn() {
    return getToken() !== null;
}

// 공통 HTTP 헤더 생성
// 모든 API 요청에 공통으로 들어가는 헤더
// 로그인 상태이면 Authorization 헤더를 자동으로 추가
// 반환 예시 (비로그인):  { "Content-Type": "application/json" }
// (로그인): { "Content-Type": "application/json", "Authorization": "Bearer 토큰" }
function getHeaders() {
    const headers = {
        "Content-Type": "application/json", // Content-Type: 요청 본문이 JSON 형식임을 서버에 알림
    }
    const token = getToken();
    if (token) {
        headers["Authorization"] = `Bearer ${token}`; // Bearer 인증 방식
    }
    return headers;
}

// GET 요청 — 데이터 조회
// HTTP GET 요청을 보내고 JSON 응답을 반환
// async 함수: await 키워드를 사용해 비동기 작업을 동기처럼 작성
// await: 서버 응답이 올 때까지 이 줄에서 기다림 (브라우저는 멈추지 않음)
async function apiGet(path) { //http://127.0.0.1:8000/parking-lots
    try {
        const response = await fetch(`${BASE_URL}${path}`, { // fetch(): 브라우저 내장 HTTP 요청 함수
            method : "GET",
            headers: getHeaders(),
        });
        if(!response.ok){
            const error = await response.json(); // FastAPI의 HTTPException detail 메시지를 오류로 던짐
            throw new Error(error.detail || `오류: ${response.status}`); // new Error(A || B) A가 없으면 B 실행
        }
        return await response.json(); // response.json(): HTTP 응답 본문을 JSON → JavaScript 객체로 파싱
    } catch (error) { // 네트워크 오류(서버 꺼짐), HTTP 오류 모두 여기서 처리
        console.error(`GET ${path} 실패:`, error.message);
        throw error; // throw: 오류를 다시 던져서 호출한 곳 (loadParkingLots()) 에서도 처리 가능
    }
}

// POST 요청 — 데이터 생성
async function apiPost(path, body) {
    try {
        const response = await fetch(`${BASE_URL}${path}`, {
            method : "POST",
            headers: getHeaders(),
            body   : JSON.stringify(body), //JavaScript 객체 → JSON 문자열 변환  { email: "a@b.com" } → '{"email":"a@b.com"}'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `오류: ${response.status}`);
        }
        const text = await response.text(); // 201 Created는 본문이 있는 경우도 있고 없는 경우도 있음
        return text ? JSON.parse(text) : null; // response.text()로 먼저 읽고 내용이 있으면 JSON 파싱,JavaScript 객체로 변환
    }catch (error) {
        console.error(`POST ${path} 실패:`, error.message);
        throw error;
    }
}

// PATCH 요청 — 데이터 수정
// HTTP PATCH 요청을 보내고 JSON 응답을 반환, 수정할 필드만 포함해서 보낸다
// @param {string} path - API 경로 (예: "/parking-lots/1")
// @param {object} body - 수정할 필드만 포함한 객체
async function apiPatch(path, body) {
    try {
        const response = await fetch(`${BASE_URL}${path}`, {
            method : "PATCH",
            headers: getHeaders(),
            body   : JSON.stringify(body),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `오류: ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error(`PATCH ${path} 실패:`, error.message);
        throw error;
    }
}

// DELETE 요청 — 데이터 삭제
// HTTP DELETE 요청을 보낸다
// 204 No Content: 삭제 성공 시 응답 본문 없음
// @param {string} path - API 경로 (예: "/reservations/1")
// @returns {Promise<boolean>} - 삭제 성공 시 true
async function apiDelete(path) {
    try {
        const response = await fetch(`${BASE_URL}${path}`, {
            method : "DELETE",
            headers: getHeaders(),
            // DELETE는 body 없음
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `오류: ${response.status}`);
        }

        return true;  // 204 No Content → 본문 없이 성공 반환

    } catch (error) {
        console.error(`DELETE ${path} 실패:`, error.message);
        throw error;
    }
}

// JWT 페이로드 해독 함수 (role / user_id 읽기)
function getPayload() {
    const token = getToken();
    if (!token) return null;
    try { //일반 문자열로 디코딩
        return JSON.parse(atob(token.split(".")[1])); // JWT는 "헤더.페이로드.서명" 세 부분이 점(.)으로 이어진 구조
    } catch {
        return null;
    }
}

// 현재 로그인한 사용자의 역할(role)을 반환
function getUserRole() {
    const payload = getPayload();
    return payload ? payload.role : null;
}

// 현재 로그인한 사용자가 관리자인지 여부를 반환
function isAdmin() {
    return getUserRole() === "admin";
}
// 화면에 표시할 사용자 이름을 반환
function getUserName() {
    return localStorage.getItem("user_name") || "사용자";
}


// Toast 알림 함수
// 화면 오른쪽 하단에 잠깐 나타났다 사라지는 알림을 표시
// 로그인 성공/실패 알림에 사용
// Toast 알림 표시
function showToast(message, type = "success") {
    const existing = document.getElementById("liveToast");
    if (existing) existing.remove(); // 이미 표시 중인 Toast가 있으면 먼저 제거

    const toastHtml = `
    <div  id="liveToast" class="toast align-items-center text-bg-${type} border-0" 
        role="alert" aria-live="assertive" style="position:fixed; bottom:1rem; right:1rem; z-index:9999;>
        <div class="d-flex">
            <div class="toast-body fw-bold" id="toastMessage">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="닫기"></button>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML("beforeend", toastHtml);
    // insertAdjacentHTML("beforeend", ...): body 태그 닫히기 직전에 HTML 삽입

    // Bootstrap Toast 인스턴스 생성 후 표시
    const toastEl = document.getElementById("liveToast");
    // Bootstrap Toast 인스턴스 생성 & 표시, 3초 후 자동으로 닫힘
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
}