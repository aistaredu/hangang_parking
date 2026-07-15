// 모든 페이지 공통 navbar , footer

// 공통 메뉴 정의
// href : 이동할 경로 / label : 표시 글자 / admin : 관리자 전용 여부
const NAV_ITEMS = [
    { href: "/static/index.html",   label: "지도" },
    { href: "/static/predict.html", label: "예측하기" },
    { href: "/static/mypage.html",  label: "내 예약" },
    { href: "/static/admin.html",   label: "관리자", admin: true },  // 관리자만 노출
];

// navbar HTML 문자열 생성
function renderNavbar() {
    const path = window.location.pathname; // 현재 페이지 경로, http://127.0.0.1:8000/static/index.html
    const admin = (typeof isAdmin === "function") && isAdmin(); // isAdmin이 함수면 isAdmin() 함수 호출
    // 관리자 여부에 따라 메뉴 목록을 필터링, 일반 사용자와 관리자 전용은 관리자만
    const menuHtml = NAV_ITEMS.filter(item => !item.admin || admin).map(item => {
        // 현재 페이지면 active 클래스 부여, /static/index.html,
        const active = path.endsWith(item.href.split("/").pop()) ? "active" : "";
        return `<li class="nav-item">
                    <a class="nav-link ${active}" href="${item.href}">${item.label}</a>
                </li>`;
    }).join("");
    return `
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
      <div class="container">
        <a class="navbar-brand  fw-bold" href="/static/index.html"><i class="bi bi-p-square-fill"></i> 한강공원 주차 예측</a>
        <!--  햄버거 버튼    -->
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navMenu">
          <ul class="navbar-nav me-auto">
            ${menuHtml}
          </ul>
           <div class="d-flex gap-2 align-items-center"  id="authButtons">
                 <!-- 로그인 상태: 사용자 이름 표시 -->
                <span class="navbar-text d-none text-light small" id="userNameDisplay"></span>
                <!-- 로그인 상태: 로그아웃 버튼 -->
                <button class="btn btn-outline-light btn-sm d-none" id="logoutBtn">로그아웃</button>
                <!-- 로그인 버튼: 로그인 모달을 여는 트리거 -->
                <button type="button" class="btn btn-outline-light  btn-sm"
                        id="loginBtn" data-bs-toggle="modal" data-bs-target="#authModal">로그인</button>
            </div>
        </div>
      </div>
    </nav>`;
}
// footer HTML 문자열 생성
function renderFooter() {
    const year = new Date().getFullYear();
    return `
        <footer  class="bg-light border-top mt-5 py-3">
            <div class="container text-center text-muted small">
                한강공원 주차장 예측 서비스 | 데이터: 서울 열린데이터광장 | &copy; ${year}
            </div>
        </footer>`;
}
// navbar 로그인 상태 반영
//  Navbar 인증 상태 전환
function updateNavbar() {
    const loginBtn        = document.querySelector("#loginBtn");
    const logoutBtn       = document.querySelector("#logoutBtn");
    const userNameDisplay = document.querySelector("#userNameDisplay");
    // navbar가 아직 안 그려졌으면 중단(방어 코드)
    if (!loginBtn || !logoutBtn || !userNameDisplay) return;

    if(isLoggedIn()) { // 로그인 상태 처리
        loginBtn.classList.add("d-none");           // 로그인 버튼 숨김
        logoutBtn.classList.remove("d-none");       // 로그아웃 버튼 표시
        userNameDisplay.classList.remove("d-none"); // 이름 표시
        userNameDisplay.textContent = `${getUserName()}님`;
    } else { // 비로그인 상태 처리
        loginBtn.classList.remove("d-none");     // 로그인 버튼 표시
        logoutBtn.classList.add("d-none");       // 로그아웃 버튼 숨김
        userNameDisplay.classList.add("d-none"); // 이름 숨김
        userNameDisplay.textContent = "";        // 텍스트 초기화
    }
}


// Modal 닫기
function closeModal() {
    const modalEl       = document.querySelector("#authModal");
    const modalInstance = bootstrap.Modal.getInstance(modalEl);// 이미 열려있는 Modal의 인스턴스를 반환
    if (modalInstance) modalInstance.hide(); // Modal이 열리지 않은 상태이면 null 반환
}

// Alert 오류 메시지 표시
function showError(elementId, message) {
    const el = document.querySelector("#" + elementId);
    el.textContent = message; // 오류 메시지 텍스트 설정
    el.classList.remove("d-none"); // 숨김 해제 → 화면에 표시
}

// Alert 오류 메시지 숨김
function clearError(elementId) {
    const el = document.querySelector("#" + elementId); //div
    el.textContent = "";        // 텍스트 초기화
    el.classList.add("d-none"); // d-none 추가 → 다시 숨김
}

// 로그인 처리 함수
async function handleLogin() {
    const email    = document.querySelector("#loginEmail").value.trim();
    const password = document.querySelector("#loginPw").value;
    const errEl    = document.querySelector("#loginError");

    // 서버 요청 전 유효성 검사
    if (!email || !password) { // !email: 빈 문자열(""), null, undefined 모두 true
        showError("loginError", "이메일과 비밀번호를 모두 입력해주세요.");
        return; // 함수 종료
    }
    clearError("loginError"); // 이전 오류 메시지 초기화
    try {
        // POST /users/login 호출
        const data = await apiPost("/users/login", { email, password });
        //토큰 저장
        saveToken(data.access_token);
        // 사용자 이름 저장 (Navbar 표시용), user1@test.com -> user1
        localStorage.setItem("user_name", email.split("@")[0]);

        closeModal();
        updateNavbar();
        showToast("로그인 성공! 환영합니다 ", "success");

    }catch (error) {
        showError("loginError", error.message || "로그인에 실패했습니다.");
    }
}

// 회원가입 처리 함수
async function handleSignup() {
    // input 입력값 가져오기
    const name      = document.querySelector("#signupName").value.trim();
    const email     = document.querySelector("#signupEmail").value.trim();
    const password  = document.querySelector("#signupPw").value;
    const pwConfirm = document.querySelector("#signupPwConfirm").value;

    // 빈 값 체크
    if (!name || !email || !password) {
        showError("signupError", "모든 항목을 입력해주세요.");
        return;
    }

     // 비밀번호 일치 여부 확인 (서버에 보내기 전 클라이언트에서 처리)
    if (password !== pwConfirm) {
        showError("signupError", "비밀번호가 일치하지 않습니다.");
        return;
    }
    clearError("signupError");
    try {
        // POST /users/signup 호출
        await apiPost("/users/signup", { email, password, name });
        closeModal();
        showToast("회원가입 완료! 로그인해주세요 ", "success");
        document.querySelector("#loginEmail").value = email; // 로그인 탭의 이메일 필드에 방금 가입한 이메일 자동 입력
    }catch (error) {
        showError("signupError", error.message || "회원가입에 실패했습니다.");

    }
}

// 로그아웃 처리 함수
function handleLogout() {
    removeToken(); // api.js
    localStorage.removeItem("user_name");
    updateNavbar(); // Navbar를 "로그인 버튼" 상태로 전환
    showToast("로그아웃 되었습니다.", "warning");
    window.location.href = "/static/index.html"; // 로그아웃 후 메인 페이지로 이동 (관리자 페이지에 남지 않도록)
}

//메뉴(관리자 링크 포함)를 새 로그인 상태로 다시 그림
function refreshNavbar() {
    const navSlot = document.querySelector("#navbar-placeholder");
    if (!navSlot) return;
    navSlot.innerHTML = renderNavbar();
    updateNavbar(); // 로그인,로그아웃 버튼 상태 반영
    // innerHTML을 새로 넣으면 기존 이벤트 연결이 사라지므로 다시 연결
    const logoutBtn = document.querySelector("#logoutBtn");
    if (logoutBtn) logoutBtn.addEventListener("click", handleLogout);
}

// 페이지 로드 시: navbar/footer 삽입 → 상태 반영 → 이벤트 연결
document.addEventListener("DOMContentLoaded", () => {
    const footSlot = document.querySelector("#footer-placeholder");
    if (footSlot) footSlot.innerHTML = renderFooter();

    refreshNavbar(); // navbar 그리기 + 로그인 상태 반영 + 로그아웃 버튼 연결

    //  로그인/회원가입 버튼 이벤트 연결
    document.querySelector("#loginSubmitBtn")?.addEventListener("click", handleLogin);
    document.querySelector("#signupSubmitBtn")?.addEventListener("click", handleSignup);
    document.querySelector("#loginPw")?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") handleLogin();
    });
});