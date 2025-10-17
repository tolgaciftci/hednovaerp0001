// Yapılandırma kartlarını üretir; İSİM alanına göre arama yapar; Git butonlarını hazırlar.
(function () {
    const grid = document.getElementById("ylGrid");
    const search = document.getElementById("ylSearch");
    const clearBtn = document.getElementById("ylClear");

    // ===== Veri =====
    // İsim ve Açıklama; Kodlar JS tarafından YPLN-0001... şeklinde atanır.
    const rows = [
        { name: "Satış", icon: "fa-cart-shopping", desc: "Satış modülüne ait yapılandırmaları buradan yönetebilirsiniz." },
        { name: "Satınalma", icon: "fa-truck", desc: "Satınalma modülüne ait yapılandırmaları buradan yönetebilirsiniz." },
        { name: "Üretim", icon: "fa-industry", desc: "Üretim modülüne ait yapılandırmaları buradan yönetebilirsiniz." },
        { name: "Sistem", icon: "fa-gear", desc: "Sistem modülüne ait yapılandırmaları buradan yönetebilirsiniz." },
        { name: "Muhasebe", icon: "fa-calculator", desc: "Muhasebe modülüne ait yapılandırmaları buradan yönetebilirsiniz." },
        { name: "Finans", icon: "fa-coins", desc: "Finans modülüne ait yapılandırmaları buradan yönetebilirsiniz." },
        // İstersen burada yeni modüller ekleyebilirsin...
    ];

    // Kod üretimi
    let counter = 1;
    function nextCode() {
        const num = String(counter).padStart(4, "0");
        counter += 1;
        return `YPLN-${num}`;
    }
    rows.forEach(r => r.code = nextCode());

    // ===== Render =====
    function renderCards(list) {
        grid.innerHTML = list.map(r => `
      <div class="yl-col">
        <article class="yl-card" data-name="${r.name.toLowerCase()}">
          <div class="yl-top">
            <span class="yl-code">${r.code}</span>
            <span class="yl-badge"><i class="fa-solid ${r.icon}"></i><span>${r.name}</span></span>
          </div>

          <h3 class="yl-name">${r.name}</h3>
          <p class="yl-desc">${r.desc}</p>

          <div class="yl-actions">
            <a class="yl-btn" href="/Yapilandirma/Detay?evrakno=${encodeURIComponent(r.code)}" title="Git">
              <i class="fa-solid fa-arrow-right"></i> <span>Git</span>
            </a>
          </div>
        </article>
      </div>
    `).join("");
    }
    renderCards(rows);

    // ===== Arama (İSİM) =====
    function normalize(s) { return (s || "").toLocaleLowerCase("tr-TR"); }

    function filterByName(q) {
        const term = normalize(q);
        const cards = grid.querySelectorAll(".yl-card");
        let any = false;

        cards.forEach(card => {
            const name = card.getAttribute("data-name") || "";
            const show = !term || name.includes(term);
            card.parentElement.classList.toggle("yl-hidden", !show);
            if (show) any = true;
        });

        clearBtn.classList.toggle("d-none", !(term && term.length));
    }

    search?.addEventListener("input", (e) => filterByName(e.target.value));
    clearBtn?.addEventListener("click", () => {
        search.value = "";
        filterByName("");
        grid.querySelectorAll(".yl-hidden").forEach(el => el.classList.remove("yl-hidden"));
        clearBtn.classList.add("d-none");
    });

})();
