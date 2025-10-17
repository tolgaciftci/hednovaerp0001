// Detay: 2 üst buton, arama, 3 sütun parametre kartları ve Kaydet mock
(function () {
    const form = document.getElementById("ydForm");
    const search = document.getElementById("ydSearch");
    const clearBtn = document.getElementById("ydClear");
    const btnSave = document.getElementById("ydSave");
    const toast = document.getElementById("ydToast");

    // Kod üretimi: YPLN-0003.0001, 0002 ...
    let sub = 1;
    const nextCode = () => `YPLN-0003.${String(sub++).padStart(4, "0")}`;

    // Parametreler
    const params = [
        { name: "Operatör kodu okutulsun", desc: "Operatör kart/QR okutma zorunlu olsun.", type: "switch", default: true },
        { name: "Tezgâh okutulsun", desc: "Tezgâh seçimi kart/QR okutma ile yapılsın.", type: "switch", default: false },
        { name: "Başlamış işler gün aralığı", desc: "‘Başlamış işler’ listesinde geriye dönük gün sayısı.", type: "number", min: 1, max: 365, step: 1, default: 7 },
        { name: "Bitmiş işler gün aralığı", desc: "‘Bitmiş işler’ listesinde geriye dönük gün sayısı.", type: "number", min: 1, max: 365, step: 1, default: 30 },
        { name: "Bitiş miktarı bildirilsin", desc: "Tamamlanan miktar kullanıcıdan istenir.", type: "switch", default: true },
        { name: "Lot/seri zorunlu", desc: "Ürünlerde lot/seri numarası zorunlu olsun.", type: "switch", default: false },
        { name: "Ürün resmi butonu", desc: "Operatör ekranında ürün resmi açma butonu görünsün.", type: "switch", default: true },
        { name: "Çoklu operatör seçimi", desc: "Aynı bildirimde birden fazla operatör atanabilsin.", type: "switch", default: false },
        { name: "Duruş girişi", desc: "Operatör duruş nedenlerini bildirebilsin.", type: "switch", default: true },
        { name: "Ek malzeme tüketimi", desc: "Plan dışı ek malzeme tüketimi yapılabilsin.", type: "switch", default: false },
        { name: "Fire bildirimi", desc: "Üretimde oluşan fire miktarı girilebilsin.", type: "switch", default: true },
        { name: "Yan ürün bildirimi", desc: "Ana üretime bağlı yan ürün bildirimi yapılabilsin.", type: "switch", default: false },
        { name: "Sonraki iş başlangıcı otomatik", desc: "Bir işin bitişi sonraki işin başlangıcı olsun.", type: "switch", default: true },
        {
            name: "Operatör seçimi ekranı", desc: "Operatör seçimi hangi adımda yapılacak?",
            type: "select",
            options: [
                { value: "start", label: "Başlangıç ekranı" },
                { value: "end", label: "Bitiş ekranı" },
                { value: "both", label: "Her iki ekran" }
            ],
            default: "start"
        },
        { name: "Başlamış/bitmiş sekmeli görünüm", desc: "Listelerde iki durum ayrı sekmelerde gösterilsin.", type: "switch", default: true }
    ].map(p => ({ ...p, code: nextCode() }));

    // ==== render ====
    function cellHTML(cls, inner) { return `<div class="yd-cell ${cls}">${inner}</div>`; }
    function renderRow(p) {
        const id = `p_${p.code.replace(/\W/g, "")}`;
        let input = "";
        if (p.type === "switch") {
            input = `<label class="yd-switch" for="${id}">
                 <input type="checkbox" id="${id}" class="form-check-input" ${p.default ? "checked" : ""}/>
                 <span>Açık</span>
               </label>`;
        } else if (p.type === "number") {
            input = `<input type="number" id="${id}" class="form-control"
                      value="${p.default ?? ""}" ${p.min ? `min="${p.min}"` : ""}
                      ${p.max ? `max="${p.max}"` : ""} ${p.step ? `step="${p.step}"` : ""} />`;
        } else if (p.type === "select") {
            const opts = (p.options || []).map(o => `<option value="${o.value}" ${o.value === p.default ? "selected" : ""}>${o.label}</option>`).join("");
            input = `<select id="${id}" class="form-select">${opts}</select>`;
        } else {
            input = `<input type="text" id="${id}" class="form-control" value="${p.default ?? ""}" />`;
        }
        return `
      <div class="yd-row">
        <div class="yd-card" data-name="${p.name.toLowerCase()}" data-code="${p.code}">
          ${cellHTML("yd-name", `<div>${p.name}<div class="small mt-1">${p.code}</div></div>`)}
          ${cellHTML("yd-desc", `<p class="yd-desc">${p.desc}</p>`)}
          ${cellHTML("yd-input", input)}
        </div>
      </div>
    `;
    }
    function renderAll(list) { form.innerHTML = list.map(renderRow).join(""); }
    renderAll(params);

    // ==== search by name ====
    function normalize(s) { return (s || "").toLocaleLowerCase("tr-TR"); }
    function doSearch(q) {
        const t = normalize(q);
        form.querySelectorAll(".yd-card").forEach(card => {
            const n = card.getAttribute("data-name") || "";
            const show = !t || n.includes(t);
            card.parentElement.classList.toggle("yd-hidden", !show);
        });
        clearBtn.classList.toggle("d-none", !(t && t.length));
    }
    search?.addEventListener("input", e => doSearch(e.target.value));
    clearBtn?.addEventListener("click", () => {
        search.value = ""; doSearch("");
        form.querySelectorAll(".yd-hidden").forEach(el => el.classList.remove("yd-hidden"));
        clearBtn.classList.add("d-none");
    });

    // ==== save (mock) ====
    function showToast(msg) {
        if (!toast) return;
        toast.textContent = msg;
        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 2200);
    }

    document.getElementById("ydSave")?.addEventListener("click", () => {
        const data = [];
        form.querySelectorAll(".yd-card").forEach(card => {
            const code = card.getAttribute("data-code");
            const name = card.getAttribute("data-name");
            const input = card.querySelector("input,select,textarea");
            let value = null;
            if (input) {
                value = (input.type === "checkbox") ? input.checked : input.value;
            }
            data.push({ code, name, value });
        });
        console.log("Kaydedilen veriler:", data);
        // TODO: Backend POST burada bağlanacak.
        showToast("Ayarlar kaydedildi.");
    });
})();
