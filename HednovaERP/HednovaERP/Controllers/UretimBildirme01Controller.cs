using Microsoft.AspNetCore.Mvc;



namespace HednovaERP.Controllers
{
    public class UretimBildirme01Controller : Controller
    {
        public IActionResult Index()
        {
            return View();
        }

        [HttpGet]
        public ActionResult GetData()
        {
            var data = new { Message = "Hello World!" };
            return new JsonResult(data);
        }


    }
}
