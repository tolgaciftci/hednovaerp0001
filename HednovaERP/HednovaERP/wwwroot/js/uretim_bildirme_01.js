

function getDataWithAjax() {
    $.ajax({

        url: '/UretimBildirme01/GetData',
        type: 'GET',
        success: function (data) {
            console.log(data);
        },
        error: function (x, status, err) {
            console.log(err);
        }
    })
}