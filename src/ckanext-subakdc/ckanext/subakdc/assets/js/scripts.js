Mousetrap.bind('/', function() {
    document.getElementById("field-main-search").focus();
    return false;   
});

Mousetrap.bind('esc', function() {
    document.getElementById("field-main-search").blur();
    return false;   
});