function sleep(d){
  for(var t = Date.now();Date.now() - t <= d;);
}

function generate_photo_div(url) {
    //sleep(5000) // for test loading bubble
    $.ajaxSetup({async: false});
    var main = "";
    $.getJSON(url, function (data) {
        $.each(data, function (key, val) {
            main += '<a target="_blank" href="/samer/' + val['author_uid'] + '"><img class="lazy" data-original="' + val['photo'] + '" src="/static/image/ajax-loader.gif" weight=512 height=256 /></a>';
        });
    });
    document.getElementById("container").innerHTML = main;
    document.getElementById("loading-bubble").remove();
}