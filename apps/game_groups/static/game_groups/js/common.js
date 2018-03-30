function get_game_table() {
    $.ajax({
        url: $(this).parent().attr("action"),
        method: "post",
        data: $(this).parent().serialize(),
        success: function(res){
            $("#game_table_div").html(res);
        }
    });
}

$(document).ready(function(){
    $(document).on("click", ".show_hide", function(){
        linked = "." + $(this).attr("linked-element");
        $(linked).slideToggle();
        return false;
    });
    $(document).on("click", "#select_all_games", function(e){
        $(".user_game_choices").prop("checked", this.checked);
    });
    $("#filter_form").submit(function(e){
        e.preventDefault();
        get_game_table();
    });
    $("#filter_form").children().change(get_game_table);
    // $("#add_game, #add_from_collection").submit(function(e){
    //     e.preventDefault();
    //     $.ajax({
    //         url: $(this).parent().attr("action"),
    //         method: "post",
    //         data: $(this).parent().serialize(),
    //         success: function(res){
    //             $("#filter_form").submit();
    //         }
    //     });
    // });
    $("#group_name_form").submit(function(e){
        e.preventDefault()
        $.ajax({
            url: $(this).attr("action"),
            method: "post",
            data: $(this).serialize(),
            success: function(res){
                $("title").text(res);
                $("h1").text(res);
                $("#nameEditButton").dropdown("toggle");
            }
        });
    });
    $(document).on("submit", "#new_group_member", function(e){
        e.preventDefault()
        $.ajax({
            url: $(this).attr("action"),
            method: "post",
            data: $(this).serialize(),
            success: function(res){
                $(".members").html(res);
            }
        });
    });
    $(document).on("click", ".remove_group_member", function(e){
        $.ajax({
            url: $(this).attr("href"),
            method: "get",
            success: function(res){
                $(".members").html(res);
            }
        });
        return false;
    });
    $("#random_game_button").click(function(){
        $.ajax({
            url: $(this).attr("action"),
            method: "get",
            success: function(res){
                $(".modal-body").html(res);
            }
        });
    });
    $("#bgg_game_search").submit(function(e){
        e.preventDefault();
        $("#game_search_results").html("<img src='"+$(this).attr("spinner")+"' width='100'>")
        $.ajax({
            url: $(this).attr("action"),
            method: "post",
            data: $(this).serialize(),
            success: function(res){
                $("#game_search_results").html(res);
            }
        });
    });
    $("#bgg_user_search").submit(function(e){
        e.preventDefault();
        $("#user_search_results").html("<img src='"+$(this).attr("spinner")+"' width='100'>")
        $.ajax({
            url: $(this).attr("action"),
            method: "post",
            data: $(this).serialize(),
            success: function(res){
                $("#user_search_results").html(res);
            }
        });
    });
});