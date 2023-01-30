$(function () {
    // Force all external links to open in new tab
    var links = document.querySelectorAll('a')
    for (var i = 0; i < links.length; i++) {
        var link = links[i]
        loc = link.getAttribute("href")
        if (loc != null && loc.startsWith("http") && !loc.startsWith("http://data.subak.org")) {
            link.setAttribute("target", "_blank")
        }
    }
})