// Tek menü ikonu: kapalıyken sağ üstte, açıkken sidebar içinde logo sağ üstünde.
// Sidebar tüm ekranlarda off-canvas; başlangıçta kapalı.
// Arama: menüyü filtreler, eşleşen grupları açar.
(function () {
    const sidebar = document.getElementById("sidebar");
    const menuTree = document.getElementById("menuTree");
    const slot = document.getElementById("menuButtonSlot");
    const btnMenu = document.getElementById("btnMenu");

    const searchInput = document.getElementById("sidebarSearch");
    const btnClearSearch = document.getElementById("btnClearSearch");

    // ---- helpers ----
    function openSidebar() {
        // butonu sidebar içine taşı
        if (slot && btnMenu && !slot.contains(btnMenu)) {
            slot.appendChild(btnMenu);
            btnMenu.classList.add("menu-btn-internal");
        }
        sidebar.classList.add("open");
    }
    function closeSidebar() {
        // butonu tekrar ana içeriğe (body içinde sabit sağ üst) taşı
        if (btnMenu && !document.body.contains(btnMenu)) return;
        const main = document.querySelector(".main");
        if (main && btnMenu && !main.contains(btnMenu)) {
            main.appendChild(btnMenu);
        }
        btnMenu.classList.remove("menu-btn-internal");
        sidebar.classList.remove("open");
    }

    // Başlangıç: kapalı
    closeSidebar();

    // Tek butonla aç/kapat
    btnMenu?.addEventListener("click", () => {
        if (sidebar.classList.contains("open")) closeSidebar();
        else openSidebar();
    });

    // Menü tıklanınca kapat
    sidebar?.querySelectorAll(".item").forEach(a => a.addEventListener("click", closeSidebar));

    // ---- Accordion ----
    menuTree?.addEventListener("click", (e) => {
        const btn = e.target.closest(".group-toggle");
        if (!btn) return;
        const group = btn.closest(".group");
        const body = group.querySelector(".group-body");
        const willShow = !body.classList.contains("show");
        body.classList.toggle("show", willShow);
        btn.setAttribute("aria-expanded", willShow ? "true" : "false");
    });

    // ---- Search ----
    function normalize(s) { return (s || "").toLocaleLowerCase("tr-TR"); }
    function filterMenu(q) {
        const term = normalize(q);
        const items = menuTree.querySelectorAll(".item");
        const groups = menuTree.querySelectorAll(".group");

        // Reset
        items.forEach(i => i.classList.remove("d-none"));
        groups.forEach(g => g.classList.remove("d-none"));

        if (!term) {
            btnClearSearch?.classList.add("d-none");
            return;
        }
        btnClearSearch?.classList.remove("d-none");

        // Hide unmatched items + expand parents of hits
        items.forEach(i => {
            const hit = normalize(i.textContent).includes(term);
            i.classList.toggle("d-none", !hit);
            if (hit) {
                // open parents
                let p = i.parentElement;
                while (p && p !== menuTree) {
                    if (p.classList.contains("group-body")) {
                        p.classList.add("show");
                        p.closest(".group")?.querySelector(".group-toggle")?.setAttribute("aria-expanded", "true");
                    }
                    p = p.parentElement;
                }
            }
        });

        // Hide empty groups
        groups.forEach(g => {
            const visibleItems = g.querySelectorAll(":scope .group-body > .item:not(.d-none)");
            const visibleGroups = g.querySelectorAll(":scope .group-body > .group:not(.d-none)");
            const hasAny = visibleItems.length + visibleGroups.length > 0;
            g.classList.toggle("d-none", !hasAny);
        });
    }

    searchInput?.addEventListener("input", e => filterMenu(e.target.value));
    btnClearSearch?.addEventListener("click", () => {
        searchInput.value = "";
        filterMenu("");
        menuTree.querySelectorAll(".d-none").forEach(el => el.classList.remove("d-none"));
    });

})();
