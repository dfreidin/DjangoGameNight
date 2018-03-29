$(document).ready(function(){
    $(".show_hide").click(function(){
        linked = "." + $(this).attr("linked-element");
        $(linked).slideToggle();
        return false;
    });
});