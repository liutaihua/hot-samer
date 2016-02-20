$(function () {
    $(function () {
        $("img.lazy").lazyload({
//                    event: "sporty",
            effect: "fadeIn",
            effectTime: 200,
            threshold: 200
        });
    });
    $(window).bind("load", function () {
        var timeout = setTimeout(function () {
            $("img.lazy").trigger("sporty")
        }, 5000);
    });
});