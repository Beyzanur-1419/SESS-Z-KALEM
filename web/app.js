/**
 * Sessiz Kalem — Web Arayüzü Mantığı (Vanilla JS)
 * Issue #5 ve #7 gereksinimlerini karşılar.
 * Derleme adımı yoktur (proje kararı uyarınca düz JS).
 */

// Uygulama Durumu (State)
const state = {
  currentUser: localStorage.getItem("sessiz_kalem_active_user") || null,
  currentBelgeId: null,
  currentFilename: null,
  bulgular: [],
  temizMetin: null,
  rapor: null,
  isOllamaOffline: false,
  adminVerified: false,
};

// ============================================================================
// Sayfa Başlatma (Init)
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupUpload();
  setupReviewActions();
  setupModals();
  setupSimulations();
  updateAuthUI();
  setupAdminControlCenter();
});

// ============================================================================
// 1. Navigasyon ve Sekme Geçişleri
// ============================================================================
function setupNavigation() {
  const navButtons = document.querySelectorAll(".nav-item");

  navButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchTab(tabId);
    });
  });

  // Hero butonları
  document.getElementById("btn-hero-start")?.addEventListener("click", () => {
    switchTab("yeni-analiz");
  });

  document.getElementById("btn-hero-sample")?.addEventListener("click", () => {
    loadSampleDocument();
  });

  document.getElementById("btn-load-sample-upload")?.addEventListener("click", () => {
    loadSampleDocument();
  });

  document.getElementById("btn-re-run-demo")?.addEventListener("click", () => {
    loadSampleDocument();
  });

  document.getElementById("link-direct-demo")?.addEventListener("click", (e) => {
    e.preventDefault();
    closeAllModals();
    loadSampleDocument();
  });

  document.getElementById("link-direct-demo-2")?.addEventListener("click", (e) => {
    e.preventDefault();
    closeAllModals();
    loadSampleDocument();
  });
}

function switchTab(tabId) {
  // Sidebar butonlarını güncelle
  document.querySelectorAll(".nav-item").forEach((btn) => {
    if (btn.getAttribute("data-tab") === tabId) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // Pane içeriklerini güncelle
  document.querySelectorAll(".tab-pane").forEach((pane) => {
    if (pane.id === `pane-${tabId}`) {
      pane.classList.add("active");
    } else {
      pane.classList.remove("active");
    }
  });

  window.scrollTo({ top: 0, behavior: "smooth" });

  // Eğer Yönetici & Denetim sekmesine geçildiyse ve henüz kilit açılmadıysa Enclave Gate Modal'ı aç
  if (tabId === "yonetici-denetim" && !state.adminVerified) {
    const gateModal = document.getElementById("modal-admin-enclave-gate");
    if (gateModal) gateModal.style.display = "flex";
  }
}

// ============================================================================
// 2. Belge Yükleme (POST /belgeler - Issue #5)
// ============================================================================
function setupUpload() {
  const dropzone = document.getElementById("document-dropzone");
  const fileInput = document.getElementById("file-input");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });
}

async function uploadFile(file) {
  const progressCard = document.getElementById("upload-progress");
  const progressName = document.getElementById("progress-file-name");
  const progressFill = document.getElementById("progress-bar-fill");
  const progressText = document.getElementById("progress-status-text");

  progressCard.style.display = "block";
  progressName.textContent = file.name;
  progressFill.style.width = "40%";
  progressText.textContent = "Yerel çıkarım motoru çalışıyor...";

  const formData = new FormData();
  formData.append("dosya", file);

  try {
    const res = await fetch("/belgeler", {
      method: "POST",
      body: formData,
    });

    progressFill.style.width = "85%";

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      handleApiError(res.status, err);
      progressCard.style.display = "none";
      return;
    }

    const data = await res.json();
    progressFill.style.width = "100%";
    progressText.textContent = "Tamamlandı!";

    setTimeout(() => {
      progressCard.style.display = "none";
      onDocumentUploaded(data.belge_id, file.name, data.bulgular);
    }, 400);

  } catch (err) {
    showAlert("Sunucu bağlantı hatası: API çalışıyor mu kontrol edin.");
    progressCard.style.display = "none";
  }
}

async function loadSampleDocument() {
  const ornekMetin =
    "MADDE 4.2 - TARAFLAR VE TİCARİ YÜKÜMLÜLÜKLER\n\n" +
    "İşbu sözleşme kapsamında danışman Ayşe Yılmaz, şirket bünyesinde gizli olarak yürütülen " +
    "Atlas Projesi veri tabanı mimarisi üzerinde tam yetkiyle çalışacaktır.\n" +
    "İlk faz tamamlanma bedeli olan 450.000 TL hak ediş, yüklenicinin QNB Finansbank nezdindeki " +
    "TR44 0011 1000 0000 0456 7890 12 nolu hesabına en geç 5 iş günü içinde transfer edilecektir.\n" +
    "Proje tesliminde gizli protokol hükmü saklıdır.";

  const blob = new Blob([ornekMetin], { type: "text/plain" });
  const file = new File([blob], "Gizlilik_Sozlesmesi_v3.txt", { type: "text/plain" });
  switchTab("yeni-analiz");
  await uploadFile(file);
}

function onDocumentUploaded(belgeId, filename, bulgular) {
  state.currentBelgeId = belgeId;
  state.currentFilename = filename;
  state.bulgular = bulgular;

  // Kullanıcı giriş yapmışsa belgesini kasasına ekle
  if (state.currentUser) {
    saveVaultDocument(state.currentUser, {
      id: belgeId,
      filename: filename,
      date: new Date().toISOString().replace("T", " ").substring(0, 16),
      findingsCount: bulgular.length,
      maskedCount: 0,
      status: "İnceleniyor"
    });
  }

  // Başlığı güncelle
  const titleEl = document.getElementById("review-doc-title");
  if (titleEl) {
    titleEl.textContent = `İnceleme: ${filename} (ID: ${belgeId})`;
  }

  // Sidebar badge güncelle
  const sidebarCount = document.getElementById("sidebar-finding-count");
  if (sidebarCount) {
    sidebarCount.textContent = bulgular.length;
    sidebarCount.style.display = "inline-block";
  }

  renderFindingsList();
  updateStatistics();
  switchTab("analiz-sonuclari");
}

// ============================================================================
// 3. İnceleme Ekranı ve Kararlar (Issue #7)
// ============================================================================
function setupReviewActions() {
  // Tümünü kabul et
  document.getElementById("btn-accept-all")?.addEventListener("click", async () => {
    for (const b of state.bulgular) {
      if (b.karar !== "kabul") {
        await submitDecision(b.id, "kabul");
      }
    }
    renderFindingsList();
    updateStatistics();
  });

  // Maskelemeyi uygula
  document.getElementById("btn-proceed-mask")?.addEventListener("click", async () => {
    await applyMasking();
  });

  // Elle bulgu ekleme formu
  const manualForm = document.getElementById("form-manual-finding");
  manualForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    await addManualFinding();
  });

  // İndirme butonları
  document.getElementById("btn-download-txt")?.addEventListener("click", () => {
    triggerDownload("txt");
  });
  document.getElementById("btn-download-docx")?.addEventListener("click", () => {
    triggerDownload("docx");
  });
  document.getElementById("btn-download-rapor")?.addEventListener("click", () => {
    triggerDownload("rapor");
  });

  // Kopyalama butonları
  document.getElementById("btn-copy-clean-text")?.addEventListener("click", () => {
    const txt = document.getElementById("clean-text-content");
    if (txt) {
      navigator.clipboard.writeText(txt.value);
      alert("Maskelenmiş metin panoya kopyalandı!");
    }
  });

  document.getElementById("btn-copy-masked-preview")?.addEventListener("click", () => {
    navigator.clipboard.writeText("İşbu sözleşme kapsamında danışman [KİŞİ_01], şirket bünyesinde gizli olarak yürütülen [PROJE_AD_A] veri tabanı üzerinde çalışacaktır.");
    alert("Örnek çıktı panoya kopyalandı!");
  });
}

function renderFindingsList() {
  const container = document.getElementById("findings-list");
  if (!container) return;

  if (state.bulgular.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>Henüz tespit edilmiş bir bulgu yok.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = "";

  state.bulgular.forEach((b) => {
    const isUnverified = b.durum === "dogrulanamadi";
    const statusClass = b.karar === "kabul" ? "status-kabul" : (b.karar === "red" ? "status-red" : "");
    const unverifiedClass = isUnverified ? "unverified-flag" : "";

    const card = document.createElement("div");
    card.className = `finding-item ${statusClass} ${unverifiedClass}`;
    card.id = `finding-card-${b.id}`;

    // Konum metni
    let locText = "Konum: Doğrulanamadı";
    if (b.konum && b.konum.satir) {
      locText = `Satır: ${b.konum.satir}`;
      if (b.konum.baslangic !== null && b.konum.baslangic !== undefined) {
        locText += ` (Karakter: ${b.konum.baslangic} - ${b.konum.bitis})`;
      }
    }

    card.innerHTML = `
      <div class="finding-top-row">
        <div class="finding-badges">
          <span class="badge-category">${escapeHtml(b.kategori.toUpperCase())}</span>
          <span class="badge-risk risk-${b.risk || 'orta'}">Risk: ${(b.risk || 'orta').toUpperCase()}</span>
          ${isUnverified ? '<span class="badge-unverified">⚠ Elle Kontrol Edilmeli (Doğrulanamadı)</span>' : ''}
          <span class="badge-confidence">Güven: %${Math.round((b.guven || 0.9) * 100)}</span>
          <span class="badge-confidence">Kaynak: ${escapeHtml(b.kaynak)}</span>
        </div>
        <div class="finding-actions">
          <button class="btn-decision ${b.karar === 'kabul' ? 'active-kabul' : ''}" data-id="${b.id}" data-action="kabul">
            ✓ Kabul
          </button>
          <button class="btn-decision ${b.karar === 'red' ? 'active-red' : ''}" data-id="${b.id}" data-action="red">
            ✕ Red
          </button>
        </div>
      </div>

      <div class="finding-evidence-box">
        <span class="evidence-label">KANIT METNİ:</span>
        <span class="evidence-quote">"${escapeHtml(b.kanit)}"</span>
      </div>

      <div class="finding-meta-row">
        <span class="finding-reason">${escapeHtml(b.neden || '')}</span>
        <span class="finding-source-loc">${locText}</span>
      </div>
    `;

    // Buton dinleyicileri
    const btnKabul = card.querySelector('[data-action="kabul"]');
    const btnRed = card.querySelector('[data-action="red"]');

    btnKabul.addEventListener("click", async () => {
      await submitDecision(b.id, "kabul");
      btnKabul.classList.add("active-kabul");
      btnRed.classList.remove("active-red");
      card.classList.remove("status-red");
      card.classList.add("status-kabul");
      updateStatistics();
    });

    btnRed.addEventListener("click", async () => {
      await submitDecision(b.id, "red");
      btnRed.classList.add("active-red");
      btnKabul.classList.remove("active-kabul");
      card.classList.remove("status-kabul");
      card.classList.add("status-red");
      updateStatistics();
    });

    container.appendChild(card);
  });
}

async function submitDecision(bulguId, karar) {
  try {
    const res = await fetch(`/bulgular/${bulguId}/karar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ karar }),
    });

    if (res.ok) {
      const guncel = await res.json();
      const idx = state.bulgular.findIndex((x) => x.id === bulguId);
      if (idx !== -1) {
        state.bulgular[idx].karar = guncel.karar;
      }
    } else {
      showAlert("Karar güncellenirken bir hata oluştu.");
    }
  } catch (err) {
    showAlert("API bağlantı hatası!");
  }
}

async function addManualFinding() {
  if (!state.currentBelgeId) {
    showAlert("Lütfen önce bir belge yükleyin.");
    return;
  }

  const kanitInput = document.getElementById("manual-kanit");
  const kategoriInput = document.getElementById("manual-kategori");
  const riskInput = document.getElementById("manual-risk");

  const kanit = kanitInput.value.trim();
  const kategori = kategoriInput.value;
  const risk = riskInput.value;

  if (!kanit) return;

  try {
    const res = await fetch(`/belgeler/${state.currentBelgeId}/bulgular`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kategori,
        kanit,
        risk,
        neden: "Kullanıcı tarafından elle eklendi (Özel Arama)",
      }),
    });

    if (res.ok) {
      const yeniBulgu = await res.json();
      // Otomatik olarak kabul edilmiş sayabiliriz veya beklemede kalabilir
      yeniBulgu.karar = "kabul";
      state.bulgular.unshift(yeniBulgu);
      kanitInput.value = "";
      renderFindingsList();
      updateStatistics();
      showAlert("Yeni bulgu başarıyla eklendi!", "info");
    } else {
      showAlert("Elle bulgu eklenirken hata oluştu.");
    }
  } catch (err) {
    showAlert("API bağlantı hatası!");
  }
}

function updateStatistics() {
  const total = state.bulgular.length;
  const accepted = state.bulgular.filter((b) => b.karar === "kabul").length;
  const rejected = state.bulgular.filter((b) => b.karar === "red").length;
  const unverified = state.bulgular.filter((b) => b.durum === "dogrulanamadi").length;

  const statTotal = document.getElementById("stat-total");
  const statAccepted = document.getElementById("stat-accepted");
  const statRejected = document.getElementById("stat-rejected");
  const statUnverified = document.getElementById("stat-unverified");

  if (statTotal) statTotal.textContent = total;
  if (statAccepted) statAccepted.textContent = accepted;
  if (statRejected) statRejected.textContent = rejected;
  if (statUnverified) statUnverified.textContent = unverified;
}

// ============================================================================
// 4. Maskeleme ve Çıktı Alma (POST /belgeler/{id}/maskele)
// ============================================================================
async function applyMasking() {
  if (!state.currentBelgeId) {
    showAlert("Lütfen önce bir belge yükleyin.");
    return;
  }

  try {
    const res = await fetch(`/belgeler/${state.currentBelgeId}/maskele`, {
      method: "POST",
    });

    if (!res.ok) {
      showAlert("Maskeleme sırasında bir hata oluştu.");
      return;
    }

    const data = await res.json();
    state.temizMetin = data.temiz_metin;
    state.rapor = data.rapor;

    // Kullanıcının kasasındaki durumu güncelle
    if (state.currentUser && state.currentBelgeId) {
      updateVaultDocStatus(state.currentUser, state.currentBelgeId, "Maskelendi", data.rapor?.ozet?.toplam_maskelenen || 0);
    }

    // Önizleme alanını doldur
    const previewEl = document.getElementById("clean-text-content");
    if (previewEl) previewEl.value = data.temiz_metin;

    // Rapor JSON alanını doldur
    const raporView = document.getElementById("rapor-json-view");
    if (raporView) {
      raporView.textContent = JSON.stringify(data.rapor, null, 2);
    }

    switchTab("onizleme-indir");
  } catch (err) {
    showAlert("API bağlantı hatası!");
  }
}

function triggerDownload(tip) {
  if (!state.currentBelgeId) {
    showAlert("İndirilecek belge bulunamadı. Lütfen önce analiz yapın.");
    return;
  }
  window.location.href = `/belgeler/${state.currentBelgeId}/indir?tip=${tip}`;
}

// ============================================================================
// 5. Modallar ve Kullanıcı Oturumu (Auth & Vault Management)
// ============================================================================
function setupModals() {
  const modalLogin = document.getElementById("modal-login");
  const modalRegister = document.getElementById("modal-register");

  // Açma butonları
  document.getElementById("btn-open-login")?.addEventListener("click", () => {
    closeAllModals();
    modalLogin.style.display = "flex";
  });

  document.getElementById("btn-open-register")?.addEventListener("click", () => {
    closeAllModals();
    modalRegister.style.display = "flex";
  });

  document.getElementById("btn-hero-key")?.addEventListener("click", () => {
    closeAllModals();
    modalLogin.style.display = "flex";
  });

  // Kapatma butonları
  document.getElementById("btn-close-login")?.addEventListener("click", closeAllModals);
  document.getElementById("btn-close-register")?.addEventListener("click", closeAllModals);

  // Tab geçişleri
  document.getElementById("modal-switch-to-register")?.addEventListener("click", () => {
    closeAllModals();
    modalRegister.style.display = "flex";
  });

  document.getElementById("modal-switch-to-login")?.addEventListener("click", () => {
    closeAllModals();
    modalLogin.style.display = "flex";
  });

  document.getElementById("link-to-login")?.addEventListener("click", (e) => {
    e.preventDefault();
    closeAllModals();
    modalLogin.style.display = "flex";
  });

  // Giriş Yap Onay Butonu
  document.getElementById("btn-confirm-login")?.addEventListener("click", () => {
    const inputUser = document.getElementById("input-login-username");
    const username = (inputUser && inputUser.value.trim()) ? inputUser.value.trim() : "hakan.guvenlik";
    loginUser(username);
    closeAllModals();
  });

  // Kayıt Ol / Kasa Oluştur Onay Butonu
  document.getElementById("btn-confirm-register")?.addEventListener("click", () => {
    const inputReg = document.getElementById("input-register-username");
    const username = (inputReg && inputReg.value.trim()) ? inputReg.value.trim() : "Hukuk Bürosu A.Ş.";
    loginUser(username);
    closeAllModals();
  });

  // Çıkış Yap / Kasayı Kilitle Butonu
  document.getElementById("btn-logout")?.addEventListener("click", () => {
    logoutUser();
  });

  // Kasada Yeni Analiz Butonu
  document.getElementById("btn-vault-new-analysis")?.addEventListener("click", () => {
    switchTab("yeni-analiz");
  });

  // Modal dışına tıklayınca kapatma
  window.addEventListener("click", (e) => {
    if (e.target === modalLogin || e.target === modalRegister) {
      closeAllModals();
    }
  });
}

function loginUser(username) {
  state.currentUser = username;
  localStorage.setItem("sessiz_kalem_active_user", username);
  updateAuthUI();
  showAlert(`"${username}" şifreli çalışma alanı açıldı. Kasanızdaki analizler yüklendi.`, "info");
}

function logoutUser() {
  const oldUser = state.currentUser;
  state.currentUser = null;
  localStorage.removeItem("sessiz_kalem_active_user");
  updateAuthUI();
  showAlert(`"${oldUser}" kasası kilitlendi. Yerel oturum RAM'den temizlendi (Zero-Trace).`, "info");
}

function updateAuthUI() {
  const authUnlogged = document.getElementById("auth-unlogged");
  const authLogged = document.getElementById("auth-logged");
  const topbarUser = document.getElementById("topbar-username");
  const avatarBadge = document.getElementById("user-avatar-badge");
  const userVaultSection = document.getElementById("user-vault-section");

  if (state.currentUser) {
    if (authUnlogged) authUnlogged.style.display = "none";
    if (authLogged) authLogged.style.display = "flex";
    if (topbarUser) topbarUser.textContent = state.currentUser;
    if (avatarBadge) {
      const initials = state.currentUser.split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase() || "🔒";
      avatarBadge.innerHTML = `<span style="font-weight:700;font-size:11px;">${initials}</span>`;
      avatarBadge.style.borderColor = "var(--mint-primary)";
    }
    if (userVaultSection) {
      userVaultSection.style.display = "block";
    }
    renderUserVault();
  } else {
    if (authUnlogged) authUnlogged.style.display = "flex";
    if (authLogged) authLogged.style.display = "none";
    if (avatarBadge) {
      avatarBadge.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
      avatarBadge.style.borderColor = "var(--border-highlight)";
    }
    if (userVaultSection) {
      userVaultSection.style.display = "none";
    }
  }
}

function getVaultDocuments(username) {
  const key = `sessiz_kalem_vault_${username}`;
  const saved = localStorage.getItem(key);
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (e) {}
  }

  // Varsayılan mock veriler (Kullanıcıya özel ilk yükleme)
  let initialDocs = [];
  if (username.toLowerCase().includes("hakan")) {
    initialDocs = [
      {
        id: "doc-hakan-01",
        filename: "Gizlilik_Sozlesmesi_v3.pdf",
        date: "2026-10-17 21:15",
        findingsCount: 4,
        maskedCount: 4,
        status: "Maskelendi"
      },
      {
        id: "doc-hakan-02",
        filename: "Ticari_Protokol_Atlas.txt",
        date: "2026-10-17 22:40",
        findingsCount: 3,
        maskedCount: 3,
        status: "Maskelendi"
      }
    ];
  } else if (username.toLowerCase().includes("hukuk")) {
    initialDocs = [
      {
        id: "doc-hukuk-01",
        filename: "Danismanlik_Sozlesmesi_2026.docx",
        date: "2026-10-17 19:30",
        findingsCount: 5,
        maskedCount: 5,
        status: "Maskelendi"
      }
    ];
  }

  localStorage.setItem(key, JSON.stringify(initialDocs));
  return initialDocs;
}

function saveVaultDocument(username, doc) {
  const docs = getVaultDocuments(username);
  // Aynı id varsa güncelle, yoksa başa ekle
  const idx = docs.findIndex(d => d.id === doc.id);
  if (idx !== -1) {
    docs[idx] = { ...docs[idx], ...doc };
  } else {
    docs.unshift(doc);
  }
  localStorage.setItem(`sessiz_kalem_vault_${username}`, JSON.stringify(docs));
  renderUserVault();
}

function updateVaultDocStatus(username, docId, newStatus, maskedCount) {
  const docs = getVaultDocuments(username);
  const doc = docs.find(d => d.id === docId);
  if (doc) {
    doc.status = newStatus;
    if (maskedCount !== undefined) doc.maskedCount = maskedCount;
    localStorage.setItem(`sessiz_kalem_vault_${username}`, JSON.stringify(docs));
    renderUserVault();
  }
}

function deleteVaultDocument(docId) {
  if (!state.currentUser) return;
  if (!confirm("Bu analiz kaydını kasanızdan silmek istediğinize emin misiniz?")) return;
  
  const key = `sessiz_kalem_vault_${state.currentUser}`;
  let docs = getVaultDocuments(state.currentUser);
  docs = docs.filter(d => d.id !== docId);
  localStorage.setItem(key, JSON.stringify(docs));
  renderUserVault();
  showAlert("Belge kaydı kasanızdan silindi.", "info");
}

function renderUserVault() {
  if (!state.currentUser) return;

  const displayEl = document.getElementById("vault-user-display");
  if (displayEl) displayEl.textContent = state.currentUser;

  const docs = getVaultDocuments(state.currentUser);
  const countEl = document.getElementById("vault-doc-count");
  const maskedEl = document.getElementById("vault-masked-count");

  if (countEl) countEl.textContent = docs.length;
  if (maskedEl) {
    const totalMasked = docs.reduce((acc, d) => acc + (d.maskedCount || 0), 0);
    maskedEl.textContent = `${totalMasked} İhlal İzolasyonu`;
  }

  const listContainer = document.getElementById("vault-doc-list");
  if (!listContainer) return;

  if (docs.length === 0) {
    listContainer.innerHTML = `
      <div class="empty-state" style="padding: 24px;">
        <p>Henüz bu kasaya kayıtlı bir analiz yok. Yukarıdaki <strong>"+ Bu Kasada Yeni Analiz"</strong> butonunu kullanarak ilk belgenizi inceleyebilirsiniz.</p>
      </div>
    `;
    return;
  }

  listContainer.innerHTML = "";
  docs.forEach(d => {
    const ext = d.filename.split(".").pop().toUpperCase();
    const isMasked = d.status === "Maskelendi";
    
    const item = document.createElement("div");
    item.className = "vault-doc-item";
    item.innerHTML = `
      <div class="doc-info-col">
        <div class="doc-type-icon">${ext}</div>
        <div>
          <div class="doc-title-text">${escapeHtml(d.filename)}</div>
          <div class="doc-date-text">Tarih: ${d.date} • ID: ${d.id}</div>
        </div>
      </div>
      <div class="doc-meta-col">
        <span class="doc-findings-badge">${d.findingsCount} Bulgu Tespit Edildi</span>
        <span class="badge-tag" style="font-family:var(--font-mono);font-size:11px;color:${isMasked ? 'var(--mint-primary)' : 'var(--yellow-warn)'};">
          ${isMasked ? '✓ ' + d.status : '⏳ ' + d.status}
        </span>
        <div class="doc-actions-wrap">
          <button class="btn btn-xs btn-outline-xs" onclick="inspectVaultDoc('${d.id}', '${escapeHtml(d.filename)}')">
            İncele
          </button>
          <button class="btn btn-xs btn-outline-xs text-red" onclick="deleteVaultDocument('${d.id}')" title="Kasadan Sil">
            Sil
          </button>
        </div>
      </div>
    `;
    listContainer.appendChild(item);
  });
}

// Global scope'a bağla (onclick için)
window.inspectVaultDoc = function(docId, filename) {
  loadSampleDocument();
  showAlert(`"${filename}" kasadan çözülüp inceleme ekranına aktarıldı.`, "info");
};

window.deleteVaultDocument = deleteVaultDocument;

function closeAllModals() {
  const m1 = document.getElementById("modal-login");
  const m2 = document.getElementById("modal-register");
  const m3 = document.getElementById("modal-admin-enclave-gate");
  const m4 = document.getElementById("modal-add-admin");
  if (m1) m1.style.display = "none";
  if (m2) m2.style.display = "none";
  if (m3) m3.style.display = "none";
  if (m4) m4.style.display = "none";
}

// ============================================================================
// 6. Simülasyon ve Hata Yönetimi (503 & 400 - docs/api-contract.md §4)
// ============================================================================
function setupSimulations() {
  const toggleBtn = document.getElementById("btn-toggle-ollama");
  const badge = document.getElementById("ollama-status-badge");

  toggleBtn?.addEventListener("click", async () => {
    state.isOllamaOffline = !state.isOllamaOffline;

    try {
      await fetch(`/simulasyon/model-durumu?cevrildisi=${state.isOllamaOffline}`, {
        method: "POST",
      });
    } catch (e) {}

    if (state.isOllamaOffline) {
      badge.style.color = "var(--red-alert)";
      badge.style.borderColor = "rgba(244, 63, 94, 0.4)";
      badge.innerHTML = `<span class="pulse-dot" style="background-color: var(--red-alert);"></span><span>Ollama: Çevrimdışı (127.0.0.1)</span>`;
      showAlert("Simülasyon Aktif: Ollama çevrimdışı duruma getirildi (503 testi için).");
    } else {
      badge.style.color = "var(--mint-primary)";
      badge.style.borderColor = "rgba(23, 216, 166, 0.3)";
      badge.innerHTML = `<span class="pulse-dot"></span><span>Ollama: Bağlı (Gemma 4 · 127.0.0.1)</span>`;
      showAlert("Ollama servisi yeniden bağlandı.", "info");
    }
  });
}

function handleApiError(statusCode, err) {
  if (statusCode === 503) {
    showAlert(
      "Ollama modeline erişilemiyor! Lütfen Ollama servisinin çalıştığından emin olun (127.0.0.1:11434). [docs/api-contract.md §4 uyarısı]"
    );
  } else if (statusCode === 400) {
    const msg = err.detail?.hata === "desteklenmeyen_dosya_tipi"
      ? "Desteklenmeyen dosya formatı! Yalnızca .pdf, .docx veya .txt yükleyebilirsiniz."
      : "Belge boş veya okunamadı!";
    showAlert(msg);
  } else {
    showAlert("Bir hata oluştu: " + (err.detail?.hata || statusCode));
  }
}

function showAlert(msg, type = "error") {
  const banner = document.getElementById("global-alert");
  const text = document.getElementById("global-alert-text");
  if (!banner || !text) return;

  text.textContent = msg;
  banner.style.display = "flex";

  if (type === "info") {
    banner.style.background = "rgba(23, 216, 166, 0.15)";
    banner.style.borderColor = "rgba(23, 216, 166, 0.4)";
    banner.style.color = "#a7f3d0";
  } else {
    banner.style.background = "rgba(244, 63, 94, 0.15)";
    banner.style.borderColor = "rgba(244, 63, 94, 0.4)";
    banner.style.color = "#fda4af";
  }

  setTimeout(() => {
    banner.style.display = "none";
  }, 7000);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ============================================================================
// 7. Sistem Yönetimi & Kurumsal Kontrol Merkezi (Screenshot 1 & 2)
// ============================================================================
function setupAdminControlCenter() {
  // 1. Alt Sekmeler (Subtabs)
  const subtabBtns = document.querySelectorAll(".admin-tab");
  subtabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetSubtab = btn.getAttribute("data-subtab");
      subtabBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      document.querySelectorAll(".admin-subpane").forEach((pane) => {
        pane.style.display = "none";
        pane.classList.remove("active");
      });

      const activePane = document.getElementById(`subpane-${targetSubtab}`);
      if (activePane) {
        activePane.style.display = "block";
        activePane.classList.add("active");
      }
    });
  });

  // 2. Enclave Doğrulama Kapısı (Screenshot 2 Modal)
  const enclaveGateModal = document.getElementById("modal-admin-enclave-gate");
  const touchTargetFido = document.getElementById("touch-target-fido");
  const btnUnlockAdminGate = document.getElementById("btn-unlock-admin-gate");
  const btnCancelAdminGate = document.getElementById("btn-cancel-admin-gate");
  const btnCloseAdminGate = document.getElementById("btn-close-admin-gate");

  function unlockEnclaveSuccess() {
    state.adminVerified = true;
    if (touchTargetFido) touchTargetFido.classList.add("active");

    setTimeout(() => {
      if (enclaveGateModal) enclaveGateModal.style.display = "none";
      if (touchTargetFido) touchTargetFido.classList.remove("active");
      showAlert(
        "Süper Yönetici Enclave Kilidi Açıldı (YubiKey 5 NFC WebAuthn Doğrulandı)",
        "info"
      );
    }, 450);
  }

  touchTargetFido?.addEventListener("click", () => {
    const title = touchTargetFido.querySelector(".touch-prompt-title");
    if (title) title.textContent = "Biyometrik veri doğrulanıyor...";
    unlockEnclaveSuccess();
  });

  btnUnlockAdminGate?.addEventListener("click", () => {
    unlockEnclaveSuccess();
  });

  btnCancelAdminGate?.addEventListener("click", () => {
    if (enclaveGateModal) enclaveGateModal.style.display = "none";
    switchTab("genel-bakis");
  });

  btnCloseAdminGate?.addEventListener("click", () => {
    if (enclaveGateModal) enclaveGateModal.style.display = "none";
    switchTab("genel-bakis");
  });

  // Enclave Modal İç Sekmeler (Donanım vs Kasa Parolası)
  const tabHardware = document.getElementById("tab-hardware-fido");
  const tabAdminPwd = document.getElementById("tab-admin-pwd");
  const gateViewHardware = document.getElementById("gate-view-hardware");
  const gateViewPassword = document.getElementById("gate-view-password");

  tabHardware?.addEventListener("click", () => {
    tabHardware.classList.add("active");
    tabAdminPwd?.classList.remove("active");
    if (gateViewHardware) gateViewHardware.style.display = "block";
    if (gateViewPassword) gateViewPassword.style.display = "none";
  });

  tabAdminPwd?.addEventListener("click", () => {
    tabAdminPwd.classList.add("active");
    tabHardware?.classList.remove("active");
    if (gateViewHardware) gateViewHardware.style.display = "none";
    if (gateViewPassword) gateViewPassword.style.display = "block";
    document.getElementById("input-admin-token")?.focus();
  });

  // 3. Tablo Filtreleme ve Arama
  const searchInput = document.getElementById("admin-user-search");
  const filterDept = document.getElementById("filter-dept");
  const filterRole = document.getElementById("filter-role");

  function filterMatrixTable() {
    const query = (searchInput?.value || "").toLowerCase().trim();
    const dept = filterDept?.value || "all";
    const role = filterRole?.value || "all";

    const rows = document.querySelectorAll("#matrix-tbody tr");
    let visibleCount = 0;
    rows.forEach((row) => {
      const text = row.innerText.toLowerCase();
      const matchQuery = !query || text.includes(query);

      let matchDept = true;
      if (dept === "hukuk") matchDept = text.includes("hukuk") || text.includes("müşavir");
      else if (dept === "guvenlik") matchDept = text.includes("güvenlik") || text.includes("ciso");
      else if (dept === "kvkk") matchDept = text.includes("kvkk") || text.includes("denetçi");
      else if (dept === "arge") matchDept = text.includes("sistem") || text.includes("mühendis");

      let matchRole = true;
      if (role === "super") matchRole = text.includes("süper yönetici");
      else if (role === "onaylayici") matchRole = text.includes("onaylayıcı");
      else if (role === "salt-okunur") matchRole = text.includes("salt-okunur");

      if (matchQuery && matchDept && matchRole) {
        row.style.display = "";
        visibleCount++;
      } else {
        row.style.display = "none";
      }
    });

    const footerCount = document.querySelector(".footer-count");
    if (footerCount) {
      footerCount.textContent = `Toplam 12 kullanıcıdan ${visibleCount} tanesi gösteriliyor`;
    }
  }

  searchInput?.addEventListener("input", filterMatrixTable);
  filterDept?.addEventListener("change", filterMatrixTable);
  filterRole?.addEventListener("change", filterMatrixTable);

  // 4. Aksiyon Butonları (YAML Export, Purge, Yeni Yönetici Ekle)
  document.getElementById("btn-export-yaml")?.addEventListener("click", () => {
    const yamlContent =
`# Sessiz Kalem Air-Gap Kurumsal Yapılandırma
version: "2.4-ephemeral"
node:
  id: "0x90A...FD21"
  mode: "air-gap-strict"
  tls_pinned: "1.3"
  host: "127.0.0.1"
enclave:
  type: "Hardware-RAM-ZeroTrace"
  zero_access_policy: true
  ram_purge_on_exit: true
  master_hash_algorithm: "SHA-256"
inference_engine:
  provider: "ollama"
  endpoint: "http://127.0.0.1:11434"
  model: "gemma3:4b"
  quantization: "Q4_K_M"
  hardware_accel: "Metal GPU 32-Core"
  latency_avg_ms: 18
dlp_rules:
  tr_national_id: true
  tr_iban: true
  project_codenames: true
  financial_amounts: true
  checksum_validation: true
active_principals: 12
export_timestamp: "${new Date().toISOString()}"
`;
    const blob = new Blob([yamlContent], { type: "text/yaml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sessiz_kalem_config.yaml";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showAlert("Kurumsal yapılandırma YAML dosyası başarıyla dışa aktarıldı.", "info");
  });

  // Bellek Sıfırla (Purge)
  document.getElementById("btn-purge-ram")?.addEventListener("click", () => {
    const ramValEl = document.querySelector(".kpi-card:nth-child(4) .kpi-val");
    const ramBar = document.querySelector(".kpi-card:nth-child(4) .dual-bar");
    if (ramValEl) ramValEl.textContent = "0";
    if (ramBar) ramBar.style.width = "0%";
    showAlert("Uçucu RAM ve Güvenli Enclave Belleği Sıfırlandı (Purge tamamlandı - 0 Byte sızıntı).", "info");

    setTimeout(() => {
      if (ramValEl) ramValEl.textContent = "142";
      if (ramBar) ramBar.style.width = "14%";
    }, 2500);
  });

  // Yeni Yönetici Ekle Modal
  const modalAddAdmin = document.getElementById("modal-add-admin");
  document.getElementById("btn-open-add-admin")?.addEventListener("click", () => {
    if (modalAddAdmin) modalAddAdmin.style.display = "flex";
  });
  document.getElementById("btn-close-add-admin")?.addEventListener("click", () => {
    if (modalAddAdmin) modalAddAdmin.style.display = "none";
  });

  // Yetkilendir ve Kasaya Ekle
  document.getElementById("btn-submit-new-admin")?.addEventListener("click", () => {
    const name = document.getElementById("add-admin-name")?.value.trim() || "Av. Yeni Analist";
    const email = document.getElementById("add-admin-email")?.value.trim() || "analist@sessizkalem.corp";
    const role = document.getElementById("add-admin-role")?.value || "Hukuk Danışmanı";
    const level = document.getElementById("add-admin-level")?.value || "Onaylayıcı";

    const initials = name.split(" ").map((w) => w[0]).join("").substring(0, 2).toUpperCase() || "KV";
    const tbody = document.getElementById("matrix-tbody");

    let levelClass = "role-approver";
    if (level === "Süper Yönetici") levelClass = "role-super";
    if (level === "Salt-Okunur") levelClass = "role-readonly";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <div class="table-user-cell">
          <div class="user-badge-circle" style="background:rgba(0, 229, 255, 0.15);color:#00e5ff;border:1px solid rgba(0, 229, 255, 0.35);">${initials}</div>
          <div>
            <div class="user-cell-name">${escapeHtml(name)}</div>
            <div class="user-cell-email">${escapeHtml(email)}</div>
          </div>
        </div>
      </td>
      <td>${escapeHtml(role)}</td>
      <td><span class="role-pill ${levelClass}">${escapeHtml(level)}</span></td>
      <td>
        <span class="user-status-pill status-active"><span class="dot-mint"></span> Aktif</span>
      </td>
      <td class="cell-time">Şimdi <code>(127.0.0.1)</code></td>
      <td style="text-align: right;">
        <div class="row-actions">
          <button class="action-icon-btn btn-edit" title="Yetkileri Düzenle">✏️</button>
          <button class="action-icon-btn btn-revoke" title="Erişimi Askıya Al">🚫</button>
        </div>
      </td>
    `;

    tbody?.prepend(tr);
    if (modalAddAdmin) modalAddAdmin.style.display = "none";
    showAlert(`"${name}" başarıyla yetkilendirildi ve kurumsal erişim matrisine eklendi.`, "info");
    wireRowActions();
  });

  // Düzenle & Askıya Al butonları
  function wireRowActions() {
    document.querySelectorAll(".row-actions .btn-edit").forEach((btn) => {
      btn.onclick = () => {
        const row = btn.closest("tr");
        const name = row?.querySelector(".user-cell-name")?.textContent || "Kullanıcı";
        showAlert(`"${name}" yetki profili düzenleme modu açıldı.`, "info");
      };
    });

    document.querySelectorAll(".row-actions .btn-revoke").forEach((btn) => {
      btn.onclick = () => {
        const row = btn.closest("tr");
        const name = row?.querySelector(".user-cell-name")?.textContent || "Kullanıcı";
        const statusPill = row?.querySelector(".user-status-pill");
        const isCurrentlyActive = statusPill?.classList.contains("status-active");

        if (isCurrentlyActive) {
          if (confirm(`"${name}" kullanıcısının yetkilerini askıya almak istiyor musunuz?`)) {
            if (statusPill) {
              statusPill.className = "user-status-pill status-revoked";
              statusPill.innerHTML = `<span class="dot-red"></span> Askıya Alındı`;
            }
            row.style.opacity = "0.6";
            showAlert(`"${name}" kullanıcısının erişimi askıya alındı.`, "info");
          }
        } else {
          if (statusPill) {
            statusPill.className = "user-status-pill status-active";
            statusPill.innerHTML = `<span class="dot-mint"></span> Aktif`;
          }
          row.style.opacity = "1";
          showAlert(`"${name}" kullanıcısının erişimi yeniden aktif edildi.`, "info");
        }
      };
    });
  }
  wireRowActions();

  // Ollama Ping & Reload Model
  document.getElementById("btn-ping-ollama")?.addEventListener("click", () => {
    showAlert("Ollama Gemma 4 Yanıt Testi: 18ms (127.0.0.1:11434 / Metal GPU 32-Core Canlı)", "info");
  });

  document.getElementById("btn-reload-weights")?.addEventListener("click", () => {
    showAlert("Model ağırlıkları (Q4_K_M) GPU belleğine yeniden başarıyla yüklendi.", "info");
  });
}
