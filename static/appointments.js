$(document).ready(function(){
    // default to only show today otherwise too much data
    var today = new Date();
    var yyyy = today.getFullYear();
    var mm = today.getMonth() > 9 ? today.getMonth() + 1 : '0' + (today.getMonth() +1);
    var dd = today.getDate() > 10 ? today.getDate() : '0' + today.getDate();
    var date =  yyyy + "-" + mm + "-" + dd;
    $("#date-select").val(date).prop("min", date);

    $.ajax({
        url: "my-appointment",
        type: "GET",
        success: function (data) {
           if ("claimed_slot" in data){
               $(".highlight").show();
                displayMyAppointment(data.claimed_slot)
            }
        },
        error: function (jqXHR, exception) {
            console.log(jqXHR.responseText);
        }
    });

    $.ajax({
        url: "list",
        type: "GET",
        data: {
            "date": date,
        },
        success: function (data) {
           if ("available_slots" in data){
                updateAppointmentTable(data.available_slots)
            }
        },
        error: function (jqXHR, exception) {
            alert(jqXHR.responseText);
        }
    });
});

$("#location-select").on("change", function () {
    filterOnChange();
});

$("#date-select").on("change", function () {
    filterOnChange();
});

$("#timeslot-select").on("change", function () {
    filterOnChange();
});

$("#submit-appointment").on("click", function() {
    // check if ONE appointment has been selected
    var selectedElement = $("#available-appointments").find('tbody').find("input:checked");
    if (selectedElement.length === 1){
        var appt_id = $(selectedElement[0]).val();
        $.ajax({
            url: "submit",
            type: "POST",
            contentType: 'application/json',
            data:JSON.stringify({
                "appt_id":appt_id
            }),
            success: function (data) {
                alert("your appointment:" + JSON.stringify(data) + "has successfully been booked!")
                displayMyAppointment(data.claimed_slot);
            },
            error: function (jqXHR, exception) {
                alert(jqXHR.responseText);
            }
        });
    }
    else{
        alert("You have to select ONE available appointment!");
    }

});

/**
 * cancelling
 */
$("#my-appointment").on("click", "button", function() {
    var appt_id = $(this).attr('id');
    $.ajax({
        url: "cancel",
        type: "DELETE",
        contentType: 'application/json',
        data:JSON.stringify({
            "appt_id":appt_id
        }),
        success: function (data) {
            alert("your appointment:" + JSON.stringify(data) + "has successfully been canceled!");
            window.location.href=window.location.href;
        },
        error: function (jqXHR, exception) {
            alert(jqXHR.responseText);
        }
    });
});

function filterOnChange() {
    var location = $("#location-select option:selected").val();
    if ($("#date-select").val() !== "" && $("#date-select").val() !== undefined) {
        var date = $("#date-select").val();
    } else {
        var date = "";
    }

    var time = $("#timeslot-select option:selected").val();
    $.ajax({
        url: "list",
        type: "GET",
        data: {
            "location": location,
            "date": date,
            "time": time,
        },
        success: function (data) {
            if ("available_slots" in data) {
                updateAppointmentTable(data.available_slots)
            }
        },
        error: function (jqXHR, exception) {
            alert(jqXHR.responseText);
        }
    });
}

function updateAppointmentTable(available_slots) {
    $("#available-appointments").find('tbody').empty();
    $.each(available_slots, function (i, item) {
        $("#available-appointments").find('tbody').append(
            "<tr>" +
            "<td>" +
            "<input type=\"checkbox\" id=\"" + item.id + "\" name=\"submit\" value=\"" + item.id + "\">" +
            "</td>" +
            "<td>" + item.location + "</td>" +
            "<td>" + item.date + "</td>" +
                "<td>" + item.time + "</td>"
            + "</tr>");
    })
}

function displayMyAppointment(claimed_slot) {
    $("#my-appointment").find('tbody').empty();
    if (!$.isEmptyObject(claimed_slot)){
        $.each(claimed_slot, function (i, item) {
            $("#my-appointment").find('tbody').append(
                "<tr>" +
                "<td>" + item.location + "</td>" +
                "<td>" + item.date + "</td>" +
                "<td>" + item.time + "</td>" +
                "<td><button class=\"btn btn-danger\" type=\"submit\" id=\"" + item.id + "\"" +
                " value=\"" + item.id + "\">Cancel</button></td>" +
                "</tr>");
        });
    }
}