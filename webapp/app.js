// ==================== AUDIO SYNTHESIS SYSTEM (Web Audio API) ====================
let audioCtx = null;
let soundEnabled = localStorage.getItem("football_sound_enabled") !== "false";

function getAudioContext() {
    if (!audioCtx) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
            audioCtx = new AudioContextClass();
        }
    }
    if (audioCtx && audioCtx.state === "suspended") {
        audioCtx.resume();
    }
    return audioCtx;
}

function toggleSound() {
    soundEnabled = !soundEnabled;
    localStorage.setItem("football_sound_enabled", soundEnabled ? "true" : "false");
    updateSoundToggleUI();
    if (soundEnabled) {
        playClickSound("success");
    }
}

function updateSoundToggleUI() {
    const isEnabled = (localStorage.getItem("football_sound_enabled") !== "false");
    soundEnabled = isEnabled;
    document.querySelectorAll(".btn-sound-toggle, .btn-sound-toggle-dark").forEach(btn => {
        const iconSpan = btn.querySelector(".sound-toggle-icon");
        const labelSpan = btn.querySelector(".sound-toggle-label");
        if (iconSpan) iconSpan.textContent = isEnabled ? "🔊" : "🔇";
        if (labelSpan) labelSpan.textContent = isEnabled ? "เสียง: เปิด" : "เสียง: ปิด";
        if (isEnabled) {
            btn.classList.add("sound-on");
            btn.classList.remove("sound-off");
        } else {
            btn.classList.add("sound-off");
            btn.classList.remove("sound-on");
        }
    });
}

function playClickSound(type = "click") {
    if (!soundEnabled) return;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        if (type === "tab") {
            // crisp high tick for tab switching
            osc.type = "sine";
            osc.frequency.setValueAtTime(950, now);
            osc.frequency.exponentialRampToValueAtTime(450, now + 0.04);
            gain.gain.setValueAtTime(0.08, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
            osc.start(now);
            osc.stop(now + 0.045);
        } else if (type === "card") {
            // warm pop for opening cards or modals
            osc.type = "triangle";
            osc.frequency.setValueAtTime(620, now);
            osc.frequency.exponentialRampToValueAtTime(280, now + 0.07);
            gain.gain.setValueAtTime(0.10, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.07);
            osc.start(now);
            osc.stop(now + 0.075);
        } else if (type === "success") {
            // pleasant two-tone chime (C5 -> G5)
            osc.type = "sine";
            osc.frequency.setValueAtTime(523.25, now);
            osc.frequency.setValueAtTime(783.99, now + 0.08);
            gain.gain.setValueAtTime(0.09, now);
            gain.gain.setValueAtTime(0.10, now + 0.08);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
            osc.start(now);
            osc.stop(now + 0.23);
        } else if (type === "danger") {
            // low warning tap
            osc.type = "triangle";
            osc.frequency.setValueAtTime(280, now);
            osc.frequency.exponentialRampToValueAtTime(140, now + 0.09);
            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);
            osc.start(now);
            osc.stop(now + 0.095);
        } else {
            // default standard subtle click
            osc.type = "sine";
            osc.frequency.setValueAtTime(780, now);
            osc.frequency.exponentialRampToValueAtTime(360, now + 0.035);
            gain.gain.setValueAtTime(0.08, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035);
            osc.start(now);
            osc.stop(now + 0.04);
        }
    } catch (err) {
        // Silently catch audio policy blocks
    }
}

// Global click event listener for tactile audio feedback
document.addEventListener("click", (e) => {
    const target = e.target.closest("button, a, .nav-pill-item, .player-card, .admin-squad-club-card, input[type='submit'], input[type='checkbox'], select, [role='button'], .btn-back-page, .split-link-btn, .photo-slide-arrow, .squad-toggle-btn, .carousel-arrow-btn, .ghost-hero-btn, .football-hero-arrow");
    if (!target) return;
    if (target.id === "btn-toggle-sound" || target.closest(".btn-sound-toggle") || target.closest(".btn-sound-toggle-dark")) return;
    
    if (target.classList.contains("nav-pill-item") || target.classList.contains("squad-toggle-btn") || target.classList.contains("btn-photo-tab")) {
        playClickSound("tab");
    } else if (target.classList.contains("player-card") || target.classList.contains("admin-squad-club-card")) {
        playClickSound("card");
    } else if (target.classList.contains("btn-green") || target.classList.contains("split-btn-submit") || target.type === "submit") {
        playClickSound("success");
    } else if (target.classList.contains("btn-red") || target.classList.contains("btn-logout-danger") || target.classList.contains("btn-danger")) {
        playClickSound("danger");
    } else {
        playClickSound("click");
    }
}, true);

// ==================== GLOBAL STATE ====================
let currentUser = null;
let appData = {
    players: [],
    clubs: [],
    offers: [],
    users: [],
    emails: []
};
let lastRegisteredUsername = "";
let pendingPlayerImageBase64 = "";
let pendingPlayerImageBase64_2 = "";
let pendingClubLogoBase64 = "";
let pendingEditClubLogoBase64 = "";
let pendingAgentPhotoBase64 = "";
let currentViewingAgentId = null;
let currentDetailAgentId = 1;
let pendingPlayerVideoBase64 = "";
let pendingPlayerVideoName = "";
let currentDetailPlayerId = null;
let highlightAnimId = null;
let scoutingPlayerIndex = 0;
let carouselPhotoIndex = 0;
let detailPhotoIndex = 0;
let currentFilteredPlayers = [];
let selectedMyClubName = "ครูคอมแต่ง";
let activeAdminStatusFilter = "ALL";
let adminSearchQuery = "";
let adminSelectedSquadClub = "ครูคอมแต่ง";
let playerFormOriginTab = null;
let playerDetailOriginTab = null;

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ==================== INITIALIZATION ====================
document.addEventListener("DOMContentLoaded", () => {
    updateSoundToggleUI();
    applyHeroBg();
    const saved = localStorage.getItem("football_session_user");
    if (saved) {
        try {
            currentUser = JSON.parse(saved);
            enterDashboard();
        } catch (e) {
            localStorage.removeItem("football_session_user");
        }
    }

    const fileInput = document.getElementById("p-image-file");
    if (fileInput) {
        fileInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            const prevBox = document.getElementById("p-image-preview-box");
            const prevImg = document.getElementById("p-image-preview-img");
            if (!file) {
                pendingPlayerImageBase64 = "";
                if (prevBox) prevBox.classList.add("hidden");
                return;
            }
            const reader = new FileReader();
            reader.onload = () => {
                pendingPlayerImageBase64 = reader.result;
                if (prevImg) prevImg.src = reader.result;
                if (prevBox) prevBox.classList.remove("hidden");
            };
            reader.readAsDataURL(file);
        });
    }

    const fileInput2 = document.getElementById("p-image-file-2");
    if (fileInput2) {
        fileInput2.addEventListener("change", (e) => {
            const file = e.target.files[0];
            const prevBox = document.getElementById("p-image-preview-box-2");
            const prevImg = document.getElementById("p-image-preview-img-2");
            if (!file) {
                pendingPlayerImageBase64_2 = "";
                if (prevBox) prevBox.classList.add("hidden");
                return;
            }
            const reader = new FileReader();
            reader.onload = () => {
                pendingPlayerImageBase64_2 = reader.result;
                if (prevImg) prevImg.src = reader.result;
                if (prevBox) prevBox.classList.remove("hidden");
            };
            reader.readAsDataURL(file);
        });
    }

    const videoInput = document.getElementById("p-video-file");
    if (videoInput) {
        videoInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (!file) {
                pendingPlayerVideoBase64 = "";
                pendingPlayerVideoName = "";
                return;
            }
            pendingPlayerVideoName = file.name;
            const reader = new FileReader();
            reader.onload = () => {
                pendingPlayerVideoBase64 = reader.result;
            };
            reader.readAsDataURL(file);
        });
    }
});

// ==================== API HELPER ====================
async function apiCall(action, payload = {}) {
    try {
        const res = await fetch(`api.php?action=${encodeURIComponent(action)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        return await res.json();
    } catch (err) {
        console.error("API call error:", action, err);
        return { ok: false, error: err.message || "ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้" };
    }
}

function formatEuro(amount) {
    const val = Number(amount || 0);
    if (val >= 1000000) {
        return "€" + (val / 1000000).toFixed(1).replace(".0", "") + "M";
    } else if (val >= 1000) {
        return "€" + Math.round(val / 1000).toLocaleString() + "K";
    }
    return "€" + val.toLocaleString();
}

// ==================== HERO STAGE & BACKGROUND SLIDER ====================
const HERO_BACKGROUNDS = [
    "/assets/stadium_bg.jpg",
    "/assets/wembley_bg.jpg",
    "/assets/bg_dark_stadium.jpg",
    "/assets/bg_night_lights.jpg"
];
let currentHeroBgIndex = 0;

function slideHeroBg(dir) {
    currentHeroBgIndex = (currentHeroBgIndex + dir + HERO_BACKGROUNDS.length) % HERO_BACKGROUNDS.length;
    applyHeroBg();
    playClickSound("tab");
}

function setHeroBg(idx) {
    if (idx >= 0 && idx < HERO_BACKGROUNDS.length) {
        currentHeroBgIndex = idx;
        applyHeroBg();
        playClickSound("tab");
    }
}

function applyHeroBg() {
    const authScreen = document.getElementById("auth-screen");
    if (authScreen) {
        authScreen.style.backgroundImage = `url('${HERO_BACKGROUNDS[currentHeroBgIndex]}')`;
    }
    renderHeroDots();
}

function renderHeroDots() {
    const container = document.getElementById("hero-dots-container");
    if (!container) return;
    container.innerHTML = "";
    HERO_BACKGROUNDS.forEach((_, idx) => {
        const dot = document.createElement("button");
        dot.type = "button";
        dot.className = "hero-dot" + (idx === currentHeroBgIndex ? " active" : "");
        dot.title = `ภาพสนามที่ ${idx + 1}`;
        dot.setAttribute("aria-label", `Slide ${idx + 1}`);
        dot.onclick = () => setHeroBg(idx);
        container.appendChild(dot);
    });
}

function openLoginModal() {
    const modal = document.getElementById("login-modal-overlay");
    if (modal) {
        modal.classList.remove("hidden");
        playClickSound("card");
        focusLoginForm();
    }
}

function closeLoginModal() {
    const modal = document.getElementById("login-modal-overlay");
    if (modal) {
        modal.classList.add("hidden");
    }
}

function handleLoginModalBackdrop(e) {
    if (e.target && e.target.id === "login-modal-overlay") {
        closeLoginModal();
        playClickSound("click");
    }
}

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeLoginModal();
    }
});

// ==================== AUTH & IN-PAGE VIEW SWITCHING ====================
function focusLoginForm() {
    const input = document.getElementById("login-username");
    if (input) {
        setTimeout(() => input.focus(), 100);
    }
}

function switchAuthPage(page) {
    closeLoginModal();
    document.getElementById("login-view").classList.add("hidden");
    document.getElementById("register-view").classList.add("hidden");
    const regAgentView = document.getElementById("register-agent-view");
    if (regAgentView) regAgentView.classList.add("hidden");
    document.getElementById("register-success-view").classList.add("hidden");
    const regAgentSuccess = document.getElementById("register-agent-success-view");
    if (regAgentSuccess) regAgentSuccess.classList.add("hidden");
    document.getElementById("auth-alert").classList.add("hidden");

    if (page === "login") {
        document.getElementById("login-view").classList.remove("hidden");
    } else if (page === "register") {
        document.getElementById("register-form").reset();
        document.getElementById("reg-doc-path").value = "";
        const docStatus = document.getElementById("reg-doc-status");
        if (docStatus) {
            docStatus.textContent = "⚠️ ยังไม่ได้แนบเอกสารการเงิน";
            docStatus.style.color = "#EF4444";
        }
        const errBox = document.getElementById("reg-error-msg");
        if (errBox) errBox.classList.add("hidden");
        document.getElementById("register-view").classList.remove("hidden");
    } else if (page === "register-agent") {
        const agentForm = document.getElementById("register-agent-form");
        if (agentForm) agentForm.reset();
        const errBox = document.getElementById("reg-agent-error-msg");
        if (errBox) errBox.classList.add("hidden");
        if (regAgentView) regAgentView.classList.remove("hidden");
    } else if (page === "success") {
        document.getElementById("register-success-view").classList.remove("hidden");
    } else if (page === "success-agent") {
        if (regAgentSuccess) regAgentSuccess.classList.remove("hidden");
    }
}

function toggleLoginPassword() {
    const input = document.getElementById("login-password");
    const btn = document.getElementById("eye-toggle-btn");
    if (!input || !btn) return;
    if (input.type === "password") {
        input.type = "text";
        btn.textContent = "ซ่อน";
    } else {
        input.type = "password";
        btn.textContent = "แสดง";
    }
}

function toggleQuickAccounts() {
    document.getElementById("quick-accounts-panel").classList.toggle("hidden");
}

function showForgotPasswordInfo() {
    showAuthAlert("หากลืมรหัสผ่าน กรุณาติดต่อผู้ดูแลระบบ (Admin) หรือตรวจสอบอีเมลสโมสรของท่าน (รหัสผ่านเริ่มต้นทดสอบ: password123)", "#1D4ED8");
}

function showAuthAlert(msg, color = "#B91C1C") {
    const box = document.getElementById("auth-alert");
    box.textContent = msg;
    box.style.color = color;
    box.classList.remove("hidden");
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value.trim();

    const res = await apiCall("login", { username, password });
    if (!res.ok) {
        showAuthAlert(res.error || "เข้าสู่ระบบไม่สำเร็จ");
        return;
    }

    currentUser = res.user;
    if (document.getElementById("remember-me").checked) {
        localStorage.setItem("football_session_user", JSON.stringify(currentUser));
    }
    enterDashboard();
}

async function quickLogin(username) {
    const res = await apiCall("quick_login", { username });
    if (!res.ok) {
        showAuthAlert(res.error || "ไม่พบบัญชีผู้ใช้");
        return;
    }
    currentUser = res.user;
    localStorage.setItem("football_session_user", JSON.stringify(currentUser));
    enterDashboard();
}

function handleRegFileSelect(input) {
    if (input.files && input.files[0]) {
        const fname = input.files[0].name;
        document.getElementById("reg-doc-path").value = "assets/financial_docs/uploaded_" + fname;
        const status = document.getElementById("reg-doc-status");
        status.textContent = "✔️ แนบไฟล์แล้ว: " + fname;
        status.style.color = "#10B981";
    }
}

async function handleRegisterSubmit(e) {
    e.preventDefault();
    const errBox = document.getElementById("reg-error-msg");
    errBox.classList.add("hidden");

    const club_name = document.getElementById("reg-club-name").value.trim();
    const country = document.getElementById("reg-league").value;
    const username = document.getElementById("reg-username").value.trim().toLowerCase();
    const email = document.getElementById("reg-email").value.trim().toLowerCase();
    const emailConfirm = document.getElementById("reg-email-confirm").value.trim().toLowerCase();
    const password = document.getElementById("reg-password").value.trim();
    const passwordConfirm = document.getElementById("reg-password-confirm").value.trim();
    const budget = Number(document.getElementById("reg-budget").value || 150000000);
    const bank_name = document.getElementById("reg-bank").value;
    const financial_doc = document.getElementById("reg-doc-path").value;

    if (email !== emailConfirm) {
        errBox.textContent = "⚠️ อีเมลและช่องยืนยันอีเมลไม่ตรงกัน กรุณาตรวจสอบอีกครั้ง";
        errBox.classList.remove("hidden");
        return;
    }
    if (password !== passwordConfirm) {
        errBox.textContent = "⚠️ รหัสผ่านทั้งสองช่องไม่ตรงกัน";
        errBox.classList.remove("hidden");
        return;
    }
    if (password.length < 4) {
        errBox.textContent = "⚠️ รหัสผ่านต้องมีความยาวอย่างน้อย 4 ตัวอักษร";
        errBox.classList.remove("hidden");
        return;
    }
    if (!financial_doc) {
        errBox.textContent = "⚠️ กรุณาแนบไฟล์เอกสารหลักฐานรับรองสถานะทางการเงิน";
        errBox.classList.remove("hidden");
        return;
    }

    const res = await apiCall("register_club", {
        club_name, country, username, email, password, budget, bank_name, financial_doc,
        logo_base64: pendingClubLogoBase64
    });

    if (!res.ok) {
        errBox.textContent = "⚠️ " + (res.error || "เกิดข้อผิดพลาดในการลงทะเบียน");
        errBox.classList.remove("hidden");
        return;
    }

    lastRegisteredUsername = username;
    document.getElementById("success-club-title").textContent = `สโมสร: ${club_name} (@${username})`;
    document.getElementById("success-budget").textContent = `💰 วงเงินที่ขออนุมัติ: ${formatEuro(budget)}`;
    document.getElementById("success-email").textContent = `✉️ อีเมลติดต่อที่ลงทะเบียน: ${email}`;
    switchAuthPage("success");
}

async function handleRegisterAgentSubmit(e) {
    e.preventDefault();
    const errBox = document.getElementById("reg-agent-error-msg");
    if (errBox) errBox.classList.add("hidden");

    const first_name = document.getElementById("reg-agent-firstname").value.trim();
    const last_name = document.getElementById("reg-agent-lastname").value.trim();
    const agency_name = document.getElementById("reg-agent-agency").value.trim();
    const username = document.getElementById("reg-agent-username").value.trim().toLowerCase();
    const email = document.getElementById("reg-agent-email").value.trim().toLowerCase();
    const emailConfirm = document.getElementById("reg-agent-email-confirm").value.trim().toLowerCase();
    const password = document.getElementById("reg-agent-password").value.trim();
    const passwordConfirm = document.getElementById("reg-agent-password-confirm").value.trim();

    if (email !== emailConfirm) {
        if (errBox) {
            errBox.textContent = "⚠️ อีเมลและช่องยืนยันอีเมลไม่ตรงกัน กรุณาตรวจสอบอีกครั้ง";
            errBox.classList.remove("hidden");
        }
        return;
    }
    if (password !== passwordConfirm) {
        if (errBox) {
            errBox.textContent = "⚠️ รหัสผ่านทั้งสองช่องไม่ตรงกัน";
            errBox.classList.remove("hidden");
        }
        return;
    }
    if (password.length < 4) {
        if (errBox) {
            errBox.textContent = "⚠️ รหัสผ่านต้องมีความยาวอย่างน้อย 4 ตัวอักษร";
            errBox.classList.remove("hidden");
        }
        return;
    }

    const res = await apiCall("register_agent", {
        username,
        first_name,
        last_name,
        agency_name,
        email,
        password
    });

    if (!res.ok) {
        if (errBox) {
            errBox.textContent = "⚠️ " + (res.error || "เกิดข้อผิดพลาดในการลงทะเบียนเอเยนต์");
            errBox.classList.remove("hidden");
        }
        return;
    }

    lastRegisteredUsername = username;
    const full_name = res.full_name || `${first_name} ${last_name}`.trim();
    const titleEl = document.getElementById("success-agent-title");
    if (titleEl) titleEl.textContent = `ตัวแทน: ${full_name} (@${username})`;
    const agencyEl = document.getElementById("success-agent-agency");
    if (agencyEl) agencyEl.textContent = `🏢 สังกัดเอเยนซี่: ${agency_name || "อิสระ (Independent)"}`;
    const emailEl = document.getElementById("success-agent-email");
    if (emailEl) emailEl.textContent = `✉️ อีเมลติดต่อที่ลงทะเบียน: ${email}`;

    switchAuthPage("success-agent");
}

function finishRegistrationToLogin() {
    switchAuthPage("login");
    if (lastRegisteredUsername) {
        document.getElementById("login-username").value = lastRegisteredUsername;
        document.getElementById("login-password").value = "";
    }
}

// ==================== DASHBOARD LOGIC ====================
async function enterDashboard() {
    document.getElementById("auth-screen").classList.add("hidden");
    document.getElementById("dashboard-screen").classList.remove("hidden");

    const roleBadge = document.getElementById("nav-role-badge");
    if (roleBadge) roleBadge.textContent = currentUser.role;
    const userLabel = document.getElementById("nav-user-label");
    if (userLabel) userLabel.textContent = `👤 ${currentUser.username} (${currentUser.role})`;

    // Show/Hide Admin-only elements
    document.querySelectorAll(".admin-only").forEach(el => {
        if (currentUser.role === "Admin") {
            el.classList.remove("hidden");
        } else {
            el.classList.add("hidden");
        }
    });

    // Show/Hide Club-only elements
    document.querySelectorAll(".club-only").forEach(el => {
        if (currentUser.role === "Club") {
            el.classList.remove("hidden");
        } else {
            el.classList.add("hidden");
        }
    });

    // Show/Hide Agent-only elements
    document.querySelectorAll(".agent-only").forEach(el => {
        if (currentUser.role === "Agent") {
            el.classList.remove("hidden");
        } else {
            el.classList.add("hidden");
        }
    });

    // Update navigation tab titles based on role
    const navMarket = document.getElementById("nav-tab-label-market");
    const navOffers = document.getElementById("nav-tab-label-offers");
    const navSquad = document.getElementById("nav-tab-label-squad");

    if (currentUser.role === "Admin") {
        if (navMarket) navMarket.textContent = "ทำเนียบนักเตะ & ภาพรวม (Admin)";
        if (navOffers) navOffers.textContent = "ตรวจสอบ & อนุมัติดีลซื้อขาย";
        if (navSquad) navSquad.textContent = "นักเตะในสังกัดสโมสร";
    } else if (currentUser.role === "Club") {
        if (navMarket) navMarket.textContent = "🌐 ตลาดซื้อขายนักเตะ";
        if (navOffers) navOffers.textContent = "🤝 ข้อเสนอซื้อขายของสโมสร";
        if (navSquad) navSquad.textContent = "⚽ นักเตะในสังกัดสโมสร (My Squad)";
    } else {
        if (navMarket) navMarket.textContent = "🌐 ตลาดซื้อขาย & ทำเนียบนักเตะ";
        if (navOffers) navOffers.textContent = "📩 ข้อเสนอสัญญา & ดีลย้ายทีม";
        if (navSquad) navSquad.textContent = "⚽ นักเตะในสังกัดเอเยนต์";
    }

    // Show/Hide Add Player button (Admin, Agent & Club)
    const addBtn = document.getElementById("btn-open-add-player");
    if (addBtn) {
        addBtn.classList.remove("hidden");
    }

    // ควบคุมปุ่มโลโก้สโมสร: เอเยนต์ต้องถูกซ่อนเด็ดขาด!
    const btnSquadLogo = document.getElementById("btn-squad-upload-logo");
    if (btnSquadLogo) {
        if (currentUser.role === "Agent") {
            btnSquadLogo.classList.add("hidden");
            btnSquadLogo.style.display = "none";
        } else {
            btnSquadLogo.classList.remove("hidden");
            btnSquadLogo.style.display = "inline-flex";
        }
    }

    // ปุ่มเพิ่มนักเตะในหน้า Squad
    const squadAddBtn = document.getElementById("btn-squad-add-player");
    if (squadAddBtn) {
        squadAddBtn.classList.remove("hidden");
        squadAddBtn.style.display = "inline-flex";
        if (currentUser.role === "Agent") {
            squadAddBtn.textContent = "➕ เพิ่มนักเตะในสังกัดเอเยนต์";
        } else {
            squadAddBtn.textContent = "➕ เพิ่มนักเตะเข้าสโมสรนี้";
        }
    }

    // Reset status filter to ALL on login/role switch
    activeAdminStatusFilter = "ALL";
    document.querySelectorAll(".btn-status-filter-pill").forEach(btn => {
        const isAll = btn.getAttribute("onclick")?.includes("'ALL'");
        btn.classList.toggle("active", Boolean(isAll));
    });

    switchDashboardTab("market");
    await loadAllData();
}

function switchDashboardTab(tabName) {
    const vid = document.getElementById("detail-video-player");
    if (vid && !vid.paused) vid.pause();

    ["market", "offers", "squad", "history", "clubs", "users"].forEach(t => {
        const sec = document.getElementById(`tab-${t}`);
        if (sec) sec.classList.toggle("hidden", t !== tabName);
    });

    document.querySelectorAll(".nav-tab-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.tab === tabName);
    });

    document.querySelectorAll(".nav-pill-item").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.tab === tabName);
    });

    if (tabName === "offers") {
        renderOffersTable();
    } else if (tabName === "market") {
        renderPlayersGrid();
    } else if (tabName === "squad") {
        if (currentUser && currentUser.role === "Admin") {
            renderAdminSquadClubsGrid();
        }
        renderSquadTable();
    } else if (tabName === "history") {
        renderHistoryTable();
    } else if (tabName === "clubs") {
        renderClubsTable();
    } else if (tabName === "users") {
        renderUsersTable();
    }
}

function handleLogoutClick() {
    localStorage.removeItem("football_session_user");
    currentUser = null;
    document.getElementById("dashboard-screen").classList.add("hidden");
    document.getElementById("auth-screen").classList.remove("hidden");
    switchAuthPage("login");
}

function setAdminStatusFilter(statusFilter) {
    activeAdminStatusFilter = statusFilter;
    document.querySelectorAll(".btn-status-filter-pill").forEach(btn => {
        const btnFilter = btn.getAttribute("onclick")?.match(/'([^']+)'/)?.[1] || "ALL";
        btn.classList.toggle("active", btnFilter === statusFilter);
    });
    renderPlayersGrid();
}

function handleAdminSearchInput(val) {
    adminSearchQuery = (val || "").trim().toLowerCase();
    renderPlayersGrid();
}

function exportSpreadsheetCSV() {
    const players = appData.players || [];
    if (!players.length) {
        alert("ไม่มีข้อมูลนักเตะสำหรับส่งออก");
        return;
    }

    const headers = [
        "รหัส (ID)",
        "ชื่อในการแข่งขัน (Known As)",
        "ชื่อจริง (Full Name)",
        "สโมสรปัจจุบัน (Current Club)",
        "ตำแหน่ง (Position)",
        "สัญชาติ (Nationality)",
        "ค่าพลัง (OVR)",
        "ศักยภาพ (POT)",
        "ราคาประเมิน (EUR)",
        "ราคาตั้งขาย (EUR)",
        "สถานะความพร้อม (Status)",
        "ไฟล์วิดีโอ (Video)",
        "ส่วนสูง (Height cm)",
        "น้ำหนัก (Weight kg)",
        "เท้าที่ถนัด (Foot)"
    ];

    const rows = players.map(p => [
        p.id,
        `"${(p.known_as || "").replace(/"/g, '""')}"`,
        `"${(p.first_name || "").replace(/"/g, '""')}"`,
        `"${(p.current_club || "Free Agent").replace(/"/g, '""')}"`,
        p.main_position || "ST",
        `"${(p.nationality || "").replace(/"/g, '""')}"`,
        p.overall_rating || 80,
        p.potential || 85,
        p.estimated_value || 0,
        p.asking_price || 0,
        `"${(p.availability_status || "พร้อมย้ายทีม (Available)").replace(/"/g, '""')}"`,
        p.video_path ? "มีวิดีโอไฮไลท์" : "ไม่มี",
        p.height_cm || 180,
        p.weight_kg || 75,
        `"${(p.preferred_foot || "ขวา").replace(/"/g, '""')}"`
    ]);

    const csvContent = "\uFEFF" + [headers.join(","), ...rows.map(r => r.join(","))].join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Football_Transfer_Operations_Report_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

async function handleUserMenuSelect(selectEl) {
    const val = selectEl.value;
    selectEl.value = "";
    if (!val) return;

    if (val === "refresh") {
        await loadAllData();
    } else if (val === "logout") {
        handleLogoutClick();
    } else if (val.startsWith("switch_")) {
        const targetUser = val.replace("switch_", "");
        await quickLogin(targetUser);
    }
}

async function loadAllData() {
    if (!currentUser) {
        currentUser = { id: 1, username: "admin", role: "Admin", status: "Active" };
    }
    let res = await apiCall("get_dashboard_data", { user_id: currentUser.id, role: currentUser.role });
    if (!res.ok) {
        await new Promise(r => setTimeout(r, 600));
        res = await apiCall("get_dashboard_data", { user_id: currentUser.id, role: currentUser.role });
    }
    if (!res.ok) return;

    appData = res;
    populateMyClubSelect();
    renderBannerAndKPIs();
    populateClubFilter();
    populateOfferClubScopeSelect();
    renderPlayersGrid();
    renderOffersTable();
    renderSquadTable();
    renderHistoryTable();
    renderClubEmailsTable();
    if (currentUser.role === "Admin") {
        renderAdminSquadClubsGrid();
        renderClubsTable();
        renderEmailsTable();
        renderUsersTable();
    }
}

function getCurrentUserAgent() {
    if (!currentUser) return null;
    if (appData.my_agent) return appData.my_agent;
    const byUid = (appData.agents || []).find(a => Number(a.user_id) === Number(currentUser.id));
    if (byUid) return byUid;
    if (currentUser.role === "Agent") {
        const byName = (appData.agents || []).find(a => 
            (a.email && currentUser.email && a.email.toLowerCase() === currentUser.email.toLowerCase()) ||
            (a.full_name && currentUser.username && a.full_name.toLowerCase().includes(currentUser.username.toLowerCase()))
        );
        if (byName) return byName;
        if (appData.agents && appData.agents.length > 0) return appData.agents[appData.agents.length - 1];
    }
    return null;
}

function getCurrentUserClubName() {
    if (!currentUser) return "ครูคอมแต่ง";
    // ข้อสำคัญ: ผู้ใช้บทบาทเอเยนต์ (Agent) ไม่ได้สังกัดสโมสรใด จึงต้องคืนค่าว่างเสมอ!
    if (currentUser.role === "Agent") {
        return "";
    }
    if (currentUser.role === "Club") {
        const myClub = appData.my_club || (appData.clubs || []).find(c => Number(c.user_id) === Number(currentUser.id));
        if (myClub && myClub.club_name) return myClub.club_name.trim();
        if (currentUser.username) {
            const u = currentUser.username.trim().toLowerCase();
            if (u === "comed fc" || u === "comedfc") return "ครูคอมแต่ง";
            const matched = (appData.clubs || []).find(c => (c.club_name || "").toLowerCase().replace(/\s+/g, "") === u);
            if (matched && matched.club_name) return matched.club_name.trim();
        }
        return "ครูคอมแต่ง";
    }
    if (selectedMyClubName === "NONE") return "";
    return (selectedMyClubName || "ครูคอมแต่ง").trim();
}

function populateMyClubSelect() {
    const sel = document.getElementById("market-my-club-select");
    if (!sel) return;

    if (currentUser && currentUser.role === "Club") {
        const myClub = appData.my_club || (appData.clubs || []).find(c => Number(c.user_id) === Number(currentUser.id));
        const cName = (myClub && myClub.club_name) ? myClub.club_name.trim() : getCurrentUserClubName();
        selectedMyClubName = cName;
        sel.innerHTML = `<option value="${cName}">🏳️ ${cName}</option>`;
        sel.value = cName;
        sel.disabled = true;
        return;
    }

    sel.disabled = false;
    const clubsSet = new Set(["ครูคอมแต่ง"]);
    (appData.clubs || []).forEach(c => {
        if (c.club_name) clubsSet.add(c.club_name.trim());
    });
    (appData.players || []).forEach(p => {
        if (p.current_club && p.current_club !== "Free Agent") clubsSet.add(p.current_club.trim());
    });
    const clubList = Array.from(clubsSet);

    if (!selectedMyClubName) {
        selectedMyClubName = (currentUser && currentUser.role === "Agent") ? "NONE" : "ครูคอมแต่ง";
    }

    sel.innerHTML = clubList.map(c => `<option value="${c}">🏳️ ${c}</option>`).join("") +
        `<option value="NONE">🌐 แสดงทุกสโมสร</option>`;

    if (selectedMyClubName === "NONE" || clubList.includes(selectedMyClubName)) {
        sel.value = selectedMyClubName;
    } else {
        selectedMyClubName = "ครูคอมแต่ง";
        sel.value = "ครูคอมแต่ง";
    }
}

function handleMyClubChange(clubVal) {
    selectedMyClubName = clubVal || "Real Madrid";
    const offerSel = document.getElementById("offer-club-scope-select");
    if (offerSel && selectedMyClubName !== "NONE") {
        offerSel.value = selectedMyClubName;
    }
    const filterClubSel = document.getElementById("filter-club");
    if (filterClubSel && filterClubSel.value.toLowerCase() === getCurrentUserClubName().toLowerCase()) {
        filterClubSel.value = "ALL";
    }
    renderBannerAndKPIs();
    populateClubFilter();
    renderPlayersGrid();
    renderOffersTable();
    renderSquadTable();
}

function getMarketPlayers() {
    const allPlayers = appData.players || [];
    const myClubName = getCurrentUserClubName().toLowerCase();
    if (!myClubName) return allPlayers;
    // กฎตลาดซื้อขายนักเตะ: เมื่อเลือกสโมสร (เช่น Real Madrid) จะไม่เห็นชื่อทีมตัวเองและชื่อนักเตะตัวเองในตลาดซื้อขายเด็ดขาด
    return allPlayers.filter(p => (p.current_club || "").trim().toLowerCase() !== myClubName);
}

function renderBannerAndKPIs() {
    const totalPlayers = (appData.players || []).length;
    const clubsCount = (appData.clubs || []).length;
    const totalOffers = (appData.offers || []).length;
    const completedDeals = (appData.offers || []).filter(o => o.status === "Completed").length;
    const pendingClubs = (appData.clubs || []).filter(c => c.verification_status === "Pending").length;
    const activeDeals = (appData.offers || []).filter(o => ["Pending", "Negotiating", "Accepted", "Contract Pending", "Pending Approval"].includes(o.status)).length;
    const totalFee = (appData.transfer_history || []).reduce((sum, h) => sum + Number(h.transfer_fee || 0), 0) || 1240000000;
    const pctCompleted = totalOffers > 0 ? ((completedDeals / totalOffers) * 100).toFixed(1) : "68.2";

    // 1. Header & Staff Pill Text
    const headerTitle = document.getElementById("header-main-title");
    const headerSub = document.getElementById("header-sub-title");
    const staffUser = document.getElementById("staff-username");
    const staffTitle = document.getElementById("staff-title-text");
    const staffBadge = document.getElementById("staff-role-badge");

    if (staffUser) staffUser.textContent = `(${currentUser.username})`;

    if (currentUser.role === "Admin") {
        if (headerTitle) headerTitle.textContent = "ศูนย์บริหารระบบและติดตามตลาดซื้อขาย (Admin Operations)";
        if (headerSub) headerSub.textContent = "Football Transfer Intelligence • ระบบสัญญา & ควบคุมดีล 3 ฝ่าย (Club • Agent • Admin)";
        if (staffTitle) staffTitle.textContent = "ฝ่ายกำกับดูแลและสัญญา (Admin)";
        if (staffBadge) {
            staffBadge.textContent = "ADMIN";
            staffBadge.style.background = "#EFF6FF";
            staffBadge.style.color = "#2563EB";
            staffBadge.style.borderColor = "#BFDBFE";
        }
    } else if (currentUser.role === "Club") {
        const cName = getCurrentUserClubName() || currentUser.username;
        if (headerTitle) headerTitle.textContent = `ศูนย์บริหารสโมสร ${cName} (Club Operations)`;
        if (headerSub) headerSub.textContent = "ระบบจัดซื้อและบริหารสัญญาผู้เล่น Football Transfer Management System";
        if (staffTitle) staffTitle.textContent = `เจ้าหน้าที่สโมสร (${cName})`;
        if (staffBadge) {
            staffBadge.textContent = "CLUB";
            staffBadge.style.background = "#ECFDF5";
            staffBadge.style.color = "#059669";
            staffBadge.style.borderColor = "#A7F3D0";
        }
    } else {
        if (headerTitle) headerTitle.textContent = `ศูนย์บริหารนักเตะและดีลสำหรับเอเยนต์ (Agent Operations)`;
        if (headerSub) headerSub.textContent = "ระบบดูแลสัญญาและการเจรจาค่าตัวนักฟุตบอล Football Agency Intelligence";
        if (staffTitle) staffTitle.textContent = `เอเยนต์ผู้ดูแลนักเตะ (${currentUser.username})`;
        if (staffBadge) {
            staffBadge.textContent = "AGENT";
            staffBadge.style.background = "#F3E8FF";
            staffBadge.style.color = "#7E22CE";
            staffBadge.style.borderColor = "#DDD6FE";
        }
    }

    // 2. Floating Nav Pill Counters
    const badgePlayers = document.getElementById("badge-count-players");
    const badgeOffers = document.getElementById("badge-count-offers");
    const badgeClubs = document.getElementById("badge-count-clubs");
    const badgeHistory = document.getElementById("badge-count-history");

    if (badgePlayers) badgePlayers.textContent = totalPlayers;
    if (badgeOffers) badgeOffers.textContent = `${totalOffers}/${totalOffers}`;
    if (badgeClubs) badgeClubs.textContent = `${clubsCount}/${clubsCount}`;
    if (badgeHistory) badgeHistory.textContent = (appData.transfer_history || []).length;

    // 3. Operations 4 Large Metric Cards
    const kpiPlayers = document.getElementById("admin-kpi-total-players");
    const kpiSubPlayers = document.getElementById("admin-kpi-sub-players");
    const kpiDeals = document.getElementById("admin-kpi-completed-deals");
    const kpiDealsPct = document.getElementById("admin-kpi-completed-pct");
    const kpiSubDeals = document.getElementById("admin-kpi-sub-deals");
    const kpiActive = document.getElementById("admin-kpi-active-deals");
    const kpiPending = document.getElementById("admin-kpi-pending-clubs");

    if (kpiPlayers) kpiPlayers.textContent = totalPlayers;
    if (kpiSubPlayers) kpiSubPlayers.textContent = `จาก ${clubsCount} สโมสรชั้นนำ & เอเยนต์ทั่วโลก`;
    if (kpiDeals) kpiDeals.textContent = completedDeals;
    if (kpiDealsPct) kpiDealsPct.textContent = `(${pctCompleted}%)`;
    if (kpiSubDeals) kpiSubDeals.textContent = `มูลค่าการซื้อขายรวมกว่า ${formatEuro(totalFee)}`;
    if (kpiActive) kpiActive.textContent = activeDeals;
    if (kpiPending) kpiPending.textContent = pendingClubs;

    // 4. Position Breakdown
    const fwCount = (appData.players || []).filter(p => ["ST", "CF", "LW", "RW"].includes(p.main_position)).length;
    const mfCount = (appData.players || []).filter(p => ["CAM", "CM", "CDM", "LM", "RM"].includes(p.main_position)).length;
    const dfCount = (appData.players || []).filter(p => ["CB", "LB", "RB", "LWB", "RWB"].includes(p.main_position)).length;
    const gkCount = (appData.players || []).filter(p => p.main_position === "GK").length;

    const breakTitle = document.getElementById("breakdown-header-title");
    if (breakTitle) breakTitle.textContent = `รายชื่อนักฟุตบอล ${totalPlayers} คน แยกตามตำแหน่งในสนาม`;
    const cFw = document.getElementById("count-pos-fw");
    const cMf = document.getElementById("count-pos-mf");
    const cDf = document.getElementById("count-pos-df");
    const cGk = document.getElementById("count-pos-gk");
    if (cFw) cFw.textContent = fwCount;
    if (cMf) cMf.textContent = mfCount;
    if (cDf) cDf.textContent = dfCount;
    if (cGk) cGk.textContent = gkCount;

    // 5. Process Stages (ส่วนที่ 1, ส่วนที่ 2, ส่วนที่ 3)
    const stage1Total = totalOffers || 22;
    const stage1Done = (appData.offers || []).filter(o => ["Accepted", "Contract Pending", "Pending Approval", "Completed"].includes(o.status)).length || 18;
    const stage1Pct = Math.round((stage1Done / stage1Total) * 100);
    const s1Text = document.getElementById("stage1-count-text");
    const s1Bar = document.getElementById("stage1-bar");
    const s1Left = document.getElementById("stage1-foot-left");
    const s1Right = document.getElementById("stage1-foot-right");
    if (s1Text) s1Text.textContent = `${stage1Done} / ${stage1Total} ดีล`;
    if (s1Bar) s1Bar.style.width = `${stage1Pct}%`;
    if (s1Left) s1Left.textContent = `ส่งข้อเสนอแล้ว ${stage1Pct}%`;
    if (s1Right) s1Right.textContent = `ยังเจรจาอยู่ ${Math.max(0, 100 - stage1Pct)}%`;

    const stage2Total = stage1Done || 18;
    const stage2Done = (appData.offers || []).filter(o => ["Pending Approval", "Completed"].includes(o.status)).length || 16;
    const stage2Pct = ((stage2Done / stage2Total) * 100).toFixed(1);
    const s2Text = document.getElementById("stage2-count-text");
    const s2Bar = document.getElementById("stage2-bar");
    const s2Left = document.getElementById("stage2-foot-left");
    const s2Right = document.getElementById("stage2-foot-right");
    if (s2Text) s2Text.textContent = `${stage2Done} / ${stage2Total} สัญญา`;
    if (s2Bar) s2Bar.style.width = `${stage2Pct}%`;
    if (s2Left) s2Left.textContent = `ร่างสัญญาครบ ${stage2Pct}%`;
    if (s2Right) s2Right.textContent = `รอลงนาม ${(100 - parseFloat(stage2Pct)).toFixed(1)}%`;

    const stage3Total = stage2Done || 16;
    const stage3Done = completedDeals || 15;
    const stage3Pct = ((stage3Done / stage3Total) * 100).toFixed(1);
    const s3Text = document.getElementById("stage3-count-text");
    const s3Bar = document.getElementById("stage3-bar");
    const s3Left = document.getElementById("stage3-foot-left");
    const s3Right = document.getElementById("stage3-foot-right");
    if (s3Text) s3Text.textContent = `${stage3Done} / ${stage3Total} ดีล`;
    if (s3Bar) s3Bar.style.width = `${stage3Pct}%`;
    if (s3Left) s3Left.textContent = `อนุมัติเสร็จสมบูรณ์ ${stage3Pct}%`;
    if (s3Right) s3Right.textContent = `รอตราประทับ ${(100 - parseFloat(stage3Pct)).toFixed(1)}%`;

    // 6. Action Filter Bar Pill Counts
    const completedPlayerIds = new Set((appData.offers || []).filter(o => o.status === "Completed").map(o => Number(o.player_id)));
    (appData.transfer_history || []).forEach(h => { if (h.player_id) completedPlayerIds.add(Number(h.player_id)); });
    const compPlayerCount = (appData.players || []).filter(p => completedPlayerIds.has(Number(p.id))).length || completedDeals || 15;

    const pendingClubNames = new Set((appData.clubs || []).filter(c => c.verification_status === "Pending").map(c => (c.club_name || "").trim().toLowerCase()));
    const pendPlayerCount = (appData.players || []).filter(p => pendingClubNames.has((p.current_club || "").trim().toLowerCase())).length || pendingClubs || 1;

    const availCount = (appData.players || []).filter(p => !p.availability_status || p.availability_status.includes("พร้อม") || p.availability_status.includes("Available")).length;
    const negCount = (appData.players || []).filter(p => p.availability_status && (p.availability_status.includes("เจรจา") || p.availability_status.includes("Negotiating"))).length;

    const pAll = document.getElementById("pill-count-all");
    const pAvail = document.getElementById("pill-count-avail");
    const pNeg = document.getElementById("pill-count-neg");
    const pComp = document.getElementById("pill-count-comp");
    const pPend = document.getElementById("pill-count-pending");

    if (pAll) pAll.textContent = totalPlayers;
    if (pAvail) pAvail.textContent = availCount;
    if (pNeg) pNeg.textContent = negCount;
    if (pComp) pComp.textContent = compPlayerCount;
    if (pPend) pPend.textContent = pendPlayerCount;

    // 7. Club-specific Market Banner Stats
    const clubTitleName = document.getElementById("club-banner-title-name");
    const clubBudgetEl = document.getElementById("club-stat-budget");
    const clubMarketPlayersEl = document.getElementById("club-stat-market-players");
    const clubMarketSubEl = document.getElementById("club-stat-market-sub");
    const clubMyDealsEl = document.getElementById("club-stat-my-deals");

    const currentClubName = getCurrentUserClubName() || "Real Madrid";
    if (clubTitleName) clubTitleName.textContent = currentClubName;

    // Find club budget
    const myClubObj = (appData.clubs || []).find(c => (c.club_name || "").toLowerCase() === currentClubName.toLowerCase()) || appData.my_club;
    const clubBudgetVal = myClubObj ? Number(myClubObj.budget || 0) : 150000000;
    if (clubBudgetEl) clubBudgetEl.textContent = formatEuro(clubBudgetVal);

    // Available players in market (excluding own club)
    const marketPlayersCount = getMarketPlayers().length;
    if (clubMarketPlayersEl) clubMarketPlayersEl.innerHTML = `${marketPlayersCount} <span>คน</span>`;
    if (clubMarketSubEl) clubMarketSubEl.textContent = `จากสโมสรอื่นทั่วโลก (ไม่รวม ${currentClubName})`;

    // Deals sent by this club
    const myClubDeals = (appData.offers || []).filter(o => (o.club_name || "").toLowerCase() === currentClubName.toLowerCase());
    if (clubMyDealsEl) clubMyDealsEl.innerHTML = `${myClubDeals.length} <span>ดีล</span>`;

    // Club pill counts
    const clubPillAll = document.getElementById("club-pill-all");
    const clubPillAvail = document.getElementById("club-pill-avail");
    const clubPillNeg = document.getElementById("club-pill-neg");
    if (clubPillAll) clubPillAll.textContent = marketPlayersCount;
    if (clubPillAvail) {
        const cAvail = getMarketPlayers().filter(p => !p.availability_status || p.availability_status.includes("พร้อม") || p.availability_status.includes("Available")).length;
        clubPillAvail.textContent = cAvail;
    }
    if (clubPillNeg) {
        const cNeg = getMarketPlayers().filter(p => p.availability_status && (p.availability_status.includes("เจรจา") || p.availability_status.includes("Negotiating"))).length;
        clubPillNeg.textContent = cNeg;
    }

    // 8. Agent-specific Market Banner Stats
    const agentTitleName = document.getElementById("agent-banner-title-name");
    const agentPlayersCountEl = document.getElementById("agent-stat-players-count");
    const agentPendingOffersEl = document.getElementById("agent-stat-pending-offers");
    const agentCompletedDealsEl = document.getElementById("agent-stat-completed-deals");

    if (agentTitleName) agentTitleName.textContent = currentUser ? currentUser.username : "Agent Portal";

    const myAgent = appData.my_agent || (appData.agents || []).find(a => Number(a.user_id) === Number(currentUser.id));
    const myAid = myAgent ? Number(myAgent.id) : 1;
    const myAgentPlayers = (appData.players || []).filter(p => {
        if (currentUser && currentUser.role === "Agent" && currentUser.id) {
            return Number(p.agent_id) === myAid || Number(p.agent_id) === Number(currentUser.id) || p.agent_name === currentUser.username;
        }
        return true;
    });
    const agentDealsPending = (appData.offers || []).filter(o => ["Pending", "Negotiating", "Contract Pending"].includes(o.status));
    const agentDealsDone = (appData.offers || []).filter(o => o.status === "Completed");

    if (agentPlayersCountEl) agentPlayersCountEl.innerHTML = `${myAgentPlayers.length} <span>คน</span>`;
    if (agentPendingOffersEl) agentPendingOffersEl.innerHTML = `${agentDealsPending.length} <span>ข้อเสนอ</span>`;
    if (agentCompletedDealsEl) agentCompletedDealsEl.innerHTML = `${agentDealsDone.length} <span>คน</span>`;

    const agentPillAll = document.getElementById("agent-pill-all");
    const agentPillAvail = document.getElementById("agent-pill-avail");
    const agentPillNeg = document.getElementById("agent-pill-neg");
    if (agentPillAll) agentPillAll.textContent = totalPlayers;
    if (agentPillAvail) agentPillAvail.textContent = availCount;
    if (agentPillNeg) agentPillNeg.textContent = negCount;
}

function populateClubFilter() {
    const sel = document.getElementById("filter-club");
    const currentVal = sel.value;
    const myClubNameLower = getCurrentUserClubName().toLowerCase();
    const clubsSet = new Set();

    getMarketPlayers().forEach(p => {
        const cName = (p.current_club || "").trim();
        if (cName && (!myClubNameLower || cName.toLowerCase() !== myClubNameLower)) {
            clubsSet.add(cName);
        }
    });
    appData.clubs.forEach(c => {
        const cName = (c.club_name || "").trim();
        if (cName && (!myClubNameLower || cName.toLowerCase() !== myClubNameLower)) {
            clubsSet.add(cName);
        }
    });

    const sortedClubs = Array.from(clubsSet).sort();
    sel.innerHTML = `<option value="ALL">🏟️ สโมสรอื่นทั้งหมดในตลาด (กรองตามสโมสร)</option>` +
        sortedClubs.map(c => `<option value="${c}">${c}</option>`).join("");

    if (sortedClubs.includes(currentVal)) {
        sel.value = currentVal;
    } else {
        sel.value = "ALL";
    }
}

function getPlayerPhotoUrl(player) {
    if (!player) return "/assets/players/player_1.png";

    // 1. ถ้านักเตะมีรูปที่อัปโหลดผ่านเว็บ (web_player_) หรือรูปเฉพาะ (player_61 หรือรูปนอกระบบ)
    if (player.image_path) {
        const clean = "/" + player.image_path.replace(/^\/+/, "");
        if (clean.includes("web_player_") || clean.includes("player_61") || !clean.match(/\/player_\d+\.png$/i)) {
            return clean;
        }
    }

    // 2. ถ้ามีรูปจริงความละเอียดสูงใน gallery_json (Wikimedia หรือ URL ภายนอก)
    if (player.gallery_json) {
        try {
            const gallery = JSON.parse(player.gallery_json);
            if (Array.isArray(gallery) && gallery.length > 0) {
                const realPhoto = gallery.find(item => item.url && (item.url.includes("wikimedia.org") || item.url.startsWith("http")));
                if (realPhoto && realPhoto.url) {
                    return realPhoto.url;
                }
                if (gallery[1] && gallery[1].url && !gallery[1].url.endsWith("/player_51.png")) {
                    return gallery[1].url;
                }
                if (gallery[0] && gallery[0].url) {
                    return gallery[0].url;
                }
            }
        } catch (e) {}
    }

    // 3. ถ้ามี image_path อื่นๆ
    if (player.image_path) {
        return "/" + player.image_path.replace(/^\/+/, "");
    }

    // 4. ถ้า player.id อยู่ในช่วง 1-56 และไฟล์มีอยู่
    const pid = Number(player.id);
    if (pid >= 1 && pid <= 56) {
        return `/assets/players/player_${pid}.png`;
    }

    return "/assets/players/player_1.png";
}

function getPlayerGallery(player) {
    const list = [];
    const name = player.known_as || player.first_name || "นักฟุตบอล";
    const h = player.height_cm || 182;
    const w = player.weight_kg || 76;
    const body = player.body_type || "สมส่วน แข็งแกร่ง (Athletic Build)";
    const foot = player.preferred_foot || "ขวา (Right)";

    // 1. Photo 1 (Official Portrait)
    const photo1 = getPlayerPhotoUrl(player);
    list.push({
        url: photo1,
        caption: `👤 ภาพโปรไฟล์ทางการ (Official Portrait) — ${name}`
    });

    // 2. Photo 2 (In-Action / Secondary Match Photo)
    if (player.image_path_2) {
        const photo2 = "/" + player.image_path_2.replace(/^\/+/, "");
        list.push({
            url: photo2,
            caption: `⚡ ภาพถ่ายฟอร์มการเล่นในสนาม (Match Action / In-Game) — ${name}`
        });
    } else {
        list.push({
            url: photo1,
            caption: `🏃‍♂️ สัดส่วนร่างกาย: สูง ${h} cm • หนัก ${w} kg • ${body} • เท้าที่ถนัด: ${foot}`
        });
    }

    if (player.gallery_json) {
        try {
            const parsed = JSON.parse(player.gallery_json);
            if (Array.isArray(parsed) && parsed.length > 0) {
                parsed.forEach(item => {
                    if (item.url && !list.some(x => x.url === item.url)) {
                        list.push(item);
                    }
                });
            }
        } catch (e) {}
    }

    return list;
}

// ==================== INTERACTIVE SCOUTING CAROUSEL & PHOTO SLIDER ====================
function renderScoutingCarousel() {
    const wrapper = document.getElementById("scouting-carousel");
    if (!wrapper) return;

    const marketPlayers = getMarketPlayers();
    const list = currentFilteredPlayers.length > 0 ? currentFilteredPlayers : marketPlayers;
    if (!list || list.length === 0) {
        wrapper.classList.add("hidden");
        return;
    }
    wrapper.classList.remove("hidden");

    if (scoutingPlayerIndex >= list.length) scoutingPlayerIndex = 0;
    if (scoutingPlayerIndex < 0) scoutingPlayerIndex = list.length - 1;

    const p = list[scoutingPlayerIndex];
    const price = p.asking_price > 0 ? p.asking_price : p.estimated_value;

    document.getElementById("carousel-counter-badge").textContent = `นักเตะคนที่ ${scoutingPlayerIndex + 1} / ${list.length}`;
    document.getElementById("carousel-player-pos").textContent = p.main_position || "ST";
    document.getElementById("carousel-player-club").textContent = `🏟️ ${p.current_club || "Free Agent"}`;
    document.getElementById("carousel-player-price").textContent = formatEuro(price);
    document.getElementById("carousel-player-name").textContent = p.known_as || p.first_name;
    document.getElementById("carousel-player-fullname").textContent = `ชื่อเต็ม: ${p.first_name || p.known_as} • 🌍 สัญชาติ: ${p.nationality || "-"}`;

    document.getElementById("carousel-player-height").textContent = `${p.height_cm || 182} cm`;
    document.getElementById("carousel-player-weight").textContent = `${p.weight_kg || 76} kg`;
    document.getElementById("carousel-player-foot").textContent = p.preferred_foot || "ขวา (Right)";
    document.getElementById("carousel-player-body").textContent = p.body_type || "สมส่วน แข็งแกร่ง (Athletic Build)";
    document.getElementById("carousel-player-ovr").textContent = p.overall_rating || 80;
    document.getElementById("carousel-player-pot").textContent = p.potential || 85;

    // Action buttons inside carousel
    let actHtml = `
        <button type="button" class="btn-sm btn-blue" style="padding: 0 16px; height: 36px;" onclick="openPlayerDetail(${p.id})">
            🎬 เปิดดูข้อมูลเต็ม & จัดการวิดีโอ
        </button>
    `;
    if (currentUser && currentUser.role === "Club") {
        actHtml += `
            <button type="button" class="btn-sm btn-green" style="padding: 0 16px; height: 36px;" onclick="openOfferForm(${p.id})">
                💰 ยื่นข้อเสนอซื้อตัว
            </button>
        `;
    } else if (currentUser && (currentUser.role === "Admin" || currentUser.role === "Agent")) {
        actHtml += `
            <button type="button" class="btn-sm" style="padding: 0 16px; height: 36px; background: rgba(255,255,255,0.14); color: #FFFFFF;" onclick="openPlayerForm(${p.id})">
                ✏️ แก้ไขข้อมูลนักเตะ
            </button>
        `;
    }
    document.getElementById("carousel-action-buttons").innerHTML = actHtml;

    // Render Multi-Photo Slider for this player
    renderCarouselPhotoSlide(p);

    // Render Real Video in Carousel
    const vidEl = document.getElementById("carousel-video-player");
    const dlBtn = document.getElementById("carousel-download-video-btn");
    if (p.video_path) {
        const vUrl = "/" + p.video_path.replace(/^\/+/, "");
        if (vidEl.getAttribute("src") !== vUrl) {
            vidEl.src = vUrl;
            vidEl.play().catch(() => {});
        }
        dlBtn.href = `api.php?action=download_video&player_id=${p.id}`;
        dlBtn.setAttribute("download", `highlight_${(p.known_as || "player").replace(/\s+/g, "_")}.mp4`);
    }
}

function renderCarouselPhotoSlide(player) {
    const gallery = getPlayerGallery(player);
    if (carouselPhotoIndex >= gallery.length) carouselPhotoIndex = 0;
    if (carouselPhotoIndex < 0) carouselPhotoIndex = gallery.length - 1;

    const slide = gallery[carouselPhotoIndex];
    const imgEl = document.getElementById("carousel-active-photo");
    imgEl.src = slide.url;
    document.getElementById("carousel-photo-counter").textContent = `รูปที่ ${carouselPhotoIndex + 1}/${gallery.length}`;
    document.getElementById("carousel-photo-caption").textContent = slide.caption || "";

    const dotsEl = document.getElementById("carousel-photo-dots");
    dotsEl.innerHTML = gallery.map((_, idx) => `
        <span class="photo-dot ${idx === carouselPhotoIndex ? "active" : ""}" onclick="setCarouselPhoto(${idx})"></span>
    `).join("");
}

function slideScoutingPlayer(dir) {
    const marketPlayers = getMarketPlayers();
    const list = currentFilteredPlayers.length > 0 ? currentFilteredPlayers : marketPlayers;
    if (!list.length) return;
    scoutingPlayerIndex = (scoutingPlayerIndex + dir + list.length) % list.length;
    carouselPhotoIndex = 0;
    renderScoutingCarousel();
}

function slideCarouselPhoto(dir) {
    const marketPlayers = getMarketPlayers();
    const list = currentFilteredPlayers.length > 0 ? currentFilteredPlayers : marketPlayers;
    if (!list.length) return;
    const p = list[scoutingPlayerIndex];
    const gallery = getPlayerGallery(p);
    carouselPhotoIndex = (carouselPhotoIndex + dir + gallery.length) % gallery.length;
    renderCarouselPhotoSlide(p);
}

function setCarouselPhoto(idx) {
    carouselPhotoIndex = idx;
    const marketPlayers = getMarketPlayers();
    const list = currentFilteredPlayers.length > 0 ? currentFilteredPlayers : marketPlayers;
    if (!list.length) return;
    renderCarouselPhotoSlide(list[scoutingPlayerIndex]);
}

function renderPlayersGrid() {
    const searchInput = document.getElementById("admin-search-box") || document.getElementById("filter-search");
    const q = (searchInput ? searchInput.value : adminSearchQuery || "").trim().toLowerCase();
    const clubFilter = document.getElementById("filter-club") ? document.getElementById("filter-club").value : "ALL";
    const posFilter = document.getElementById("filter-pos") ? document.getElementById("filter-pos").value : "ALL";
    const myClubNameLower = getCurrentUserClubName().toLowerCase();

    // กฎตลาดซื้อขาย: หากเป็นสโมสร เช่น Real Madrid จะไม่แสดงนักเตะของ Real Madrid และชื่อสโมสรตัวเองในตลาดซื้อขาย
    const marketPlayers = getMarketPlayers();

    // เก็บรายการไอดีนักเตะที่ดีลปิดสำเร็จแล้ว
    const completedPlayerIds = new Set(
        (appData.offers || []).filter(o => o.status === "Completed").map(o => Number(o.player_id))
    );
    (appData.transfer_history || []).forEach(h => {
        if (h.player_id) completedPlayerIds.add(Number(h.player_id));
    });

    // เก็บชื่อสโมสรที่รอการอนุมัติเอกสารการเงิน
    const pendingClubNames = new Set(
        (appData.clubs || []).filter(c => c.verification_status === "Pending").map(c => (c.club_name || "").trim().toLowerCase())
    );

    const filtered = marketPlayers.filter(p => {
        const pClubLower = (p.current_club || "").trim().toLowerCase();
        if (myClubNameLower && pClubLower === myClubNameLower) {
            return false;
        }

        // กรองตามคำค้นหา (ID, ชื่อ, สโมสร, สัญชาติ, ตำแหน่ง)
        const matchQ = !q ||
            String(p.id).includes(q) ||
            (p.known_as && p.known_as.toLowerCase().includes(q)) ||
            (p.first_name && p.first_name.toLowerCase().includes(q)) ||
            (p.last_name && p.last_name.toLowerCase().includes(q)) ||
            (p.current_club && p.current_club.toLowerCase().includes(q)) ||
            (p.nationality && p.nationality.toLowerCase().includes(q)) ||
            (p.main_position && p.main_position.toLowerCase().includes(q));

        // กรองตามสโมสรและตำแหน่ง
        const matchClub = clubFilter === "ALL" || p.current_club === clubFilter;
        const matchPos = posFilter === "ALL" || p.main_position === posFilter;

        // กรองตามปุ่มสถานะใน Action Bar (ALL, AVAILABLE, NEGOTIATING, COMPLETED, PENDING_CLUB)
        let matchStatus = true;
        const avail = (p.availability_status || "").toLowerCase();
        if (activeAdminStatusFilter === "AVAILABLE") {
            matchStatus = !p.availability_status || avail.includes("พร้อม") || avail.includes("available");
        } else if (activeAdminStatusFilter === "NEGOTIATING") {
            matchStatus = avail.includes("เจรจา") || avail.includes("negotiating");
        } else if (activeAdminStatusFilter === "COMPLETED") {
            matchStatus = completedPlayerIds.has(Number(p.id));
        } else if (activeAdminStatusFilter === "PENDING_CLUB") {
            matchStatus = pendingClubNames.has(pClubLower);
        }

        return matchQ && matchClub && matchPos && matchStatus;
    });

    currentFilteredPlayers = filtered;
    scoutingPlayerIndex = 0;
    carouselPhotoIndex = 0;
    if (filtered.length > 0) {
        renderScoutingCarousel();
    } else {
        const wrapper = document.getElementById("scouting-carousel");
        if (wrapper) wrapper.classList.add("hidden");
    }

    const container = document.getElementById("players-grid");
    if (!container) return;

    if (filtered.length === 0) {
        container.innerHTML = `<div class="data-card" style="grid-column: 1 / -1; text-align: center; color: #64748B; padding: 40px 20px;">
            <div style="font-size: 36px; margin-bottom: 8px;">🔍</div>
            <div style="font-size: 16px; font-weight: 600; color: #1E293B;">ไม่พบข้อมูลนักฟุตบอลตามเงื่อนไขที่เลือก</div>
            <div style="font-size: 13px; color: #64748B; margin-top: 4px;">ลองเปลี่ยนตัวกรองสถานะ หรือล้างคำค้นหาเพื่อดูรายชื่อทั้งหมด</div>
        </div>`;
        return;
    }

    container.innerHTML = filtered.map(p => {
        const photoUrl = getPlayerPhotoUrl(p);
        const gallery = getPlayerGallery(p);
        const price = p.asking_price > 0 ? p.asking_price : p.estimated_value;
        const hasVideo = Boolean(p.video_path);
        const isCutout = photoUrl.includes("player_61") || (photoUrl.endsWith(".png") && !photoUrl.includes("wikimedia"));

        let actionsHtml = `
            <button class="btn-sm btn-blue" onclick="event.stopPropagation(); openPlayerDetail(${p.id})">🎬 ข้อมูล & วิดีโอ</button>
        `;
        if (currentUser.role === "Club") {
            actionsHtml += `
                <button class="btn-sm btn-green" onclick="event.stopPropagation(); openOfferForm(${p.id})">💰 ยื่นซื้อ</button>
            `;
        } else if (currentUser.role === "Admin" || currentUser.role === "Agent") {
            if (myClubNameLower) {
                actionsHtml += `
                    <button class="btn-sm btn-green" onclick="event.stopPropagation(); openOfferForm(${p.id})">💰 ยื่นซื้อ</button>
                `;
            }
            actionsHtml += `
                <button class="btn-sm btn-gray" style="color:#0F172A;" onclick="event.stopPropagation(); openPlayerForm(${p.id})">✏️ แก้ไข</button>
                <button class="btn-sm btn-red" onclick="event.stopPropagation(); deletePlayer(${p.id})">🗑️</button>
            `;
        }

        const watermarkClub = (p.current_club || p.known_as || "FOOTBALL").toUpperCase();
        const watermarkName = (p.known_as || p.first_name || "STAR").toUpperCase();
        const watermarkText = `${watermarkClub} • ${watermarkName} • ${watermarkClub}`;

        const pAgent = (appData.agents || []).find(a => Number(a.id) === Number(p.agent_id));
        const agentDisplayName = pAgent ? (pAgent.agency_name || pAgent.full_name || "Agent") : "อิสระ";

        return `
            <div class="player-card" onclick="openPlayerDetail(${p.id})">
                <!-- 1. Upper Orange Portrait Stage with Central Light Glow and Watermark (ตามภาพตัวอย่าง) -->
                <div class="player-orange-stage">
                    <span class="stage-watermark">${watermarkText}</span>

                    <div class="stage-badges-bar">
                        <span class="stage-pos-pill">${p.main_position || "ST"}</span>
                        <span class="stage-status-pill">${hasVideo ? "🎬 วิดีโอจริง" : "⚡ พร้อมลงสนาม"}</span>
                    </div>

                    <img class="player-stage-img ${isCutout ? 'is-cutout' : ''}" src="${photoUrl}" alt="${p.known_as}" onerror="this.src='/assets/default_player_card.png'">
                </div>

                <!-- 2. Lower Clean White Info Box (ตรงตามรูปภาพตัวอย่างเป๊ะๆ) -->
                <div class="player-orange-info">
                    <h3 class="orange-card-name" title="${p.known_as || p.first_name}">${p.known_as || p.first_name}</h3>
                    <p class="orange-card-role">ตำแหน่ง ${p.main_position || "ST"} • สโมสร ${p.current_club || "Free Agent"}</p>
                    <p class="orange-card-sub">สัญชาติ ${p.nationality || "-"} • 💼 ${escapeHtml(agentDisplayName)} • OVR: <strong>${p.overall_rating || 75}</strong> • ${formatEuro(price)}</p>

                    <div class="orange-card-actions" onclick="event.stopPropagation()">
                        ${actionsHtml}
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

// ==================== PLAYER DETAIL & HIGHLIGHT VIDEO SHOWCASE ====================
function renderDetailPhotoSlide(player) {
    const gallery = getPlayerGallery(player);
    if (detailPhotoIndex >= gallery.length) detailPhotoIndex = 0;
    if (detailPhotoIndex < 0) detailPhotoIndex = gallery.length - 1;

    const slide = gallery[detailPhotoIndex];
    document.getElementById("detail-player-img").src = slide.url;
    document.getElementById("detail-photo-counter").textContent = `รูปที่ ${detailPhotoIndex + 1}/${gallery.length}`;
    document.getElementById("detail-photo-caption").textContent = slide.caption || "";

    const detailWatermark = document.getElementById("detail-stage-watermark");
    if (detailWatermark) {
        const clubText = (player.current_club || player.known_as || "FOOTBALL").toUpperCase();
        const pText = (player.known_as || player.first_name || "STAR").toUpperCase();
        detailWatermark.textContent = `${clubText} • ${pText} • ${clubText}`;
    }

    const dotsEl = document.getElementById("detail-photo-dots");
    if (dotsEl) {
        dotsEl.innerHTML = gallery.map((_, idx) => `
            <span class="photo-dot ${idx === detailPhotoIndex ? "active" : ""}" onclick="setDetailPhoto(${idx})"></span>
        `).join("");
    }

    const btnTab1 = document.getElementById("btn-tab-photo-1");
    const btnTab2 = document.getElementById("btn-tab-photo-2");
    if (btnTab1) btnTab1.classList.toggle("active", detailPhotoIndex === 0);
    if (btnTab2) btnTab2.classList.toggle("active", detailPhotoIndex === 1);
}

function slideDetailPhoto(dir) {
    const p = appData.players.find(x => Number(x.id) === Number(currentDetailPlayerId));
    if (!p) return;
    const gallery = getPlayerGallery(p);
    detailPhotoIndex = (detailPhotoIndex + dir + gallery.length) % gallery.length;
    renderDetailPhotoSlide(p);
}

function setDetailPhoto(idx) {
    const p = appData.players.find(x => Number(x.id) === Number(currentDetailPlayerId));
    if (!p) return;
    detailPhotoIndex = idx;
    renderDetailPhotoSlide(p);
}

function slideDetailPlayer(dir) {
    let list = [];
    if (playerDetailOriginTab === "squad") {
        list = getSquadPlayersList();
    } else {
        const marketPlayers = getMarketPlayers();
        list = currentFilteredPlayers.length > 0 ? currentFilteredPlayers : marketPlayers;
    }
    if (!list.length) return;
    const curIdx = list.findIndex(x => Number(x.id) === Number(currentDetailPlayerId));
    const nextIdx = (curIdx + dir + list.length) % list.length;
    openPlayerDetail(list[nextIdx].id, playerDetailOriginTab);
}

function openPlayerDetail(playerId, originTab = null) {
    const p = appData.players.find(x => Number(x.id) === Number(playerId));
    if (!p) return;

    if (!originTab) {
        originTab = (!document.getElementById("tab-squad")?.classList.contains("hidden")) ? "squad" : "market";
    }
    playerDetailOriginTab = originTab;

    currentDetailPlayerId = p.id;
    detailPhotoIndex = 0;
    const panel = document.getElementById("player-detail-panel");
    if (!panel) return;

    // Attach panel inside the currently active tab: stay in My Club if opened from squad!
    if (originTab === "squad") {
        const squadRoster = document.getElementById("squad-roster-panel");
        if (squadRoster && panel.parentElement !== squadRoster.parentElement) {
            squadRoster.parentElement.insertBefore(panel, squadRoster);
        }
    } else {
        const marketGrid = document.getElementById("market-players-grid");
        if (marketGrid && panel.parentElement !== marketGrid.parentElement) {
            marketGrid.parentElement.insertBefore(panel, marketGrid);
        }
    }

    const price = p.asking_price > 0 ? p.asking_price : p.estimated_value;

    currentDetailAgentId = p.agent_id || 1;
    const agent = (appData.agents || []).find(a => Number(a.id) === Number(p.agent_id));
    const agentName = agent ? (agent.full_name || `${agent.first_name || ''} ${agent.last_name || ''}`.trim() + ` (${agent.agency_name || 'Agent'})`) : "อิสระ (Independent)";
    const detailAgentEl = document.getElementById("detail-player-agent");
    if (detailAgentEl) detailAgentEl.textContent = agentName;

    document.getElementById("detail-player-title").textContent = `🎬 โปรไฟล์นักฟุตบอล รูปร่างจริง & วิดีโอไฮไลท์: ${p.known_as || p.first_name}`;
    document.getElementById("detail-player-subtitle").textContent = `สโมสร: ${p.current_club || "Free Agent"} • เอเยนต์: ${agentName} • สัญชาติ: ${p.nationality || "-"} • สูง ${p.height_cm || 182} cm / หนัก ${p.weight_kg || 76} kg`;

    renderDetailPhotoSlide(p);

    document.getElementById("detail-player-pos").textContent = p.main_position || "ST";
    document.getElementById("detail-player-name").textContent = `${p.first_name || ""} (${p.known_as})`.trim();
    document.getElementById("detail-player-club").innerHTML = `${getClubBadgeIcon(p.current_club, 20)} ${escapeHtml(p.current_club || "Free Agent")}`;

    document.getElementById("detail-player-height").textContent = `${p.height_cm || 182} cm`;
    document.getElementById("detail-player-weight").textContent = `${p.weight_kg || 76} kg`;
    document.getElementById("detail-player-foot").textContent = p.preferred_foot || "ขวา (Right)";
    document.getElementById("detail-player-body").innerHTML = `<strong style="color:#FF6600;">🏃‍♂️ รูปร่าง:</strong> ${p.body_type || "สมส่วน แข็งแกร่ง (Athletic Build)"}`;

    document.getElementById("detail-player-ovr").textContent = p.overall_rating || 75;
    document.getElementById("detail-player-pot").textContent = p.potential || 80;
    document.getElementById("detail-player-nat").textContent = p.nationality || "-";
    document.getElementById("detail-player-price").textContent = `ราคาตลาด: ${formatEuro(price)}`;

    // Role buttons inside detail card
    const roleActions = document.getElementById("detail-role-actions");
    const myClubLower = getCurrentUserClubName().toLowerCase();
    const isMyPlayer = myClubLower && (p.current_club || "").trim().toLowerCase() === myClubLower;

    if (currentUser.role === "Club") {
        if (isMyPlayer) {
            roleActions.innerHTML = `<span class="status-pill status-Active">⚽ นักเตะในสังกัดสโมสรของคุณ</span>
            <button class="btn-sm btn-blue" onclick="openPlayerForm(${p.id}, '${originTab}')">✏️ แก้ไขข้อมูลนักเตะ</button>`;
        } else {
            roleActions.innerHTML = `<button class="btn-sm btn-green" onclick="openOfferForm(${p.id})">💰 ยื่นข้อเสนอซื้อตัว</button>`;
        }
    } else {
        roleActions.innerHTML = `<button class="btn-sm btn-blue" onclick="openPlayerForm(${p.id}, '${originTab}')">✏️ แก้ไขข้อมูลนักเตะ</button>`;
    }

    // Show/Hide Upload controls (Agent & Admin can upload video)
    const uploadControls = document.getElementById("detail-upload-controls");
    if (currentUser.role === "Agent" || currentUser.role === "Admin") {
        uploadControls.classList.remove("hidden");
    } else {
        uploadControls.classList.add("hidden");
    }

    // Setup Video Player / Tactical Highlight Canvas & Admin Download Link
    setupPlayerVideoStage(p);

    document.getElementById("detail-video-status-msg").classList.add("hidden");
    panel.classList.remove("hidden");
    panel.style.animation = "none";
    panel.offsetHeight; // force reflow
    panel.style.animation = "";
    panel.scrollIntoView({ behavior: "smooth", block: "center" });
}

function closePlayerDetail() {
    const panel = document.getElementById("player-detail-panel");
    if (panel) panel.classList.add("hidden");
    const vid = document.getElementById("detail-video-player");
    if (vid) vid.pause();
    if (highlightAnimId) {
        cancelAnimationFrame(highlightAnimId);
        highlightAnimId = null;
    }
}

function setupPlayerVideoStage(player) {
    const vidEl = document.getElementById("detail-video-player");
    const canvasEl = document.getElementById("detail-video-canvas");
    const badgeEl = document.getElementById("detail-video-badge");
    const downloadBtn = document.getElementById("btn-download-video");

    if (highlightAnimId) {
        cancelAnimationFrame(highlightAnimId);
        highlightAnimId = null;
    }

    if (player.video_path) {
        const videoUrl = "/" + player.video_path.replace(/^\/+/, "");
        vidEl.src = videoUrl;
        vidEl.classList.remove("hidden");
        canvasEl.classList.add("hidden");
        badgeEl.textContent = "✔️ อัปโหลดไฟล์วิดีโอไฮไลท์แล้ว";
        badgeEl.style.color = "#10B981";

        downloadBtn.href = `api.php?action=download_video&player_id=${player.id}`;
        downloadBtn.setAttribute("download", `highlight_${(player.known_as || "player").replace(/\s+/g, "_")}.mp4`);
        downloadBtn.onclick = null;
    } else {
        vidEl.pause();
        vidEl.removeAttribute("src");
        vidEl.classList.add("hidden");
        canvasEl.classList.remove("hidden");
        badgeEl.textContent = "🎥 ฟอร์มการเล่น (เอเยนต์สามารถอัปโหลดวิดีโอจริงได้)";
        badgeEl.style.color = "#FBBF24";

        startHighlightCanvasAnimation(canvasEl, player);

        downloadBtn.href = "#";
        downloadBtn.removeAttribute("download");
        downloadBtn.onclick = (e) => {
            e.preventDefault();
            generateAndUploadHighlightVideo(true);
        };
    }
}

function startHighlightCanvasAnimation(canvas, player) {
    const ctx = canvas.getContext("2d");
    let frame = 0;

    function drawFrame() {
        frame++;
        const w = canvas.width;
        const h = canvas.height;

        // Stadium Turf Background
        const grad = ctx.createLinearGradient(0, 0, w, h);
        grad.addColorStop(0, "#064E3B");
        grad.addColorStop(0.5, "#047857");
        grad.addColorStop(1, "#065F46");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);

        // Pitch lines
        ctx.strokeStyle = "rgba(255,255,255,0.28)";
        ctx.lineWidth = 2;
        ctx.strokeRect(24, 20, w - 48, h - 40);
        ctx.beginPath();
        ctx.moveTo(w / 2, 20);
        ctx.lineTo(w / 2, h - 20);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(w / 2, h / 2, 42, 0, Math.PI * 2);
        ctx.stroke();

        // Animated tactical run trajectory
        const t = (frame % 180) / 180;
        const px = 110 + t * (w - 230);
        const py = h / 2 + Math.sin(t * Math.PI * 3) * 55;

        // Trail
        ctx.strokeStyle = "#FF6600";
        ctx.lineWidth = 3;
        ctx.beginPath();
        for (let s = 0; s <= t; s += 0.02) {
            const tx = 110 + s * (w - 230);
            const ty = h / 2 + Math.sin(s * Math.PI * 3) * 55;
            if (s === 0) ctx.moveTo(tx, ty);
            else ctx.lineTo(tx, ty);
        }
        ctx.stroke();

        // Player Marker
        ctx.fillStyle = "#FF6600";
        ctx.beginPath();
        ctx.arc(px, py, 12, 0, Math.PI * 2);
        ctx.fill();

        // Ball
        ctx.fillStyle = "#FFFFFF";
        ctx.beginPath();
        ctx.arc(px + 15, py - 6, 5, 0, Math.PI * 2);
        ctx.fill();

        // Overlay HUD
        ctx.fillStyle = "rgba(9, 13, 22, 0.78)";
        ctx.fillRect(24, h - 72, w - 48, 44);
        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 15px Kanit, sans-serif";
        ctx.fillText(`🎬 HIGHLIGHT REEL: ${player.known_as || player.first_name} (${player.main_position || "ST"})`, 38, h - 45);
        ctx.fillStyle = "#EA580C";
        ctx.font = "13px Kanit, sans-serif";
        ctx.fillText(`OVR ${player.overall_rating || 80} | POT ${player.potential || 85} | ${player.current_club || "Free Agent"}`, 380, h - 45);

        highlightAnimId = requestAnimationFrame(drawFrame);
    }
    drawFrame();
}

async function handleDirectVideoUpload(input) {
    if (!input.files || !input.files[0] || !currentDetailPlayerId) return;
    const file = input.files[0];
    const msgEl = document.getElementById("detail-video-status-msg");
    msgEl.textContent = "⏳ กำลังอัปโหลดไฟล์วิดีโอไฮไลท์...";
    msgEl.style.color = "#EA580C";
    msgEl.classList.remove("hidden");

    try {
        const q = `api.php?action=upload_player_video&player_id=${encodeURIComponent(currentDetailPlayerId)}&filename=${encodeURIComponent(file.name)}`;
        const resp = await fetch(q, {
            method: "POST",
            headers: { "Content-Type": "application/octet-stream" },
            body: file
        });
        const res = await resp.json();
        if (res.ok) {
            msgEl.textContent = "✔️ อัปโหลดวิดีโอไฮไลท์เรียบร้อยแล้ว!";
            msgEl.style.color = "#10B981";
            input.value = "";
            await loadAllData();
            openPlayerDetail(currentDetailPlayerId);
        } else {
            msgEl.textContent = "⚠️ " + (res.error || "อัปโหลดไม่สำเร็จ");
            msgEl.style.color = "#EF4444";
        }
    } catch (err) {
        msgEl.textContent = "⚠️ อัปโหลดไม่สำเร็จ: " + err.message;
        msgEl.style.color = "#EF4444";
    }
}

async function generateAndUploadHighlightVideo(autoDownloadAfter = false) {
    if (!currentDetailPlayerId) return;
    const p = appData.players.find(x => Number(x.id) === Number(currentDetailPlayerId));
    if (!p) return;

    const msgEl = document.getElementById("detail-video-status-msg");
    msgEl.textContent = "⏳ กำลังเรนเดอร์และบันทึกไฟล์วิดีโอไฮไลท์...";
    msgEl.style.color = "#EA580C";
    msgEl.classList.remove("hidden");

    const canvas = document.getElementById("detail-video-canvas");
    canvas.classList.remove("hidden");
    startHighlightCanvasAnimation(canvas, p);

    if (typeof canvas.captureStream === "function" && typeof MediaRecorder !== "undefined") {
        const stream = canvas.captureStream(30);
        const recorder = new MediaRecorder(stream, { mimeType: "video/webm" });
        const chunks = [];
        recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
        recorder.onstop = async () => {
            const blob = new Blob(chunks, { type: "video/webm" });
            const q = `api.php?action=upload_player_video&player_id=${encodeURIComponent(p.id)}&filename=${encodeURIComponent(`highlight_${p.id}.webm`)}`;
            const resp = await fetch(q, {
                method: "POST",
                headers: { "Content-Type": "application/octet-stream" },
                body: blob
            });
            const res = await resp.json();
            if (res.ok) {
                msgEl.textContent = "✔️ สร้างและอัปโหลดไฟล์วิดีโอไฮไลท์สำเร็จ!";
                msgEl.style.color = "#10B981";
                await loadAllData();
                openPlayerDetail(p.id);
                if (autoDownloadAfter) {
                    window.location.href = `api.php?action=download_video&player_id=${p.id}`;
                }
            }
        };
        recorder.start();
        setTimeout(() => recorder.stop(), 1800);
    }
}

// ==================== PLAYER ADD / EDIT (WITH PHOTO & VIDEO UPLOAD) ====================
function populatePlayerClubSelect(selectedClub = "ครูคอมแต่ง") {
    const sel = document.getElementById("p-club");
    if (!sel) return;
    const clubsSet = new Set(["ครูคอมแต่ง"]);
    (appData.clubs || []).forEach(c => {
        if (c.club_name) clubsSet.add(c.club_name.trim());
    });
    (appData.players || []).forEach(p => {
        if (p.current_club && p.current_club !== "Free Agent") clubsSet.add(p.current_club.trim());
    });
    const sorted = Array.from(clubsSet).sort();
    sel.innerHTML = sorted.map(c => `<option value="${c}">${c}</option>`).join("") +
        `<option value="Free Agent">Free Agent (ไร้สังกัด)</option>`;

    if (selectedClub && (clubsSet.has(selectedClub) || selectedClub === "Free Agent")) {
        sel.value = selectedClub;
    } else if (sorted.length > 0) {
        sel.value = sorted[0];
    }
}

function populatePlayerAgentSelect(selectedAgentId = null) {
    const sel = document.getElementById("p-agent");
    if (!sel) return;
    const agents = appData.agents || [];
    if (agents.length === 0) {
        sel.innerHTML = `<option value="1">💼 Jorge Mendes (Gestifute)</option>`;
        return;
    }
    sel.innerHTML = agents.map(a => {
        const name = a.full_name || `${a.first_name || ''} ${a.last_name || ''}`.trim() || `Agent #${a.id}`;
        const agency = a.agency_name || "Agency";
        return `<option value="${a.id}">💼 ${escapeHtml(name)} (${escapeHtml(agency)})</option>`;
    }).join("");

    if (selectedAgentId && agents.some(a => Number(a.id) === Number(selectedAgentId))) {
        sel.value = selectedAgentId;
    } else if (agents.length > 0) {
        sel.value = agents[0].id;
    }
}

function openPlayerForm(playerId = null, originTab = null) {
    if (!originTab) {
        originTab = (!document.getElementById("tab-squad")?.classList.contains("hidden")) ? "squad" : "market";
    }
    playerFormOriginTab = originTab;

    // 1. รับประกันว่าแท็บเป้าหมาย (market หรือ squad) จะถูกเปิดใช้งานทันทีก่อนแสดงฟอร์ม
    switchDashboardTab(originTab);

    const panel = document.getElementById("player-form-panel");
    if (!panel) return;

    if (originTab === "squad") {
        const squadRoster = document.getElementById("squad-roster-panel");
        if (squadRoster && panel.parentElement !== squadRoster.parentElement) {
            squadRoster.parentElement.insertBefore(panel, squadRoster);
        }
    } else {
        const marketGrid = document.getElementById("market-players-grid");
        if (marketGrid && panel.parentElement !== marketGrid.parentElement) {
            marketGrid.parentElement.insertBefore(panel, marketGrid);
        }
    }

    const form = document.getElementById("player-crud-form");
    form.reset();
    pendingPlayerImageBase64 = "";
    pendingPlayerImageBase64_2 = "";
    pendingPlayerVideoBase64 = "";
    pendingPlayerVideoName = "";

    const prevBox1 = document.getElementById("p-image-preview-box");
    const prevImg1 = document.getElementById("p-image-preview-img");
    const prevBox2 = document.getElementById("p-image-preview-box-2");
    const prevImg2 = document.getElementById("p-image-preview-img-2");

    const isAdmin = currentUser && currentUser.role === "Admin";

    if (playerId) {
        const p = appData.players.find(x => Number(x.id) === Number(playerId));
        if (!p) return;
        document.getElementById("player-form-title").textContent = `✏️ แก้ไขข้อมูลนักเตะ: ${p.known_as || p.first_name}`;
        document.getElementById("edit-player-id").value = p.id;
        document.getElementById("p-first-name").value = p.first_name || "";
        document.getElementById("p-known-as").value = p.known_as || "";
        document.getElementById("p-nationality").value = p.nationality || "Spain";
        document.getElementById("p-position").value = p.main_position || "ST";

        if (p.image_path && prevBox1 && prevImg1) {
            prevImg1.src = "/" + p.image_path.replace(/^\/+/, "");
            prevBox1.classList.remove("hidden");
        } else if (prevBox1) {
            prevBox1.classList.add("hidden");
        }

        if (p.image_path_2 && prevBox2 && prevImg2) {
            prevImg2.src = "/" + p.image_path_2.replace(/^\/+/, "");
            prevBox2.classList.remove("hidden");
        } else if (prevBox2) {
            prevBox2.classList.add("hidden");
        }
        populatePlayerClubSelect(p.current_club || "Free Agent");
        const clubInput = document.getElementById("p-club");
        if (clubInput) {
            clubInput.disabled = (currentUser && currentUser.role === "Agent");
            clubInput.title = (currentUser && currentUser.role === "Agent") ? "การเปลี่ยนสังกัดต้องผ่านกระบวนการซื้อขายและอนุมัติดีลเท่านั้น" : "";
        }

        // แอดมินสามารถแก้ไขนักเตะย้ายสังกัดเอเยนต์ได้
        populatePlayerAgentSelect(p.agent_id);
        const agentInput = document.getElementById("p-agent");
        if (agentInput) {
            agentInput.disabled = !isAdmin;
            agentInput.title = isAdmin ? "แอดมินสามารถเปลี่ยนย้ายสังกัดเอเยนต์ให้นักเตะได้ทันที" : "เฉพาะผู้ดูแลระบบ (Admin) เท่านั้นที่สามารถเปลี่ยนสังกัดเอเยนต์ได้";
        }

        const availSel = document.getElementById("p-availability");
        if (availSel) availSel.value = p.availability_status || "พร้อมย้ายทีม (Available)";
        document.getElementById("p-ovr").value = p.overall_rating || 80;
        document.getElementById("p-pot").value = p.potential || 85;
        document.getElementById("p-value").value = p.estimated_value || 30000000;
        document.getElementById("p-asking").value = p.asking_price || p.estimated_value || 35000000;
    } else {
        document.getElementById("player-form-title").textContent = "➕ เพิ่มนักฟุตบอลใหม่";
        document.getElementById("edit-player-id").value = "";

        const clubInput = document.getElementById("p-club");
        if (currentUser && currentUser.role === "Club") {
            const userClub = getCurrentUserClubName() || "ครูคอมแต่ง";
            populatePlayerClubSelect(userClub);
            if (clubInput) {
                clubInput.value = userClub;
                clubInput.disabled = true;
                clubInput.title = "สโมสรเพิ่มนักเตะเข้าสังกัดของตนเอง";
            }
        } else if (currentUser && currentUser.role === "Agent") {
            populatePlayerClubSelect("Free Agent");
            if (clubInput) {
                clubInput.disabled = false;
                clubInput.title = "ระบุสโมสรปัจจุบันหรือ Free Agent";
            }
        } else {
            const defaultClub = (adminSelectedSquadClub || getCurrentUserClubName() || "ครูคอมแต่ง");
            populatePlayerClubSelect(defaultClub);
            if (clubInput) {
                clubInput.disabled = false;
                clubInput.title = "";
            }
        }

        const myAgent = getCurrentUserAgent();
        populatePlayerAgentSelect(myAgent ? myAgent.id : null);
        const agentInput = document.getElementById("p-agent");
        if (agentInput) {
            agentInput.disabled = !isAdmin;
            agentInput.title = isAdmin ? "แอดมินสามารถเลือกสังกัดเอเยนต์ให้นักเตะได้" : "";
        }

        const availSel = document.getElementById("p-availability");
        if (availSel) availSel.value = "พร้อมย้ายทีม (Available)";
        if (prevBox1) prevBox1.classList.add("hidden");
        if (prevBox2) prevBox2.classList.add("hidden");
    }

    panel.classList.remove("hidden");
    panel.scrollIntoView({ behavior: "smooth", block: "center" });
}

function closePlayerForm() {
    const panel = document.getElementById("player-form-panel");
    if (panel) panel.classList.add("hidden");
}

async function handlePlayerSave(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn ? submitBtn.innerHTML : "💾 บันทึกข้อมูลนักเตะ";
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = "⏳ กำลังบันทึกข้อมูลนักเตะ...";
    }

    const availSel = document.getElementById("p-availability");
    const agentSel = document.getElementById("p-agent");
    const isClub = currentUser && currentUser.role === "Club";
    const isAgent = currentUser && currentUser.role === "Agent";
    
    let clubVal = "Free Agent";
    if (isClub) {
        clubVal = getCurrentUserClubName() || "ครูคอมแต่ง";
    } else {
        const clubEl = document.getElementById("p-club");
        clubVal = (clubEl && clubEl.value) ? clubEl.value.trim() : (isAgent ? "Free Agent" : "ครูคอมแต่ง");
    }

    let agentIdVal = null;
    if (isAgent) {
        const myAgent = getCurrentUserAgent();
        agentIdVal = myAgent ? Number(myAgent.id) : (agentSel && agentSel.value ? Number(agentSel.value) : 1);
    } else {
        agentIdVal = agentSel && agentSel.value ? Number(agentSel.value) : null;
    }

    const payload = {
        id: document.getElementById("edit-player-id").value || null,
        actor_role: currentUser ? currentUser.role : "Admin",
        actor_user_id: currentUser ? currentUser.id : 1,
        agent_id: agentIdVal,
        first_name: document.getElementById("p-first-name").value.trim(),
        known_as: document.getElementById("p-known-as").value.trim(),
        nationality: document.getElementById("p-nationality").value.trim(),
        main_position: document.getElementById("p-position").value,
        current_club: clubVal,
        availability_status: availSel ? availSel.value : "พร้อมย้ายทีม (Available)",
        overall_rating: Number(document.getElementById("p-ovr").value) || 80,
        potential: Number(document.getElementById("p-pot").value) || 85,
        estimated_value: Number(document.getElementById("p-value").value) || 30000000,
        asking_price: Number(document.getElementById("p-asking").value) || 35000000,
        image_base64: pendingPlayerImageBase64,
        image_base64_2: pendingPlayerImageBase64_2,
        video_base64: pendingPlayerVideoBase64,
        video_filename: pendingPlayerVideoName
    };

    try {
        const res = await apiCall("save_player", payload);
        if (res.ok) {
            pendingPlayerImageBase64 = "";
            pendingPlayerImageBase64_2 = "";
            closePlayerForm();
            await loadAllData();
            showLiveToast("✅ บันทึกข้อมูลนักเตะสำเร็จ!", "อัปเดตข้อมูลและรูปภาพทั้ง 2 รูปเรียบร้อยแล้ว");
            if (playerFormOriginTab === "squad") {
                switchDashboardTab("squad");
                playerFormOriginTab = null;
            }
        } else {
            alert(res.error || "บันทึกข้อมูลไม่สำเร็จ");
        }
    } catch (err) {
        alert("เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์: " + (err.message || err));
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    }
}

async function deletePlayer(playerId) {
    if (!confirm("ต้องการลบนักฟุตบอลรายนี้ออกจากระบบใช่หรือไม่?")) return;
    const res = await apiCall("delete_player", { id: playerId });
    if (res.ok) {
        await loadAllData();
    }
}

// ==================== TRANSFER OFFERS (SINGLE-CLUB SCOPED + REAL EMAILS + GOOGLE DRIVE) ====================
function populateOfferClubScopeSelect() {
    const sel = document.getElementById("offer-club-scope-select");
    const box = document.getElementById("offer-club-scope-box");
    const titleEl = document.getElementById("offers-section-title");
    const badgeEl = document.getElementById("offers-scope-badge");
    if (!sel) return;

    const myClub = appData.my_club || (appData.clubs || []).find(c => Number(c.user_id) === Number(currentUser.id));
    const isAgent = currentUser && currentUser.role === "Agent";
    const isClub = currentUser && currentUser.role === "Club";

    if (isClub && myClub) {
        sel.innerHTML = `<option value="${myClub.club_name}">🏟️ ${myClub.club_name}</option>`;
        sel.value = myClub.club_name;
        if (box) box.classList.add("hidden");
        if (titleEl) titleEl.textContent = `🤝 รายการซื้อขายนักฟุตบอลของสโมสร ${myClub.club_name}`;
        if (badgeEl) badgeEl.textContent = "";
    } else if (isAgent) {
        // สำหรับเอเยนต์: ซ่อนกล่องเลือกสโมสร เพราะเอเยนต์ต้องดูดีลนักเตะในสังกัดทั้งหมดของตน
        if (box) box.classList.add("hidden");
        const myAgent = getCurrentUserAgent();
        const agentName = myAgent ? (myAgent.agency_name || myAgent.full_name) : "เอเยนต์";
        if (titleEl) titleEl.textContent = `🤝 ข้อเสนอซื้อขายและสัญญาในความดูแล (${agentName})`;
        if (badgeEl) badgeEl.textContent = "";
    } else {
        // สำหรับ Admin: ให้มีตัวเลือกดูทุกสโมสร (ALL) เป็นค่าเริ่มต้น
        if (box) box.classList.remove("hidden");
        const prevVal = sel.value || "ALL";
        const clubNames = Array.from(new Set((appData.clubs || []).map(c => c.club_name).filter(Boolean)));

        sel.innerHTML = `<option value="ALL">🌐 ดูข้อเสนอทั้งหมด (ทุกสโมสร)</option>` +
            clubNames.map(cn => `<option value="${cn}">🏟️ สโมสร ${cn}</option>`).join("");

        sel.value = (prevVal === "ALL" || clubNames.includes(prevVal)) ? prevVal : "ALL";

        const activeClub = sel.value;
        if (titleEl) {
            titleEl.textContent = activeClub === "ALL"
                ? "🤝 รายการซื้อขายและสัญญาภาพรวมทั้งหมด (Admin View)"
                : `🤝 รายการซื้อขายนักฟุตบอลสโมสร ${activeClub}`;
        }
        if (badgeEl) badgeEl.textContent = "";
    }
}

function openOfferForm(playerId) {
    // 1. สำคัญมาก: ปิดหน้าโปรไฟล์นักเตะลงก่อนทันที เพื่อไม่ให้ modal บังฟอร์มยื่นซื้อ
    closePlayerDetail();

    const p = (appData.players || []).find(x => Number(x.id) === Number(playerId));
    if (!p) return;
    document.getElementById("offer-player-id").value = p.id;
    document.getElementById("offer-panel-title").textContent = `💰 ยื่นข้อเสนอซื้อตัว: ${p.known_as} (ต้นสังกัด: ${p.current_club || "Free Agent"})`;
    document.getElementById("offer-amount").value = p.asking_price > 0 ? p.asking_price : p.estimated_value;

    const myClub = appData.my_club || (appData.clubs || []).find(c => Number(c.user_id) === Number(currentUser.id));
    const emInput = document.getElementById("offer-contact-email");
    if (emInput && !emInput.value) {
        emInput.value = (myClub && myClub.email) ? myClub.email : "transfers@realmadrid.com";
    }

    // 2. ถ้าไม่ได้อยู่ที่แท็บ market ให้สลับมาที่ market เพื่อแสดงฟอร์มทันที
    const marketTab = document.getElementById("tab-market");
    if (marketTab && marketTab.classList.contains("hidden")) {
        switchDashboardTab("market");
    }

    const panel = document.getElementById("offer-form-panel");
    if (panel) {
        panel.classList.remove("hidden");
        panel.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    showLiveToast("💰 เปิดฟอร์มยื่นซื้อตัวนักเตะ", `ระบุค่าตัวและค่าเหนื่อยสำหรับ ${p.known_as || p.first_name}`, false, "💰");
}

function closeOfferForm() {
    document.getElementById("offer-form-panel").classList.add("hidden");
}

async function handleSendOffer(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn ? submitBtn.innerHTML : "🚀 ส่งข้อเสนอและแจ้งเตือนทันที";
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = "⏳ กำลังส่งข้อเสนอซื้อตัว...";
    }

    const player_id = Number(document.getElementById("offer-player-id").value);
    const offer_amount = Number(document.getElementById("offer-amount").value);
    const wage_offer = Number(document.getElementById("offer-wage").value);
    const yearsEl = document.getElementById("offer-years");
    const contract_years = yearsEl ? Number(yearsEl.value || 4) : 4;
    const contact_email = (document.getElementById("offer-contact-email").value || "").trim();

    if (!contact_email) {
        alert("กรุณากรอกอีเมลติดต่อจริงสำหรับรับแจ้งผลดีลซื้อขาย");
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
        return;
    }

    const p = (appData.players || []).find(x => Number(x.id) === Number(player_id));
    const pName = p ? (p.known_as || p.first_name) : "นักเตะ";

    try {
        const res = await apiCall("create_offer", {
            user_id: currentUser.id,
            buyer_club_name: getCurrentUserClubName() || "Real Madrid",
            player_id,
            offer_amount,
            wage_offer,
            contract_years,
            contact_email
        });
        if (res.ok) {
            closeOfferForm();
            switchDashboardTab("offers");
            await loadAllData();
            // เด้งแจ้งเตือน Live Toast ทันที ไม่ต้องรีเฟรชหน้า!
            showLiveToast(
                "💰 ยื่นข้อเสนอซื้อตัวสำเร็จ!",
                `ยื่นซื้อ ${pName} มูลค่า ${formatEuro(offer_amount)} เรียบร้อยแล้ว (อัปเดตลงตารางทันที)`,
                false,
                "💰"
            );
        } else {
            alert(res.error || "ไม่สามารถส่งข้อเสนอได้");
        }
    } catch (err) {
        alert("เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์: " + (err.message || err));
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    }
}

function renderOffersTable() {
    const tbody = document.getElementById("offers-tbody");
    if (!tbody) return;
    const sel = document.getElementById("offer-club-scope-select");
    const myClub = appData.my_club || (appData.clubs || []).find(c => Number(c.user_id) === Number(currentUser.id));
    const isAgent = currentUser && currentUser.role === "Agent";
    const isClub = currentUser && currentUser.role === "Club";
    const isAdmin = currentUser && currentUser.role === "Admin";
    const myAgent = getCurrentUserAgent();

    let scopedOffers = appData.offers || [];

    if (isAgent) {
        // สำหรับเอเยนต์: แสดงเฉพาะดีลที่เกี่ยวข้องกับเอเยนต์คนนี้โดยตรง
        const aid = myAgent ? Number(myAgent.id) : null;
        const auid = currentUser ? Number(currentUser.id) : null;
        scopedOffers = (appData.offers || []).filter(o => {
            if (aid && (Number(o.agent_id) === aid || Number(o.player_agent_id) === aid)) return true;
            if (auid && Number(o.agent_user_id) === auid) return true;
            const p = (appData.players || []).find(x => Number(x.id) === Number(o.player_id));
            if (p && aid && Number(p.agent_id) === aid) return true;
            return false;
        });
        const titleEl = document.getElementById("offers-section-title");
        if (titleEl) titleEl.textContent = `🤝 ข้อเสนอซื้อขายและสัญญาในความดูแล (${myAgent ? (myAgent.agency_name || myAgent.full_name) : "เอเยนต์"})`;
    } else if (isClub && myClub) {
        const cLower = (myClub.club_name || "").trim().toLowerCase();
        scopedOffers = (appData.offers || []).filter(o => {
            const buyer = (o.club_name || "").trim().toLowerCase();
            const seller = (o.selling_club_name || o.selling_club || o.player_current_club || "").trim().toLowerCase();
            return buyer === cLower || seller === cLower;
        });
    } else {
        // Admin: ถ้าเลือก ALL ให้แสดงทั้งหมด ถ้าเลือกสโมสร ให้กรองตามสโมสรนั้น
        const targetClubName = (sel && sel.value) ? sel.value : "ALL";
        if (targetClubName !== "ALL") {
            const targetLower = targetClubName.trim().toLowerCase();
            scopedOffers = (appData.offers || []).filter(o => {
                const buyer = (o.club_name || "").trim().toLowerCase();
                const seller = (o.selling_club_name || o.selling_club || o.player_current_club || "").trim().toLowerCase();
                return buyer === targetLower || seller === targetLower;
            });
        }
    }

    if (scopedOffers.length === 0) {
        const msg = isAgent
            ? "ยังไม่มีข้อเสนอซื้อขายสำหรับนักเตะในความดูแลของคุณ"
            : "ยังไม่มีรายการซื้อขายในหมวดหมู่นี้";
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:#64748B; padding: 28px;">${msg}</td></tr>`;
        return;
    }

    const meanings = appData.status_meanings || {};
    tbody.innerHTML = scopedOffers.map(o => {
        const sellerClub = o.selling_club_name || o.selling_club || o.player_current_club || "Free Agent";
        const dealEmail = o.deal_email || o.contact_email || "transfers@realmadrid.com";
        const meaning = meanings[o.status] || o.status;
        const years = o.contract_years || 4;
        const isTerminal = ["Completed", "Rejected", "Cancelled", "Expired"].includes(o.status);

        let actButtons = `<button class="btn-table-action btn-blue" onclick="openNegotiationPanel(${o.id})">💬 เจรจา/ประวัติ</button>`;

        if (!isTerminal) {
            if (currentUser.role === "Agent" || currentUser.role === "Admin") {
                if (o.status === "Pending" || o.status === "Negotiating" || o.status === "Pending Agent") {
                    actButtons += `<button class="btn-table-action btn-green" onclick="updateOfferStatus(${o.id}, 'Accepted', this)">✅ ยอมรับ</button>`;
                }
            }
            if (o.status === "Accepted" || o.status === "Contract Pending" || o.status === "Agent Accepted") {
                actButtons += `<button class="btn-table-action" style="background:#8E44AD; color:#FFF;" onclick="updateOfferStatus(${o.id}, 'Pending Approval', this)">📝 ยืนยันสัญญา</button>`;
            }
            if (currentUser.role === "Admin" || o.status === "Pending Approval") {
                actButtons += `<button class="btn-table-action btn-green" onclick="updateOfferStatus(${o.id}, 'Completed', this)">👑 อนุมัติปิดดีล</button>`;
            }
            if (currentUser.role === "Club") {
                actButtons += `<button class="btn-table-action btn-red" onclick="updateOfferStatus(${o.id}, 'Cancelled', this)">🚫 ยกเลิก</button>`;
            } else {
                actButtons += `<button class="btn-table-action btn-red" onclick="updateOfferStatus(${o.id}, 'Rejected', this)">✖ ปฏิเสธ</button>`;
            }
        }

        return `
            <tr>
                <td style="font-weight:700; color:#64748B;">#${o.id}</td>
                <td><strong style="font-size:14px; color:#0F172A;">${o.player_name || "-"}</strong></td>
                <td><span style="font-weight:700; color:#0F172A;">🏟️ ${o.club_name || "-"}</span></td>
                <td><span style="color:#475569;">🏟️ ${sellerClub}</span></td>
                <td>
                    <div style="color:#059669; font-weight:800; font-size:14px; margin-bottom:2px;">${formatEuro(o.offer_amount)}</div>
                    <div style="font-size:11.5px; color:#64748B;">ค่าเหนื่อย ${formatEuro(o.wage_offer)}/wk • ${years} ปี</div>
                </td>
                <td>
                    <span style="color:#EA580C; font-size:12px; font-weight:600; display:inline-flex; align-items:center; gap:4px;">✉️ ${dealEmail}</span>
                </td>
                <td>
                    <span class="status-pill status-${(o.status || 'Pending').replace(/\s+/g, '_')}">${o.status}</span>
                    <div style="font-size:11px; color:#64748B; margin-top:3px; line-height:1.3;">${meaning}</div>
                </td>
                <td>
                    <div class="table-action-cell">
                        ${actButtons}
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

function openNegotiationPanel(offerId) {
    const o = appData.offers.find(x => Number(x.id) === Number(offerId));
    if (!o) return;
    const panel = document.getElementById("negotiation-panel");
    document.getElementById("neg-offer-id").value = o.id;
    document.getElementById("neg-panel-title").textContent = `💬 การเจรจาค่าตัว & สัญญา — ดีล #${o.id}: ${o.player_name} (${o.club_name})`;
    const meanings = appData.status_meanings || {};
    document.getElementById("neg-panel-subtitle").textContent = `สถานะปัจจุบัน: ${o.status} (${meanings[o.status] || ""})`;

    document.getElementById("neg-fee-input").value = o.offer_amount || 0;
    document.getElementById("neg-wage-input").value = o.wage_offer || 150000;
    document.getElementById("neg-years-input").value = o.contract_years || 4;
    document.getElementById("neg-notes-input").value = "";

    const rounds = (appData.negotiations || []).filter(n => Number(n.offer_id) === Number(o.id));
    const roundsEl = document.getElementById("neg-rounds-list");
    if (rounds.length === 0) {
        roundsEl.innerHTML = `<div style="font-size:12px; color:#64748B;">ยังไม่มีประวัติการต่อรองเพิ่มเติม</div>`;
    } else {
        roundsEl.innerHTML = rounds.map(r => `
            <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:10px 14px; font-size:13px;">
                <strong>รอบที่ ${r.round_no} (${r.proposer_role} — ${r.action_type}):</strong>
                ค่าตัว <strong style="color:#0071E3;">${formatEuro(r.proposed_fee)}</strong> |
                ค่าเหนื่อย <strong style="color:#10B981;">${formatEuro(r.proposed_wage)}/สัปดาห์</strong> |
                สัญญา <strong>${r.proposed_years || 4} ปี</strong>
                <div style="font-size:12px; color:#64748B; margin-top:2px;">📝 ${r.message || "-"} (${r.created_at || ""})</div>
            </div>
        `).join("");
    }

    const contract = (appData.contracts || []).find(c => Number(c.offer_id) === Number(o.id));
    const contractEl = document.getElementById("neg-contract-box");
    if (contract) {
        contractEl.innerHTML = `
            <div style="background:#EFF6FF; border:1px solid #93C5FD; border-radius:10px; padding:10px 14px; font-size:13px; color:#1D4ED8;">
                📄 <strong>ข้อมูลตารางสัญญา (Contracts Table):</strong> ค่าตัวที่ตกลง ${formatEuro(contract.agreed_fee)} • ค่าเหนื่อย ${formatEuro(contract.agreed_salary)}/wk • ระยะเวลา ${contract.contract_years} ปี • สถานะสัญญา: <strong>${contract.contract_status}</strong>
            </div>
        `;
    } else {
        contractEl.innerHTML = "";
    }

    panel.classList.remove("hidden");
    panel.scrollIntoView({ behavior: "smooth", block: "center" });
}

function closeNegotiationPanel() {
    document.getElementById("negotiation-panel").classList.add("hidden");
}

async function handleSubmitCounterOffer(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn ? submitBtn.innerHTML : "💬 ส่งราคาต่อรองใหม่ (Negotiating)";
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = "⏳ กำลังส่งราคาต่อรอง...";
    }

    const offer_id = Number(document.getElementById("neg-offer-id").value);
    const proposed_fee = Number(document.getElementById("neg-fee-input").value);
    const proposed_wage = Number(document.getElementById("neg-wage-input").value);
    const proposed_years = Number(document.getElementById("neg-years-input").value || 4);
    const notes = document.getElementById("neg-notes-input").value.trim();

    try {
        const res = await apiCall("negotiate_offer", {
            offer_id,
            actor_role: currentUser.role,
            neg_action: "counter",
            proposed_fee,
            proposed_wage,
            proposed_years,
            notes
        });
        if (res.ok) {
            await loadAllData();
            openNegotiationPanel(offer_id);
            showLiveToast("💬 ส่งข้อเสนอต่อรองสำเร็จ!", `เสนอค่าตัวใหม่ ${formatEuro(proposed_fee)} เรียบร้อยแล้ว (อัปเดตลงระบบทันที)`, false, "💬");
        } else {
            alert(res.error || "ไม่สามารถส่งข้อเสนอต่อรองได้");
        }
    } catch (err) {
        alert("เกิดข้อผิดพลาด: " + (err.message || err));
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    }
}

async function triggerNegotiationAction(negAction, btnElement = null) {
    let originalText = "";
    if (btnElement) {
        originalText = btnElement.innerHTML;
        btnElement.disabled = true;
        btnElement.innerHTML = "⏳ รอสักครู่...";
    }

    const offer_id = Number(document.getElementById("neg-offer-id").value);
    const notes = document.getElementById("neg-notes-input").value.trim();

    try {
        const res = await apiCall("negotiate_offer", {
            offer_id,
            actor_role: currentUser.role,
            neg_action: negAction,
            notes
        });
        if (res.ok) {
            await loadAllData();
            openNegotiationPanel(offer_id);
            if (negAction === "accept") {
                showLiveToast("✅ ยอมรับข้อเสนอสำเร็จ!", "สถานะข้อเสนอปรับเป็น Accepted (รอจัดทำสัญญา) แล้ว", false, "✅");
            } else if (negAction === "confirm_contract") {
                showLiveToast("📝 ยืนยันสัญญาสำเร็จ!", "ส่งดีลให้แอดมินพิจารณาอนุมัติเรียบร้อยแล้ว", false, "📝");
            } else if (negAction === "reject") {
                showLiveToast("✖ ปฏิเสธข้อเสนอแล้ว", "บันทึกลงระบบเรียบร้อยแล้ว", true, "✖");
            } else {
                showLiveToast("✔ ดำเนินการสำเร็จ", "อัปเดตสถานะการเจรจาเรียบร้อยแล้ว", false, "✔");
            }
        } else {
            alert(res.error || "ดำเนินการไม่สำเร็จ");
        }
    } catch (err) {
        alert("เกิดข้อผิดพลาด: " + (err.message || err));
    } finally {
        if (btnElement) {
            btnElement.disabled = false;
            btnElement.innerHTML = originalText;
        }
    }
}

// ==================== ADMIN SQUAD & CLUBS DIRECTORY (รูปที่ 4) ====================
function getClubBadgeEmoji(clubName = "") {
    const name = (clubName || "").toLowerCase();
    if (name.includes("madrid")) return "⚪";
    if (name.includes("barcelona")) return "🔵🔴";
    if (name.includes("manchester city") || name.includes("man city")) return "🩵";
    if (name.includes("arsenal")) return "🔴";
    if (name.includes("liverpool")) return "🔴";
    if (name.includes("dortmund")) return "🟡⚫";
    if (name.includes("bayern")) return "🔴⚪";
    if (name.includes("paris") || name.includes("psg")) return "🔵";
    if (name.includes("buriram")) return "⚡";
    if (name.includes("mongthong") || name.includes("muangthong")) return "🔴";
    if (name.includes("panompen")) return "🛡️";
    return "🏟️";
}

function getClubBadgeIcon(clubName = "", size = 20) {
    if (!clubName) return "🏟️";
    const cObj = (appData && appData.clubs)
        ? appData.clubs.find(x => (x.club_name || "").trim().toLowerCase() === (clubName || "").trim().toLowerCase())
        : null;
    if (cObj && cObj.logo_path) {
        const cleanPath = "/" + cObj.logo_path.replace(/^\/+/, "");
        return `<img src="${cleanPath}" class="club-logo-inline" style="width:${size}px; height:${size}px; object-fit:contain; border-radius:4px; vertical-align:middle; display:inline-block; margin-right:4px;" alt="${escapeHtml(clubName)}" onerror="this.onerror=null; this.src='/assets/logo.png'">`;
    }
    return getClubBadgeEmoji(clubName);
}

function formatEuroShort(num) {
    if (!num || isNaN(num)) return "€0";
    if (num >= 1000000000) return `€${(num / 1000000000).toFixed(1)}B`;
    if (num >= 1000000) return `€${(num / 1000000).toFixed(0)}M`;
    if (num >= 1000) return `€${(num / 1000).toFixed(0)}K`;
    return `€${num.toLocaleString()}`;
}

function renderAdminSquadClubsGrid() {
    const gridEl = document.getElementById("admin-squad-clubs-grid");
    if (!gridEl) return;

    const searchInput = document.getElementById("admin-squad-club-search");
    const query = (searchInput ? searchInput.value : "").trim().toLowerCase();

    // Collect all registered & player clubs
    const clubMap = new Map();

    (appData.clubs || []).forEach(c => {
        const cname = (c.club_name || c.name || "").trim();
        if (cname && !clubMap.has(cname.toLowerCase())) {
            clubMap.set(cname.toLowerCase(), {
                name: cname,
                league: c.league || "First Division",
                country: c.country || "International",
                stadium: c.stadium || "Main Stadium"
            });
        }
    });

    (appData.players || []).forEach(p => {
        const cname = (p.current_club || "").trim();
        if (cname && cname !== "Free Agent" && !clubMap.has(cname.toLowerCase())) {
            clubMap.set(cname.toLowerCase(), {
                name: cname,
                league: "International League",
                country: p.nationality || "International",
                stadium: "Home Ground"
            });
        }
    });

    if (!clubMap.has("real madrid")) {
        clubMap.set("real madrid", {
            name: "Real Madrid",
            league: "La Liga",
            country: "Spain",
            stadium: "Santiago Bernabéu"
        });
    }

    let clubsList = Array.from(clubMap.values());

    if (query) {
        clubsList = clubsList.filter(c => 
            c.name.toLowerCase().includes(query) ||
            c.league.toLowerCase().includes(query) ||
            c.country.toLowerCase().includes(query)
        );
    }

    clubsList.sort((a, b) => a.name.localeCompare(b.name));

    if (clubsList.length === 0) {
        gridEl.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: #64748B; padding: 24px;">ไม่พบสโมสรที่ค้นหา "${escapeHtml(query)}"</div>`;
        return;
    }

    gridEl.innerHTML = clubsList.map(c => {
        const squad = (appData.players || []).filter(p => (p.current_club || "").trim().toLowerCase() === c.name.toLowerCase());
        const count = squad.length;
        const totalVal = squad.reduce((sum, p) => sum + (Number(p.estimated_value) || 0), 0);
        const avgOvr = count > 0 ? Math.round(squad.reduce((sum, p) => sum + (Number(p.overall_rating) || 80), 0) / count) : "-";
        const isActive = (adminSelectedSquadClub || "").trim().toLowerCase() === c.name.toLowerCase();
        const clubObj = (appData.clubs || []).find(x => (x.club_name || "").toLowerCase() === c.name.toLowerCase());
        const badgeHtml = (clubObj && clubObj.logo_path)
            ? `<img src="/${clubObj.logo_path.replace(/^\/+/, '')}" alt="" class="club-logo-badge" onerror="this.src='/assets/logo.png'">`
            : `<div style="font-size: 28px; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; background: #FFF7ED; border-radius: 10px; border: 1.5px solid #FED7AA;">${getClubBadgeEmoji(c.name)}</div>`;

        return `
            <div class="admin-squad-club-card ${isActive ? 'active' : ''}" onclick="selectAdminSquadClub('${escapeHtml(c.name)}')">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px; min-width: 0; flex: 1;">
                        ${badgeHtml}
                        <div style="min-width: 0; flex: 1;">
                            <h4 style="font-size: 15.5px; font-weight: 800; color: #0F172A; margin: 0; word-break: break-word; line-height: 1.3;">${escapeHtml(c.name)}</h4>
                            <span style="font-size: 11.5px; color: #64748B; font-weight: 500; word-break: break-word; display: block; margin-top: 2px;">${escapeHtml(c.league)} • ${escapeHtml(c.country)}</span>
                        </div>
                    </div>
                    ${isActive ? `<span style="background: #FF6600; color: #FFFFFF; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 999px; flex-shrink: 0; white-space: nowrap;">เลือกอยู่ ✓</span>` : ''}
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; background: #FFFDF9; border: 1px solid #FED7AA; border-radius: 12px; padding: 10px; margin-bottom: 14px; text-align: center;">
                    <div>
                        <div style="font-size: 10.5px; color: #64748B;">นักเตะ</div>
                        <div style="font-size: 15px; font-weight: 800; color: #EA580C;">${count} <span style="font-size: 11px;">คน</span></div>
                    </div>
                    <div>
                        <div style="font-size: 10.5px; color: #64748B;">พลังเฉลี่ย</div>
                        <div style="font-size: 15px; font-weight: 800; color: #0F172A;">${avgOvr}</div>
                    </div>
                    <div>
                        <div style="font-size: 10.5px; color: #64748B;">มูลค่าทีม</div>
                        <div style="font-size: 13px; font-weight: 800; color: #059669;">${formatEuroShort(totalVal)}</div>
                    </div>
                </div>
                <button type="button" class="btn-sm" style="width: 100%; height: 34px; border-radius: 999px; background: ${isActive ? '#FF6600' : '#FFF7ED'}; color: ${isActive ? '#FFFFFF' : '#EA580C'}; border: 1px solid #FED7AA; font-weight: 700;">
                    📋 ดูรายชื่อนักเตะ & จัดการ (${count} คน) ➔
                </button>
            </div>
        `;
    }).join("");
}

function selectAdminSquadClub(clubName) {
    adminSelectedSquadClub = clubName;
    renderAdminSquadClubsGrid();
    const sel = document.getElementById("squad-club-select");
    if (sel) sel.value = clubName;
    renderSquadTable();
    const rosterEl = document.getElementById("squad-roster-panel");
    if (rosterEl) {
        rosterEl.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function scrollToSquadClubs() {
    const clubsEl = document.getElementById("admin-squad-clubs-panel");
    if (clubsEl) {
        clubsEl.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function handleSquadClubChange(clubName) {
    adminSelectedSquadClub = clubName;
    renderAdminSquadClubsGrid();
    renderSquadTable();
}

function openPlayerFormForCurrentSquad() {
    if (currentUser && currentUser.role === "Agent") {
        openPlayerForm(null, "squad");
        const myAgent = getCurrentUserAgent();
        if (myAgent) {
            const selAgent = document.getElementById("p-agent");
            if (selAgent) selAgent.value = myAgent.id;
        }
    } else {
        const targetClub = (currentUser && currentUser.role === "Admin") ? (adminSelectedSquadClub || "ครูคอมแต่ง") : (getCurrentUserClubName() || "ครูคอมแต่ง");
        openPlayerForm(null, "squad");
        populatePlayerClubSelect(targetClub);
    }
}

let currentSquadViewMode = "cards";

function setSquadViewMode(mode) {
    currentSquadViewMode = mode;
    const cardsGrid = document.getElementById("squad-cards-grid");
    const tableContainer = document.getElementById("squad-table-container");
    const btnCards = document.getElementById("btn-squad-view-cards");
    const btnTable = document.getElementById("btn-squad-view-table");

    if (btnCards) btnCards.classList.toggle("active", mode === "cards");
    if (btnTable) btnTable.classList.toggle("active", mode === "table");

    if (mode === "cards") {
        if (cardsGrid) cardsGrid.classList.remove("hidden");
        if (tableContainer) tableContainer.classList.add("hidden");
    } else {
        if (cardsGrid) cardsGrid.classList.add("hidden");
        if (tableContainer) tableContainer.classList.remove("hidden");
    }
}

function getSquadPlayersList() {
    if (!currentUser) return [];
    const isAdmin = currentUser.role === "Admin";
    const isAgent = currentUser.role === "Agent";
    const myAgent = getCurrentUserAgent();

    // 1. ถ้าเป็นบทบาท AGENT: ให้ดึงเฉพาะนักเตะในสังกัดของเอเยนต์คนนี้เท่านั้น ไม่ต้องยึดสโมสร!
    if (isAgent) {
        if (myAgent) {
            return (appData.players || []).filter(p => Number(p.agent_id) === Number(myAgent.id));
        }
        const byUid = (appData.agents || []).find(a => Number(a.user_id) === Number(currentUser.id));
        if (byUid) {
            return (appData.players || []).filter(p => Number(p.agent_id) === Number(byUid.id));
        }
        return [];
    }

    // 2. ถ้าเป็น ADMIN: ให้ดึงตามสโมสรที่เลือกใน Dropdown
    if (isAdmin) {
        const selectedClub = adminSelectedSquadClub || "ครูคอมแต่ง";
        return (appData.players || []).filter(p => (p.current_club || "").trim().toLowerCase() === selectedClub.toLowerCase());
    }

    // 3. ถ้าเป็น CLUB: ดึงตามสโมสรของบัญชีตัวเอง
    const activeClubName = getCurrentUserClubName();
    if (activeClubName) {
        return (appData.players || []).filter(p => (p.current_club || "").trim().toLowerCase() === activeClubName.toLowerCase());
    }
    return appData.players || [];
}

function renderSquadCards(list) {
    const grid = document.getElementById("squad-cards-grid");
    if (!grid) return;

    if (!list || list.length === 0) {
        const isAgent = currentUser && currentUser.role === "Agent";
        const myAgent = getCurrentUserAgent();
        const agentName = myAgent ? (myAgent.agency_name || myAgent.full_name) : "ของคุณ";
        const clubTarget = (currentUser && currentUser.role === "Admin")
            ? (adminSelectedSquadClub || "สโมสรนี้")
            : (getCurrentUserClubName() || "สโมสรนี้");

        const emptyTitle = isAgent ? `ยังไม่มีนักเตะในความดูแลของเอเยนต์ (${escapeHtml(agentName)})` : `ไม่พบนักฟุตบอลในสังกัด ${escapeHtml(clubTarget)}`;
        const emptySub = isAgent ? `คุณยังไม่ได้เพิ่มนักเตะในสังกัดตัวแทน คลิกปุ่มด้านล่างเพื่อเริ่มสร้างประวัตินักเตะใหม่` : `ยังไม่มีข้อมูลนักฟุตบอลที่ลงทะเบียนในสโมสรนี้`;
        const addBtnText = isAgent ? `➕ เพิ่มนักเตะคนแรกในสังกัดเอเยนต์` : `➕ เพิ่มนักเตะคนแรกเข้าสโมสรนี้`;

        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; color: #64748B; padding: 48px 20px; background: #FFFDF9; border-radius: 18px; border: 1.5px dashed #FED7AA;">
                <div style="font-size: 38px; margin-bottom: 10px;">${isAgent ? "💼" : "📋"}</div>
                <div style="font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 6px;">${emptyTitle}</div>
                <p style="font-size: 13px; color: #64748B; margin-bottom: 16px;">${emptySub}</p>
                ${(currentUser && (currentUser.role === "Admin" || currentUser.role === "Club" || currentUser.role === "Agent")) ? `<button type="button" class="btn-sm btn-blue" style="height: 38px; padding: 0 20px; display: inline-flex; align-items: center; gap: 6px;" onclick="openPlayerFormForCurrentSquad()">${addBtnText}</button>` : ''}
            </div>
        `;
        return;
    }

    const canEdit = currentUser && (currentUser.role === "Admin" || currentUser.role === "Agent" || currentUser.role === "Club");
    const isAdmin = currentUser && currentUser.role === "Admin";

    grid.innerHTML = list.map(p => {
        const photoUrl = getPlayerPhotoUrl(p);
        const avail = p.availability_status || "พร้อมย้ายทีม (Available)";
        const hasVideo = Boolean(p.video_path);
        const isCutout = photoUrl.includes("player_61") || (photoUrl.endsWith(".png") && !photoUrl.includes("wikimedia"));

        const watermarkClub = (p.current_club || p.known_as || "FOOTBALL").toUpperCase();
        const watermarkName = (p.known_as || p.first_name || "STAR").toUpperCase();
        const watermarkText = `${watermarkClub} • ${watermarkName} • ${watermarkClub}`;

        const pAgent = (appData.agents || []).find(a => Number(a.id) === Number(p.agent_id));
        const agentDisplayName = pAgent ? (pAgent.agency_name || pAgent.full_name || "Agent") : "อิสระ";

        return `
            <div class="player-card squad-player-card" onclick="openPlayerDetail(${p.id}, 'squad')" title="คลิกการ์ดนี้เพื่อดูโปรไฟล์และวิดีโอของ ${escapeHtml(p.known_as || p.first_name)}">
                <!-- 1. Upper Orange Portrait Stage -->
                <div class="player-orange-stage">
                    <span class="stage-watermark">${watermarkText}</span>

                    <div class="stage-badges-bar">
                        <span class="stage-pos-pill" style="font-weight: 800;">${escapeHtml(p.main_position || "ST")}</span>
                        ${p.image_path_2 ? '<span class="stage-photo-count-pill" title="นักเตะคนนี้มี 2 รูปภาพ">📸 2 รูป</span>' : ''}
                        <span class="stage-status-pill">${hasVideo ? "🎬 วิดีโอจริง" : "⚡ พร้อมลงสนาม"}</span>
                    </div>

                    <img class="player-stage-img ${isCutout ? 'is-cutout' : ''}" src="${photoUrl}" alt="${escapeHtml(p.known_as)}" onerror="this.src='/assets/players/player_1.png'">

                    <div style="position: absolute; bottom: 8px; left: 12px; z-index: 2; background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(4px); color: #FFF; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; border: 1px solid rgba(254, 215, 170, 0.4);">
                        #${p.id}
                    </div>
                </div>

                <!-- 2. Lower Clean Info Box -->
                <div class="player-orange-info" style="padding: 16px 18px 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                        <div style="min-width: 0; flex: 1;">
                            <h3 class="orange-card-name" style="margin: 0; font-size: 16px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(p.known_as || p.first_name)}">
                                ${escapeHtml(p.known_as || p.first_name)}
                            </h3>
                            <small style="color: #64748B; font-size: 12px; font-weight: 500; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                ${escapeHtml(p.first_name || "")}
                            </small>
                        </div>
                        <div style="text-align: right; flex-shrink: 0;">
                            <span style="font-size: 10px; font-weight: 700; color: #64748B; display: block; text-transform: uppercase;">OVR</span>
                            <span style="font-size: 18px; font-weight: 900; color: #EA580C; line-height: 1;">${p.overall_rating || 75}</span>
                        </div>
                    </div>

                    <p class="orange-card-role" style="font-size: 12.5px; color: #334155; margin-bottom: 4px; display: flex; align-items: center; gap: 4px;">
                        <span>${getClubBadgeIcon(p.current_club)}</span>
                        <strong style="color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(p.current_club || "Free Agent")}</strong>
                        <span style="color: #94A3B8;">•</span>
                        <span>${escapeHtml(p.nationality || "-")}</span>
                    </p>

                    <div style="font-size: 11.5px; color: #64748B; margin-bottom: 8px; display: flex; align-items: center; gap: 5px;">
                        <span style="color: #EA580C; font-weight: 700;">💼 เอเยนต์:</span>
                        <button type="button" onclick="event.stopPropagation(); openAgentProfile(${p.agent_id || 1})" style="background:none; border:none; color:#EA580C; font-weight:700; cursor:pointer; text-decoration:underline; padding:0; font-size:11.5px;">${escapeHtml(agentDisplayName)} ↗</button>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 6px 10px; background: #FFF7ED; border-radius: 10px; border: 1px solid #FED7AA;">
                        <span style="font-size: 11.5px; color: #9A3412; font-weight: 600;">มูลค่าประเมิน</span>
                        <strong style="font-size: 13.5px; color: #059669; font-weight: 800;">${formatEuro(p.estimated_value)}</strong>
                    </div>

                    <div style="margin-bottom: 12px;">
                        <span class="status-pill status-Active" style="font-size: 11px; padding: 3px 9px;">${escapeHtml(avail)}</span>
                    </div>

                    <div class="orange-card-actions" onclick="event.stopPropagation()" style="display: flex; gap: 6px;">
                        <button type="button" class="btn-sm btn-blue" style="flex: 1; height: 34px; font-size: 12px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; gap: 4px;" onclick="event.stopPropagation(); openPlayerDetail(${p.id}, 'squad')" title="ดูข้อมูลนักเตะและคลิปวิดีโอ">🎬 ข้อมูล & วิดีโอ</button>
                        ${canEdit ? `<button type="button" class="btn-sm btn-gray" style="color: #0F172A; height: 34px; font-size: 12px; font-weight: 700; padding: 0 12px;" onclick="event.stopPropagation(); openPlayerForm(${p.id}, 'squad')" title="แก้ไขข้อมูลนักเตะ">✏️ แก้ไข</button>` : ""}
                        ${isAdmin ? `<button type="button" class="btn-sm btn-red" style="height: 34px; width: 34px; padding: 0; display: inline-flex; align-items: center; justify-content: center; font-size: 13px;" onclick="event.stopPropagation(); deletePlayer(${p.id})" title="ลบนักเตะ">🗑️</button>` : ""}
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

function renderSquadTableRows(list) {
    const tbody = document.getElementById("squad-tbody");
    if (!tbody) return;

    if (!list || list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: #64748B; padding: 28px;">ไม่พบนักฟุตบอลในสังกัดนี้</td></tr>`;
        return;
    }

    const canEdit = currentUser && (currentUser.role === "Admin" || currentUser.role === "Agent" || currentUser.role === "Club");
    const isAdmin = currentUser && currentUser.role === "Admin";

    tbody.innerHTML = list.map(p => {
        const avail = p.availability_status || "พร้อมย้ายทีม (Available)";
        const photoSrc = getPlayerPhotoUrl(p);
        const pAgent = (appData.agents || []).find(a => Number(a.id) === Number(p.agent_id));
        const agentDisplayName = pAgent ? (pAgent.agency_name || pAgent.full_name || "Agent") : "อิสระ";

        return `
            <tr class="squad-player-row" onclick="openPlayerDetail(${p.id}, 'squad');" title="คลิกแถวนี้เพื่อดูโปรไฟล์และวิดีโอของ ${escapeHtml(p.known_as || p.first_name)}">
                <td style="font-weight: 700; color: #64748B;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <img src="${photoSrc}" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover; border: 1.5px solid #FED7AA; background: #FFF7ED;" onerror="this.src='/assets/players/player_1.png'">
                        <span>#${p.id}</span>
                    </div>
                </td>
                <td>
                    <strong style="font-size: 14px; color: #0F172A; display: block;">${escapeHtml(p.known_as || p.first_name)}</strong>
                    <small style="color: #64748B; font-size: 12px;">${escapeHtml(p.first_name || "")}</small>
                </td>
                <td><span class="stage-pos-pill" style="margin: 0; background: #FF6600; color: #FFF; font-weight: 700;">${escapeHtml(p.main_position || "ST")}</span></td>
                <td style="color: #334155; font-weight: 500;">${escapeHtml(p.nationality || "-")}</td>
                <td>
                    <strong style="color: #0F172A;">${getClubBadgeIcon(p.current_club)} ${escapeHtml(p.current_club || "Free Agent")}</strong>
                    <small style="color: #64748B; font-size: 11.5px; display: block; margin-top: 2px;">💼 <button type="button" onclick="event.stopPropagation(); openAgentProfile(${p.agent_id || 1})" style="background:none; border:none; color:#EA580C; font-weight:700; cursor:pointer; text-decoration:underline; padding:0; font-size:11.5px;">${escapeHtml(agentDisplayName)} ↗</button></small>
                </td>
                <td style="color: #EA580C; font-weight: 800; font-size: 15px;">${p.overall_rating || 80}</td>
                <td style="color: #059669; font-weight: 800; font-size: 14px;">${formatEuro(p.estimated_value)}</td>
                <td><span class="status-pill status-Active">${escapeHtml(avail)}</span></td>
                <td onclick="event.stopPropagation();">
                    <div class="table-action-cell">
                        <button type="button" class="btn-table-action" style="background: #FFF7ED; color: #EA580C; border: 1px solid #FED7AA;" onclick="event.stopPropagation(); openPlayerDetail(${p.id}, 'squad');" title="ดูข้อมูลนักเตะและคลิปวิดีโอ">🎬 วิดีโอ & โปรไฟล์</button>
                        ${canEdit ? `<button type="button" class="btn-table-action btn-blue" onclick="event.stopPropagation(); openPlayerForm(${p.id}, 'squad');" title="แก้ไขข้อมูลนักเตะ">✏️ แก้ไขข้อมูล</button>` : ""}
                        ${isAdmin ? `<button type="button" class="btn-table-action" style="background: #FEE2E2; color: #DC2626; border: none;" onclick="event.stopPropagation(); deletePlayer(${p.id});" title="ลบนักเตะ">🗑️</button>` : ""}
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

function renderSquadTable() {
    const isAdmin = (currentUser && currentUser.role === "Admin");
    const isAgent = (currentUser && currentUser.role === "Agent");
    const isClub = (currentUser && currentUser.role === "Club");
    const activeClubName = getCurrentUserClubName();
    const myAgent = getCurrentUserAgent();

    // ควบคุมการแสดงผลปุ่มโลโก้สโมสร: เอเยนต์ห้ามเห็นและห้ามแก้เด็ดขาด!
    const btnLogo = document.getElementById("btn-squad-upload-logo");
    if (btnLogo) {
        btnLogo.style.display = isAgent ? "none" : ((isAdmin || isClub) ? "inline-flex" : "none");
    }

    // สลับข้อความปุ่มเพิ่มนักเตะ
    const btnAdd = document.getElementById("btn-squad-add-player");
    if (btnAdd) {
        if (isAgent) {
            btnAdd.textContent = "➕ เพิ่มนักเตะในสังกัดเอเยนต์";
            btnAdd.style.display = "inline-flex";
        } else if (isAdmin || isClub) {
            btnAdd.textContent = "➕ เพิ่มนักเตะเข้าสโมสรนี้";
            btnAdd.style.display = "inline-flex";
        } else {
            btnAdd.style.display = "none";
        }
    }

    // Populate squad-club-select for Admin
    const squadSelect = document.getElementById("squad-club-select");
    const squadSelectBox = squadSelect ? squadSelect.closest(".admin-only") : null;
    if (squadSelectBox) {
        squadSelectBox.style.display = isAdmin ? "inline-flex" : "none";
    }

    if (squadSelect && isAdmin) {
        const clubsSet = new Set(["ครูคอมแต่ง"]);
        (appData.clubs || []).forEach(c => {
            if (c.club_name) clubsSet.add(c.club_name.trim());
        });
        (appData.players || []).forEach(p => {
            if (p.current_club && p.current_club !== "Free Agent") clubsSet.add(p.current_club.trim());
        });
        const sortedClubs = Array.from(clubsSet).sort();
        squadSelect.innerHTML = sortedClubs.map(c => `<option value="${escapeHtml(c)}">${getClubBadgeEmoji(c)} ${escapeHtml(c)}</option>`).join("");
        if (adminSelectedSquadClub && sortedClubs.includes(adminSelectedSquadClub)) {
            squadSelect.value = adminSelectedSquadClub;
        } else if (sortedClubs.includes("ครูคอมแต่ง")) {
            adminSelectedSquadClub = "ครูคอมแต่ง";
            squadSelect.value = adminSelectedSquadClub;
        } else if (sortedClubs.length > 0) {
            adminSelectedSquadClub = sortedClubs[0];
            squadSelect.value = adminSelectedSquadClub;
        }
    }

    const list = getSquadPlayersList();
    const titleEl = document.getElementById("squad-section-title");
    const subtitleEl = document.getElementById("squad-section-subtitle");

    if (isAdmin) {
        const selectedClub = adminSelectedSquadClub || "ครูคอมแต่ง";
        const cBadge = getClubBadgeIcon(selectedClub, 26);
        if (titleEl) titleEl.innerHTML = `${cBadge} การ์ดนักเตะสังกัด: <strong style="color: #EA580C;">${escapeHtml(selectedClub)}</strong> (${list.length} คน)`;
        if (subtitleEl) subtitleEl.textContent = `คลิกที่การ์ดนักเตะเพื่อดูโปรไฟล์และวิดีโอไฮไลท์ในหน้านี้ หรือคลิก ✏️ แก้ไขข้อมูลเพื่ออัปเดตสถิติ`;
    } else if (isAgent) {
        const agentName = myAgent ? (myAgent.agency_name || myAgent.full_name || `${myAgent.first_name || ''} ${myAgent.last_name || ''}`.trim()) : "เอเยนต์ของฉัน";
        if (titleEl) titleEl.innerHTML = `💼 การ์ดนักเตะในสังกัดเอเยนต์: <strong style="color: #EA580C;">${escapeHtml(agentName)}</strong> (${list.length} คน)`;
        if (subtitleEl) subtitleEl.textContent = `รายชื่อนักฟุตบอลทั้งหมดที่คุณเป็นตัวแทนดูแลสัญญาและสิทธิประโยชน์ทางการค้า`;
    } else if (activeClubName) {
        const cBadge = getClubBadgeIcon(activeClubName, 26);
        if (titleEl) titleEl.innerHTML = `${cBadge} การ์ดนักฟุตบอลในสังกัดสโมสร: <strong style="color: #EA580C;">${escapeHtml(activeClubName)}</strong> (${list.length} คน)`;
        if (subtitleEl) subtitleEl.textContent = `คลิกที่การ์ดนักเตะเพื่อดูโปรไฟล์และวิดีโอไฮไลท์ในหน้านี้ได้ทันที`;
    } else {
        if (titleEl) titleEl.textContent = `⚽ การ์ดนักฟุตบอลในระบบทั้งหมด (${list.length} คน)`;
        if (subtitleEl) subtitleEl.textContent = `คลิกที่การ์ดนักเตะเพื่อดูโปรไฟล์และวิดีโอไฮไลท์ในหน้านี้ได้ทันที`;
    }

    renderSquadCards(list);
    renderSquadTableRows(list);
    setSquadViewMode(currentSquadViewMode);
}

function renderHistoryTable() {
    const tbody = document.getElementById("history-tbody");
    if (!tbody) return;
    const list = appData.transfer_history || [];
    if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:#64748B; padding:20px;">ยังไม่มีประวัติการซื้อขายที่ปิดดีลแล้ว</td></tr>`;
        return;
    }
    tbody.innerHTML = list.map(h => `
        <tr>
            <td>#${h.id}</td>
            <td><strong>${h.player_name || "-"}</strong> (${h.main_position || "-"})</td>
            <td>🏟️ ${h.from_club || "Free Agent"}</td>
            <td><strong style="color:#10B981;">🏟️ ${h.to_club || "-"}</strong></td>
            <td style="color:#0071E3; font-weight:700;">${formatEuro(h.transfer_fee)}</td>
            <td>${formatEuro(h.agreed_wage)}/wk</td>
            <td><span class="status-pill status-Completed">${h.approved_by || "Admin"}</span></td>
            <td>${h.completed_at || "-"}</td>
        </tr>
    `).join("");
}

function renderClubEmailsTable() {
    const tbody = document.getElementById("club-emails-tbody");
    if (!tbody) return;
    if (!appData.emails || appData.emails.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#64748B;">ยังไม่มีประวัติการส่งอีเมล</td></tr>`;
        return;
    }
    tbody.innerHTML = appData.emails.slice(0, 15).map(em => `
        <tr>
            <td>${em.sent_at || "-"}</td>
            <td><strong>${em.recipient_name || "-"}</strong></td>
            <td style="color:#1B9AE5; font-weight:600;">${em.recipient_email}</td>
            <td>${em.subject}</td>
            <td><span class="status-pill status-Active">${em.status || "Sent"}</span></td>
        </tr>
    `).join("");
}

async function handleSendRealEmails(e) {
    e.preventDefault();
    const statusBox = document.getElementById("bulk-email-status");
    const rawEmails = document.getElementById("bulk-real-emails").value.trim();
    const customMsg = document.getElementById("bulk-custom-msg").value.trim();
    const smtpUser = document.getElementById("smtp-user-input").value.trim();
    const smtpPass = document.getElementById("smtp-pass-input").value.trim();
    const sel = document.getElementById("offer-club-scope-select");
    const myClub = appData.my_club || appData.clubs.find(c => Number(c.user_id) === Number(currentUser.id));
    const clubScope = (currentUser.role === "Club" && myClub) ? myClub.club_name : ((sel && sel.value) || "Real Madrid");

    statusBox.textContent = "⏳ กำลังส่งอีเมลไปยังรายชื่อผู้รับจริง...";
    statusBox.style.color = "#0284C7";
    statusBox.classList.remove("hidden");

    const res = await apiCall("send_bulk_test_email", {
        recipient_emails: rawEmails,
        club_scope: clubScope,
        custom_message: customMsg,
        smtp_user: smtpUser,
        smtp_pass: smtpPass
    });

    if (res.ok) {
        statusBox.textContent = `✔️ ส่งอีเมลสำเร็จไปยังผู้รับจริงจำนวน ${res.count} อีเมลเรียบร้อยแล้ว!`;
        statusBox.style.color = "#10B981";
        await loadAllData();
    } else {
        statusBox.textContent = `⚠️ ${res.error || "ส่งอีเมลไม่สำเร็จ"}`;
        statusBox.style.color = "#EF4444";
    }
}

let currentCompletedDealTargetClub = "";

async function updateOfferStatus(offerId, status, btnElement = null) {
    let originalText = "";
    if (btnElement) {
        originalText = btnElement.innerHTML;
        btnElement.disabled = true;
        btnElement.innerHTML = "⏳ รอสักครู่...";
    }

    try {
        const res = await apiCall("update_offer", {
            offer_id: offerId,
            status,
            actor_role: currentUser ? currentUser.role : "Admin"
        });
        if (res.ok) {
            // ดึงข้อมูลเดิมก่อน loadAllData
            const prevDeal = (appData.offers || []).find(x => Number(x.id) === Number(offerId));
            const pName = prevDeal ? (prevDeal.player_name || "นักเตะ") : "นักเตะ";

            await loadAllData();

            // เด้งแจ้งเตือน / Modal ทันที ไม่ต้องกด F5!
            if (status === "Completed") {
                showLiveToast(
                    "👑 อนุมัติปิดดีลสำเร็จ! (Deal Official)",
                    `การย้ายทีมของ ${pName} เข้าสู่สโมสรใหม่เสร็จสมบูรณ์แล้ว! ตารางและสถิติอัปเดตทันที`,
                    false,
                    "👑"
                );
                showDealCompletedModal(prevDeal);
            } else if (status === "Accepted") {
                showLiveToast(
                    "✅ ยอมรับข้อเสนอสำเร็จ!",
                    `ข้อเสนอสำหรับ ${pName} ถูกตอบรับแล้ว (สถานะ Accepted พร้อมทำสัญญา)`,
                    false,
                    "✅"
                );
            } else if (status === "Pending Approval") {
                showLiveToast(
                    "📝 ยืนยันสัญญาเรียบร้อย!",
                    `ส่งสัญญาของ ${pName} ให้ฝ่ายแอดมินพิจารณาอนุมัติขั้นสุดท้ายแล้ว`,
                    false,
                    "📝"
                );
            } else if (status === "Rejected") {
                showLiveToast(
                    "✖ ปฏิเสธข้อเสนอแล้ว",
                    `ปฏิเสธข้อเสนอซื้อตัว ${pName} เรียบร้อยแล้ว`,
                    true,
                    "✖"
                );
            } else if (status === "Cancelled") {
                showLiveToast(
                    "🚫 ยกเลิกข้อเสนอแล้ว",
                    `ยกเลิกข้อเสนอซื้อตัว ${pName} เรียบร้อยแล้ว`,
                    true,
                    "🚫"
                );
            } else {
                showLiveToast("✔ อัปเดตสถานะสำเร็จ", `สถานะปรับเป็น ${status} เรียบร้อยแล้ว`, false, "✔");
            }
        } else {
            alert(res.error || "อัปเดตสถานะดีลไม่สำเร็จ");
        }
    } catch (err) {
        alert("เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์: " + (err.message || err));
    } finally {
        if (btnElement) {
            btnElement.disabled = false;
            btnElement.innerHTML = originalText;
        }
    }
}

function showDealCompletedModal(deal) {
    if (!deal) return;
    playClickSound("success");
    const modal = document.getElementById("deal-completed-modal");
    if (!modal) return;

    const p = (appData.players || []).find(x => Number(x.id) === Number(deal.player_id));
    const pName = deal.player_name || (p ? (p.known_as || p.first_name) : "นักเตะ");
    const pPhoto = p ? getPlayerPhotoUrl(p) : "/assets/players/player_1.png";
    const fromClub = deal.selling_club_name || deal.selling_club || deal.player_current_club || "Free Agent";
    const toClub = deal.club_name || "สโมสรใหม่";

    currentCompletedDealTargetClub = toClub;

    const imgEl = document.getElementById("deal-modal-player-img");
    const nameEl = document.getElementById("deal-modal-player-name");
    const fromEl = document.getElementById("deal-modal-from-club");
    const toEl = document.getElementById("deal-modal-to-club");
    const feeEl = document.getElementById("deal-modal-fee");
    const wageEl = document.getElementById("deal-modal-wage");

    if (imgEl) imgEl.src = pPhoto;
    if (nameEl) nameEl.textContent = pName;
    if (fromEl) fromEl.textContent = fromClub;
    if (toEl) toEl.textContent = toClub;
    if (feeEl) feeEl.textContent = formatEuro(deal.offer_amount);
    if (wageEl) wageEl.textContent = `${formatEuro(deal.wage_offer)}/สัปดาห์`;

    modal.classList.remove("hidden");
    const card = modal.querySelector(".email-modal-card");
    if (card) {
        card.style.animation = "none";
        card.offsetHeight;
        card.style.animation = "";
    }
}

function closeDealCompletedModal() {
    const modal = document.getElementById("deal-completed-modal");
    if (modal) modal.classList.add("hidden");
}

function goToSquadFromDealModal() {
    closeDealCompletedModal();
    if (currentUser && currentUser.role === "Admin" && currentCompletedDealTargetClub) {
        adminSelectedSquadClub = currentCompletedDealTargetClub;
    }
    switchDashboardTab("squad");
}

// ==================== ADMIN: CLUB VERIFICATION & EMAILS ====================
function renderClubsTable() {
    const tbody = document.getElementById("clubs-tbody");
    if (!tbody) return;
    tbody.innerHTML = appData.clubs.map(c => {
        const st = c.verification_status || "Approved";
        const logoImg = c.logo_path 
            ? `<img src="/${c.logo_path.replace(/^\/+/, '')}" alt="" class="club-logo-inline" style="width:26px; height:26px; object-fit:contain; border-radius:6px; background:#fff; padding:2px; margin-right:8px;" onerror="this.src='/assets/logo.png'">`
            : `<span style="font-size: 20px; margin-right: 8px;">${getClubBadgeEmoji(c.club_name)}</span>`;
        return `
            <tr>
                <td>
                    <div style="display: flex; align-items: center;">
                        ${logoImg}
                        <strong>${escapeHtml(c.club_name)}</strong>
                    </div>
                </td>
                <td>${c.country || "International"}</td>
                <td>${c.email || "-"}</td>
                <td>${c.bank_name || "-"}</td>
                <td style="font-weight:700;">${formatEuro(c.budget)}</td>
                <td><span class="status-pill status-${st}">${st}</span></td>
                <td>
                    <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                        <button type="button" class="btn-sm btn-gray" style="padding:4px 10px; font-size:12px; color:#0F172A; font-weight:700;" onclick="openClubLogoModal(${c.id})" title="เปลี่ยนโลโก้สโมสร">🛡️ โลโก้</button>
                        <button type="button" class="btn-sm btn-green" style="padding:4px 10px;" onclick="verifyClub(${c.id}, 'Approved')">✔️ อนุมัติ & ส่งอีเมล</button>
                        <button type="button" class="btn-sm btn-red" style="padding:4px 10px;" onclick="verifyClub(${c.id}, 'Rejected')">✖ ปฏิเสธ & ส่งอีเมล</button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

async function verifyClub(clubId, decision) {
    let reason = "";
    if (decision === "Rejected") {
        reason = "เอกสารหลักฐานทางการเงินไม่ผ่านเกณฑ์การประเมินสภาพคล่องตามระเบียบ UEFA Financial Fair Play (FFP)";
    }

    const res = await apiCall("verify_club", { club_id: clubId, decision, reason });
    if (res.ok) {
        await loadAllData();
        if (res.email) {
            showEmailSentModal(res.email);
            showLiveToast(
                decision === "Rejected" ? "⚠️ ส่งอีเมลปฏิเสธสำเร็จ!" : "✅ ส่งอีเมลอนุมัติสำเร็จ!",
                `ส่งอีเมลแจ้งผลไปยัง ${res.email.recipient_email || "สโมสร"} เรียบร้อยแล้ว`,
                decision === "Rejected"
            );
        }
    } else {
        alert("เกิดข้อผิดพลาด: " + (res.error || "ไม่สามารถดำเนินการได้"));
    }
}

let currentActiveSentEmail = null;

function showEmailSentModal(email) {
    if (!email) return;
    currentActiveSentEmail = email;
    const modal = document.getElementById("email-sent-modal");
    if (!modal) return;

    const card = modal.querySelector(".email-modal-card");
    const isApproved = email.is_approved;

    if (card) {
        if (!isApproved) {
            card.classList.add("is-rejected");
        } else {
            card.classList.remove("is-rejected");
        }
    }

    const iconEl = document.getElementById("email-modal-icon");
    if (iconEl) iconEl.textContent = isApproved ? "✅" : "⚠️";

    const titleEl = document.getElementById("email-modal-title");
    if (titleEl) {
        titleEl.textContent = isApproved
            ? "อนุมัติ & ส่งอีเมลแจ้งสโมสรเรียบร้อยแล้ว!"
            : "ปฏิเสธ & ส่งอีเมลแจ้งสโมสรเรียบร้อยแล้ว!";
    }

    const subtitleEl = document.getElementById("email-modal-subtitle");
    if (subtitleEl) {
        subtitleEl.textContent = isApproved
            ? "ระบบได้ส่งอีเมลอนุมัติไปยังสโมสรเรียบร้อยแล้ว"
            : "ระบบได้ส่งอีเมลปฏิเสธไปยังสโมสรเรียบร้อยแล้ว (สโมสรสามารถกดปุ่ม Reply เพื่อตอบกลับหา footballbetatitle@gmail.com ได้ทันที)";
    }

    const decisionBadge = document.getElementById("email-modal-decision-badge");
    if (decisionBadge) {
        decisionBadge.className = isApproved ? "status-pill status-Approved" : "status-pill status-Rejected";
        decisionBadge.textContent = isApproved ? "✅ ผ่านการอนุมัติ (APPROVED)" : "❌ ไม่ผ่านการอนุมัติ (REJECTED)";
    }

    const clubNameEl = document.getElementById("email-modal-club-name");
    if (clubNameEl) clubNameEl.textContent = email.club_name || "-";

    const senderEl = document.getElementById("email-modal-sender");
    if (senderEl) senderEl.textContent = email.sender_email || "footballbetatitle@gmail.com";

    const recipEl = document.getElementById("email-modal-recipient");
    if (recipEl) recipEl.textContent = email.recipient_email || "-";

    const statusBadge = document.getElementById("email-modal-status-badge");
    if (statusBadge) statusBadge.textContent = `✔ ${email.delivery_status || "Sent & Logged"}`;

    const subjectEl = document.getElementById("email-modal-subject");
    if (subjectEl) subjectEl.textContent = email.subject || "-";

    const bodyEl = document.getElementById("email-modal-body");
    if (bodyEl) bodyEl.textContent = email.body || "-";

    modal.classList.remove("hidden");
    if (card) {
        card.style.animation = "none";
        card.offsetHeight; // trigger reflow for bounce effect
        card.style.animation = "";
    }
}

function openGmailCompose() {
    if (!currentActiveSentEmail) return;
    const to = encodeURIComponent(currentActiveSentEmail.recipient_email || "");
    const su = encodeURIComponent(currentActiveSentEmail.subject || "");
    const body = encodeURIComponent(currentActiveSentEmail.body || "");
    const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${to}&su=${su}&body=${body}`;
    window.open(gmailUrl, "_blank");
}

function openMailtoApp() {
    if (!currentActiveSentEmail) return;
    const to = encodeURIComponent(currentActiveSentEmail.recipient_email || "");
    const su = encodeURIComponent(currentActiveSentEmail.subject || "");
    const body = encodeURIComponent(currentActiveSentEmail.body || "");
    const mailtoUrl = `mailto:${to}?subject=${su}&body=${body}`;
    window.location.href = mailtoUrl;
}

function closeEmailSentModal(e) {
    if (e && e.target && e.target !== e.currentTarget && !e.target.classList.contains("btn-close-modal") && e.target.tagName !== "BUTTON") return;
    const modal = document.getElementById("email-sent-modal");
    if (modal) modal.classList.add("hidden");
}

function copyEmailContent() {
    const subj = document.getElementById("email-modal-subject")?.textContent || "";
    const to = document.getElementById("email-modal-recipient")?.textContent || "";
    const body = document.getElementById("email-modal-body")?.textContent || "";
    const fullText = `To: ${to}\nSubject: ${subj}\n\n${body}`;

    navigator.clipboard.writeText(fullText).then(() => {
        const btn = document.getElementById("btn-copy-email");
        if (btn) {
            const original = btn.textContent;
            btn.textContent = "✔ คัดลอกสำเร็จแล้ว!";
            setTimeout(() => { btn.textContent = original; }, 2000);
        }
    }).catch(() => {
        alert("คัดลอกข้อความอีเมลสำเร็จแล้ว");
    });
}

let liveToastTimer = null;
function showLiveToast(title, msg, isRejected = false, customIcon = null) {
    const toast = document.getElementById("live-toast-alert");
    if (!toast) return;

    const iconEl = document.getElementById("live-toast-icon");
    const titleEl = document.getElementById("live-toast-title");
    const msgEl = document.getElementById("live-toast-msg");

    if (iconEl) iconEl.textContent = customIcon || (isRejected ? "⚠️" : "✉️");
    if (titleEl) titleEl.textContent = title;
    if (msgEl) msgEl.textContent = msg;

    if (isRejected) {
        toast.classList.add("is-rejected");
    } else {
        toast.classList.remove("is-rejected");
    }

    toast.classList.remove("hidden");
    toast.style.animation = "none";
    toast.offsetHeight;
    toast.style.animation = "";

    if (liveToastTimer) clearTimeout(liveToastTimer);
    liveToastTimer = setTimeout(() => {
        toast.classList.add("hidden");
    }, 4500);
}

function renderEmailsTable() {
    const tbody = document.getElementById("emails-tbody");
    if (!appData.emails || appData.emails.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#64748B;">ยังไม่มีประวัติการส่งอีเมล</td></tr>`;
        return;
    }
    tbody.innerHTML = appData.emails.map(em => `
        <tr>
            <td>${em.sent_at || "-"}</td>
            <td><strong>${em.recipient_name || "-"}</strong></td>
            <td style="color:#1B9AE5;">${em.recipient_email}</td>
            <td>${em.subject}</td>
            <td><span class="status-pill status-Active">${em.status || "Sent"}</span></td>
        </tr>
    `).join("");
}

// ==================== ADMIN: USER MANAGEMENT (EDIT & DELETE) ====================
function renderUsersTable() {
    const tbody = document.getElementById("users-tbody");
    tbody.innerHTML = appData.users.map(u => `
        <tr>
            <td>#${u.id}</td>
            <td><strong>${u.username}</strong></td>
            <td>${u.role}</td>
            <td><span class="status-pill status-${u.status}">${u.status}</span></td>
            <td>
                <button class="btn-sm btn-blue" style="padding:4px 12px;" onclick="openUserEdit(${u.id})">✏️ แก้ไข</button>
                <button class="btn-sm btn-red" style="padding:4px 12px;" onclick="deleteUser(${u.id})">🗑️ ลบ</button>
            </td>
        </tr>
    `).join("");
}

function openUserEdit(userId) {
    const u = appData.users.find(x => Number(x.id) === Number(userId));
    if (!u) return;
    document.getElementById("edit-user-id").value = u.id;
    document.getElementById("edit-user-name").value = u.username;
    document.getElementById("edit-user-role").value = u.role;
    document.getElementById("edit-user-status").value = u.status || "Active";
    document.getElementById("edit-user-password").value = "";
    const panel = document.getElementById("user-edit-panel");
    panel.classList.remove("hidden");
    panel.scrollIntoView({ behavior: "smooth", block: "center" });
}

function closeUserEdit() {
    document.getElementById("user-edit-panel").classList.add("hidden");
}

async function handleSaveUser(e) {
    e.preventDefault();
    const res = await apiCall("save_user", {
        id: Number(document.getElementById("edit-user-id").value),
        username: document.getElementById("edit-user-name").value.trim(),
        role: document.getElementById("edit-user-role").value,
        status: document.getElementById("edit-user-status").value,
        password: document.getElementById("edit-user-password").value.trim()
    });
    if (res.ok) {
        closeUserEdit();
        await loadAllData();
    } else {
        alert(res.error || "แก้ไขผู้ใช้ไม่สำเร็จ");
    }
}

async function deleteUser(userId) {
    if (!confirm("ต้องการลบบัญชีผู้ใช้นี้ใช่หรือไม่?")) return;
    const res = await apiCall("delete_user", { id: userId });
    if (res.ok) {
        await loadAllData();
    }
}

// ==================== AGENT PROFILE SYSTEM (หน้าโปรไฟล์เอเยนต์) ====================
function openAgentProfile(agentId) {
    if (!appData.agents || appData.agents.length === 0) return;
    const agent = appData.agents.find(a => Number(a.id) === Number(agentId)) || appData.agents[0];
    if (!agent) return;
    currentViewingAgentId = agent.id;

    const modal = document.getElementById("agent-profile-modal");
    if (!modal) return;

    // Agent Avatar & Info
    const avatarEl = document.getElementById("agent-profile-avatar");
    const nameEl = document.getElementById("agent-profile-fullname");
    const agencyEl = document.getElementById("agent-profile-agency");
    const bioEl = document.getElementById("agent-profile-bio");
    const emailEl = document.getElementById("agent-profile-email");
    const phoneEl = document.getElementById("agent-profile-phone");
    const licEl = document.getElementById("agent-profile-license");
    const ctryEl = document.getElementById("agent-profile-country");

    const displayName = agent.full_name || `${agent.first_name || ""} ${agent.last_name || ""}`.trim() || "FIFA Agent";
    const agencyName = agent.agency_name || "อิสระ (Independent Agency)";
    const photoUrl = agent.photo_path ? "/" + agent.photo_path.replace(/^\/+/, "") : "/assets/players/player_1.png";

    if (avatarEl) avatarEl.src = photoUrl;
    if (nameEl) nameEl.textContent = displayName;
    if (agencyEl) agencyEl.textContent = `🏢 ${agencyName}`;
    if (bioEl) bioEl.textContent = agent.bio || `ตัวแทนนักฟุตบอลมาตรฐานสากล สังกัด ${agencyName} บริหารจัดการสัญญา สิทธิประโยชน์ และการเจรจาตลาดซื้อขายนักเตะอาชีพ`;
    if (emailEl) emailEl.textContent = agent.email || agent.contact || "agent@transfers.com";
    if (phoneEl) phoneEl.textContent = agent.phone || "+66 81-888-9999";
    if (licEl) licEl.textContent = agent.license_no || `FIFA-LIC-2026-00${agent.id}`;
    if (ctryEl) ctryEl.textContent = agent.country || "International";

    // Edit button permissions: allow this agent or admin
    const canEditAgent = currentUser && (
        currentUser.role === "Admin" ||
        (currentUser.role === "Agent" && (
            Number(currentUser.id) === Number(agent.user_id) ||
            (agent.email && currentUser.email && agent.email.toLowerCase() === currentUser.email.toLowerCase()) ||
            (currentUser.username && agent.full_name && agent.full_name.toLowerCase().includes(currentUser.username.toLowerCase())) ||
            Number(agent.id) === 1
        ))
    );
    const editBtn = document.getElementById("btn-edit-agent-profile");
    if (editBtn) editBtn.style.display = canEditAgent ? "inline-flex" : "none";

    const addPlayerBtn = document.getElementById("btn-agent-add-player");
    if (addPlayerBtn) addPlayerBtn.style.display = canEditAgent ? "inline-flex" : "none";

    // Managed Players Roster: ดึงเฉพาะนักเตะในสังกัดเอเยนต์คนนี้ ทั้งจาก agent.id และ agent.user_id
    const agentPlayers = (appData.players || []).filter(p => {
        if (Number(p.agent_id) === Number(agent.id)) return true;
        if (agent.user_id && Number(p.agent_id) === Number(agent.user_id)) return true;
        return false;
    });
    const totalVal = agentPlayers.reduce((sum, p) => sum + Number(p.estimated_value || p.asking_price || 0), 0);
    const avgOvr = agentPlayers.length > 0 ? Math.round(agentPlayers.reduce((sum, p) => sum + Number(p.overall_rating || 75), 0) / agentPlayers.length) : "-";

    const countEl = document.getElementById("agent-kpi-players-count");
    const valEl = document.getElementById("agent-kpi-total-val");
    const avgEl = document.getElementById("agent-kpi-avg-ovr");
    if (countEl) countEl.textContent = `${agentPlayers.length} คน`;
    if (valEl) valEl.textContent = formatEuro(totalVal);
    if (avgEl) avgEl.textContent = avgOvr !== "-" ? `${avgOvr} OVR` : "-";

    const grid = document.getElementById("agent-players-grid");
    if (grid) {
        if (agentPlayers.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; color: #64748B; padding: 36px 20px; background: rgba(255,255,255,0.02); border-radius: 14px; border: 1px dashed rgba(255,102,0,0.3);">
                    <div style="font-size: 32px; margin-bottom: 8px;">⚽</div>
                    <div style="font-size: 15px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;">ยังไม่มีนักเตะในความดูแล</div>
                    <p style="font-size: 12px; color: #94A3B8; margin-bottom: 12px;">เอเยนต์นี้ยังไม่ได้เพิ่มรายชื่อนักฟุตบอลเข้าสู่ระบบ</p>
                    ${canEditAgent ? `<button type="button" class="btn-sm btn-blue" onclick="addPlayerForCurrentAgent()">➕ เพิ่มนักเตะใหม่</button>` : ''}
                </div>
            `;
        } else {
            grid.innerHTML = agentPlayers.map(p => {
                const photoUrl = getPlayerPhotoUrl(p);
                const price = p.asking_price > 0 ? p.asking_price : p.estimated_value;
                return `
                    <div class="player-card agent-client-card" style="background: #0F172A; border: 1.5px solid rgba(234, 88, 12, 0.45); border-radius: 16px; overflow: hidden; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;" onclick="closeAgentProfile(); openPlayerDetail(${p.id});">
                        <!-- Upper Stage with 2-Photo Badge & OVR -->
                        <div class="player-orange-stage" style="height: 165px; position: relative;">
                            <div class="stage-badges-bar" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; z-index: 5;">
                                <span class="stage-pos-pill" style="font-weight: 800; font-size: 11.5px;">${escapeHtml(p.main_position || "ST")}</span>
                                <div style="display: flex; gap: 4px; align-items: center;">
                                    ${p.image_path_2 ? '<span class="stage-photo-count-pill" style="background: rgba(16, 185, 129, 0.9); color: #FFF; font-weight: 700; font-size: 11px; padding: 2px 8px; border-radius: 999px;">📸 2 รูป</span>' : ''}
                                    <span class="stage-status-pill" style="font-weight: 800; font-size: 11.5px; background: #EA580C; color: #FFF;">${p.overall_rating || 75} OVR</span>
                                </div>
                            </div>
                            <img class="player-stage-img" src="${photoUrl}" alt="${escapeHtml(p.known_as)}" onerror="this.src='/assets/default_player_card.png'" style="object-fit: cover;">
                            <div style="position: absolute; bottom: 8px; left: 10px; background: rgba(15, 23, 42, 0.85); color: #FED7AA; padding: 2px 8px; border-radius: 999px; font-size: 10.5px; font-weight: 700; border: 1px solid rgba(254, 215, 170, 0.3);">
                                สังกัด: ${escapeHtml(agencyName)}
                            </div>
                        </div>

                        <!-- Lower Info: เน้นความเป็นนักเตะในสังกัดเอเยนต์ ไม่ใช้การ์ดสโมสร -->
                        <div style="padding: 12px 14px 14px; background: #070A11; color: #FFFFFF;">
                            <h3 style="color: #FFFFFF; font-size: 15px; font-weight: 800; margin: 0 0 4px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(p.known_as || p.first_name)}</h3>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 11.5px;">
                                <span style="color: #94A3B8;">สัญชาติ ${escapeHtml(p.nationality || "International")}</span>
                                <span style="color: #60A5FA; font-weight: 600;">ศักยภาพ POT ${p.potential || 85}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px dashed rgba(255,255,255,0.12); padding-top: 8px;">
                                <div>
                                    <div style="font-size: 10px; color: #94A3B8; text-transform: uppercase;">มูลค่าสัญญา</div>
                                    <div style="font-size: 13px; font-weight: 800; color: #FF6600;">${formatEuro(price)}</div>
                                </div>
                                <span style="font-size: 11.5px; color: #FED7AA; font-weight: 700;">ดูโปรไฟล์ ➔</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join("");
        }
    }

    modal.classList.remove("hidden");
}

function closeAgentProfile() {
    const modal = document.getElementById("agent-profile-modal");
    if (modal) modal.classList.add("hidden");
}

function openCurrentAgentProfile() {
    let targetAid = 1;
    if (currentUser && currentUser.role === "Agent") {
        const myAgent = appData.my_agent || (appData.agents || []).find(a => Number(a.user_id) === Number(currentUser.id));
        if (myAgent) targetAid = myAgent.id;
    } else if (appData.agents && appData.agents.length > 0) {
        targetAid = appData.agents[0].id;
    }
    openAgentProfile(targetAid);
}

function addPlayerForCurrentAgent() {
    const aid = currentViewingAgentId || 1;
    closeAgentProfile();
    const targetTab = (currentUser && currentUser.role === "Agent") ? "squad" : "market";
    openPlayerForm(null, targetTab);
    const sel = document.getElementById("p-agent");
    if (sel) sel.value = aid;
}

function openEditAgentProfileModal(agentId = null) {
    const aid = agentId || currentViewingAgentId || 1;
    const agent = (appData.agents || []).find(a => Number(a.id) === Number(aid));
    if (!agent) return;

    // ซ่อนหน้าต่างโปรไฟล์เดิมก่อน เพื่อให้โฟกัสที่หน้าต่างแก้ไขหน้าเดียวอย่างชัดเจน (Single Focused Modal)
    const viewModal = document.getElementById("agent-profile-modal");
    if (viewModal) viewModal.classList.add("hidden");

    document.getElementById("edit-agent-id").value = agent.id;
    document.getElementById("edit-agent-firstname").value = agent.first_name || "";
    document.getElementById("edit-agent-lastname").value = agent.last_name || "";
    document.getElementById("edit-agent-agency").value = agent.agency_name || "";
    document.getElementById("edit-agent-email").value = agent.email || agent.contact || "";
    document.getElementById("edit-agent-phone").value = agent.phone || "";
    document.getElementById("edit-agent-license").value = agent.license_no || "";
    document.getElementById("edit-agent-country").value = agent.country || "International";
    document.getElementById("edit-agent-bio").value = agent.bio || "";

    pendingAgentPhotoBase64 = "";
    const prevBox = document.getElementById("edit-agent-photo-preview-box");
    const prevImg = document.getElementById("edit-agent-photo-preview");
    if (agent.photo_path && prevBox && prevImg) {
        prevImg.src = "/" + agent.photo_path.replace(/^\/+/, "");
        prevBox.classList.remove("hidden");
    } else if (prevBox) {
        prevBox.classList.add("hidden");
    }

    const modal = document.getElementById("agent-edit-profile-modal");
    if (modal) modal.classList.remove("hidden");
}

function closeEditAgentProfileModal() {
    const modal = document.getElementById("agent-edit-profile-modal");
    if (modal) modal.classList.add("hidden");

    // เมื่อปิดหรือยกเลิก ให้เปิดหน้าโปรไฟล์เอเยนต์เดิมกลับมาอย่างต่อเนื่อง
    if (currentViewingAgentId) {
        const viewModal = document.getElementById("agent-profile-modal");
        if (viewModal) viewModal.classList.remove("hidden");
    }
}

function handleAgentPhotoSelect(input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        pendingAgentPhotoBase64 = e.target.result;
        const prevBox = document.getElementById("edit-agent-photo-preview-box");
        const prevImg = document.getElementById("edit-agent-photo-preview");
        if (prevBox && prevImg) {
            prevImg.src = e.target.result;
            prevBox.classList.remove("hidden");
        }
    };
    reader.readAsDataURL(file);
}

async function handleSaveAgentProfile(e) {
    e.preventDefault();
    const aid = Number(document.getElementById("edit-agent-id").value);
    const payload = {
        agent_id: aid,
        first_name: document.getElementById("edit-agent-firstname").value.trim(),
        last_name: document.getElementById("edit-agent-lastname").value.trim(),
        agency_name: document.getElementById("edit-agent-agency").value.trim(),
        email: document.getElementById("edit-agent-email").value.trim(),
        phone: document.getElementById("edit-agent-phone").value.trim(),
        license_no: document.getElementById("edit-agent-license").value.trim(),
        country: document.getElementById("edit-agent-country").value.trim(),
        bio: document.getElementById("edit-agent-bio").value.trim(),
        photo_base64: pendingAgentPhotoBase64
    };

    const res = await apiCall("update_agent_profile", payload);
    if (res.ok) {
        const modal = document.getElementById("agent-edit-profile-modal");
        if (modal) modal.classList.add("hidden");
        await loadAllData();
        openAgentProfile(aid);
        showLiveToast("✅ บันทึกโปรไฟล์เอเยนต์สำเร็จ!", "ข้อมูลและรูปถ่ายตัวแทนได้รับการอัปเดตแล้ว", false, "✅");
    } else {
        alert(res.error || "ไม่สามารถบันทึกโปรไฟล์ได้");
    }
}

// ==================== CLUB LOGO SYSTEM (จัดการตราสโมสร) ====================
function handleClubLogoPreview(input, previewImgId) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        pendingClubLogoBase64 = e.target.result;
        const box = document.getElementById(previewImgId + "-box") || document.getElementById("reg-club-logo-preview-box");
        const img = document.getElementById(previewImgId);
        if (img) img.src = e.target.result;
        if (box) box.classList.remove("hidden");
    };
    reader.readAsDataURL(file);
}

function openClubLogoModal(targetCid = null) {
    if (currentUser && currentUser.role === "Agent") {
        alert("เอเยนต์ไม่มีสิทธิ์แก้ไขหรือเปลี่ยนแปลงโลโก้สโมสร");
        return;
    }
    const isAdmin = currentUser && currentUser.role === "Admin";
    const myClubName = getCurrentUserClubName();
    let club = null;

    if (targetCid) {
        club = (appData.clubs || []).find(c => Number(c.id) === Number(targetCid));
    } else if (isAdmin) {
        const selectedName = adminSelectedSquadClub || "ครูคอมแต่ง";
        club = (appData.clubs || []).find(c => (c.club_name || "").toLowerCase() === selectedName.toLowerCase()) || (appData.clubs || [])[0];
    } else {
        club = (appData.clubs || []).find(c => (c.club_name || "").toLowerCase() === (myClubName || "").toLowerCase()) || (appData.clubs || [])[0];
    }

    if (!club) {
        alert("ไม่พบข้อมูลสโมสรในระบบ");
        return;
    }

    // Populate select for Admin
    const selGroup = document.getElementById("club-logo-select-group");
    const sel = document.getElementById("club-logo-cid-select");
    if (selGroup && sel) {
        if (isAdmin) {
            selGroup.classList.remove("hidden");
            sel.innerHTML = (appData.clubs || []).map(c => `<option value="${c.id}" ${Number(c.id) === Number(club.id) ? "selected" : ""}>${escapeHtml(c.club_name)}</option>`).join("");
        } else {
            selGroup.classList.add("hidden");
        }
    }

    document.getElementById("club-logo-target-cid").value = club.id;
    document.getElementById("club-logo-target-name").textContent = club.club_name;
    const prevImg = document.getElementById("club-logo-current-preview");
    if (prevImg) {
        prevImg.src = club.logo_path ? "/" + club.logo_path.replace(/^\/+/, "") : "/assets/logo.png";
    }

    pendingEditClubLogoBase64 = "";
    const fileInput = document.getElementById("club-logo-file-input");
    if (fileInput) fileInput.value = "";

    const modal = document.getElementById("club-logo-modal");
    if (modal) modal.classList.remove("hidden");
}

function closeClubLogoModal() {
    const modal = document.getElementById("club-logo-modal");
    if (modal) modal.classList.add("hidden");
}

function handleClubLogoCidChange(cid) {
    const club = (appData.clubs || []).find(c => Number(c.id) === Number(cid));
    if (!club) return;
    document.getElementById("club-logo-target-cid").value = club.id;
    document.getElementById("club-logo-target-name").textContent = club.club_name;
    const prevImg = document.getElementById("club-logo-current-preview");
    if (prevImg) {
        prevImg.src = club.logo_path ? "/" + club.logo_path.replace(/^\/+/, "") : "/assets/logo.png";
    }
}

function handleClubLogoModalFile(input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        pendingEditClubLogoBase64 = e.target.result;
        const prevImg = document.getElementById("club-logo-current-preview");
        if (prevImg) prevImg.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

async function handleSaveClubLogo(e) {
    e.preventDefault();
    if (currentUser && currentUser.role === "Agent") {
        alert("เอเยนต์ไม่มีสิทธิ์แก้ไขหรือเปลี่ยนแปลงโลโก้สโมสร");
        return;
    }
    const cid = Number(document.getElementById("club-logo-target-cid").value);
    if (!cid) {
        alert("กรุณาเลือกสโมสร");
        return;
    }
    if (!pendingEditClubLogoBase64) {
        alert("กรุณาเลือกไฟล์รูปภาพโลโก้ใหม่");
        return;
    }

    const res = await apiCall("update_club_profile", {
        club_id: cid,
        logo_base64: pendingEditClubLogoBase64,
        role: currentUser ? currentUser.role : null,
        user_id: currentUser ? currentUser.id : null
    });

    if (res.ok) {
        closeClubLogoModal();
        await loadAllData();
        renderSquadTable();
        showLiveToast("🛡️ บันทึกโลโก้สโมสรสำเร็จ!", "ตราสโมสรได้รับการอัปเดตและแสดงผลทั่วทั้งระบบแล้ว");
    } else {
        alert(res.error || "ไม่สามารถบันทึกโลโก้สโมสรได้");
    }
}
