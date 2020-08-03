// search UIN
$("#search-bar button").on("click", function() {
    var uin = $("#search-bar input").val();
    if (uin !== "" && uin !== undefined) {
        $.ajax({
            url: "search",
            type: "POST",
            contentType: 'application/json',
            data: JSON.stringify({
                "uin": uin
            }),
            success: function (data) {
                alert(data.user);
            },
            error: function (jqXHR, exception) {
                alert(jqXHR.responseText);
            }
        });
    }
    else{
        alert("You have to enter UIN to search!");
    }

});