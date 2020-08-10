// search UIN
$("#search-bar input").keypress(function (e) {
    if (e.which === 13) {
        var uin = $(this).val();
        if (uin !== "" && uin !== undefined) {
            $.ajax({
                url: "search",
                type: "POST",
                contentType: 'application/json',
                data: JSON.stringify({
                    "uin": uin
                }),
                success: function (data) {
                    updateCurrentStatus(data.user)
                },
                error: function (jqXHR, exception) {
                    $("#current-status").hide().empty();
                    alert(jqXHR.responseText);
                }
            });
        } else {
            alert("You have to enter UIN to search!");
        }
    }
});

// search UIN
$("#search-bar button").on("click", function () {
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
                updateCurrentStatus(data.user)
            },
            error: function (jqXHR, exception) {
                $("#current-status").hide().empty();
                alert(jqXHR.responseText);
            }
        });
    } else {
        alert("You have to enter UIN to search!");
    }
});

// quarantine button
$("#quarantine").on("click", function(){
    submitActions("quarantine");
});

// isolate button
$("#isolate").on("click", function(){
    submitActions("isolate");
});

// release button
$("#release").on("click", function(){
    submitActions("release");
});

// update the status of the searched user (pink area)
function updateCurrentStatus(user) {
    $("#current-status").show().empty().append(
        `<h4>` + user['given_name'] + ", " + user['family_name'] + `</h4>
        <h4>UIN: ` + user['uin'] + `</h4>
        <p>Current Entry Status = ` + user['status'] + `</p>`
    );
}

// action buttons
function submitActions(action){
    var uin = $("#search-bar input").val();
    if (uin !== "" && uin !== undefined) {
        $.ajax({
            url: action,
            type: "POST",
            contentType: 'application/json',
            data: JSON.stringify({
                "uin": uin
            }),
            success: function (data) {
                 alert("Successfully "+ action  + " the current user: " + data['user']['given_name'] + ", "
                + data['user']['family_name'] +"!")
                updateCurrentStatus(data.user)
            },
            error: function (jqXHR, exception) {
                $("#current-status").hide().empty();
                alert(jqXHR.responseText);
            }
        });
    } else {
        alert("You have to enter the UIN in search box first!");
    }
}

