function openPopup(url, next) {
    /* Open popup to Google or Facebook auth */

    var w = 700;
    var h = 500;
    var left = 100;
    var top = 100;

    var settings = 'height=' + h + ',width=' + w + ',left=' + left + ',top=' + top + ',resizable=yes,scrollbars=yes,toolbar=no,menubar=no,location=yes,directories=no,status=yes';
    url += "?next=" + next;

    window.open(url, "popup", settings);
}

if (!String.prototype.format) {
    String.prototype.format = function() {
        /* format functionality for strings */
        var args = arguments;
        return this.replace(/{(\d+)}/g, function(match, number) {
            return typeof args[number] !== 'undefined' ? args[number] : match;
        });
    };
}

$.mobileDevice = (/android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(navigator.userAgent.toLowerCase()));


var range = function (n) {
    return Array.apply(null, Array(n)).map(function (_, i) {return i;});
};
