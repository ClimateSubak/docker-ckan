$(function () {
    // Force all external links to open in new tab
    var links = document.querySelectorAll('a')
    console.log(links)
    for (var i = 0; i < links.length; i++) {
        var link = links[i]
        loc = link.getAttribute("href")
        console.log(loc)
        if (loc != null && loc.startsWith("http") && !loc.startsWith("http://data.subak.org")) {
            link.setAttribute("target", "_blank")
            console.log('^ external')
        }
    }
})