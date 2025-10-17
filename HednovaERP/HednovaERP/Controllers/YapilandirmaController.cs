using Microsoft.AspNetCore.Mvc;
using HednovaERP.Models;

namespace HednovaERP.Controllers
{
    public class YapilandirmaController : Controller
    {
        public IActionResult Liste()
        {
            return View();
        }

        // /Yapilandirma/Detay?evrakno=YPLN-0001
        public IActionResult Detay(string evrakno)
        {
            var model = new YapilandirmaDetayVM
            {
                EvrakNo = string.IsNullOrWhiteSpace(evrakno) ? "YPLN-0000" : evrakno.Trim(),
                Isim = "Üretim",
                Aciklama = "Üretim modülüne ait yapılandırmaları buradan yönetebilirsiniz."
            };
            return View(model);
        }
    }
}
