function res_read() {
    var d1 = document.getElementById('article' + article_count);
    var resp = ankerset(article);

    d1.insertAdjacentHTML('afterbegin', "<pre>" + resp + "</pre>");
}

function ankerset(article) {
    var pattern_anker = /&gt;&gt;[0-9]{1,}/g;
    let resp = article;
    if (resp.match(pattern_anker)) {
        resp = resp.replace(pattern_anker, replace_insert)
    }

    else {
        //console.log("sippai")
    }
    return resp;
}

function replace_insert(match) {
    let jumplink1 = '<span class="back_anker"><a href=/thread/' + thread + "/";
    let jumplink2 = " class=\"reply_article\">";
    let jumplink3 = "</a></span>";
    let article_no = match.slice(8);
    let return_match = match;

    return (jumplink1 + article_no + jumplink2 + match + jumplink3);
}

function strIns(str, idx, val) {
    let res = str.slice(0, idx) + val + str.slice(idx);
    return res;
}

function escapeHtml(str) {
    str = str.replace(/&/g, '&amp;');
    str = str.replace(/</g, '&lt;');
    str = str.replace(/>/g, '&gt;');
    str = str.replace(/"/g, '&quot;');
    str = str.replace(/'/g, '&#39;');
    return str;
};

function message_html(article_count, name, pub_date, userid, article) {
    let article_escape = escapeHtml(article);
    let article_tip = ankerset(article_escape);

    let res_html = '<div class="post">' +
        '<span class="number">' + article_count + '</span>' +
        '<b><span class="name">' + name + '</span></b>' +
        '<span class="date">' + pub_date + '</span>' +
        '<span class="uid">   ID:' + userid + '</span>' +
        '<div class="message">' +
        '<span class="article">' +
        '<div id="article' + article_count + '"></div>' +
        '<pre>' + article_tip + '</pre>' +
        '</span>' +
        '</div>' +
        '</div>' +
        '<br>'

    return res_html
}

$(document).on(
    'mouseenter', 'div[id*="tooltips"]', function () {
        $(".tooltips").not(this).remove();
    });

$(document).on(
    'mouseleave', ".tooltips", function () {
        $(this).remove();
    });

$(document).on(
    'mouseleave', ".back_anker", function () {
        let flag = false;
        let jump_link_temp = $(this).text();
        let jump_link = jump_link_temp.replace(/>>/g, "");
        let this_tooltips_id = '#tooltips_' + jump_link;
        setTimeout(function () {
            if ($(this_tooltips_id + ':hover').length === 0) {
                $(this_tooltips_id).remove();
            }
        }, 500);
    });

$(document).on(
    'mouseenter', ".back_anker", function () {
        //試験環境
        var article_url = "https://jobbs.herokuapp.com/thread_json/"
        let url = location.pathname;
        let url_split = url.split('/');
        var thread = url_split[2];
        let jump_link_temp = $(this).text();
        let jump_link = jump_link_temp.replace(/>>/g, "");
        var tooltipdiv = "tooltips_"

        //already exist stop
        if (url_split[1] != "thread") {
            return 0;
        }
        if (document.getElementById(tooltipdiv + jump_link) != null) {
            return 0;
            console.log("exist!");
        }

        $.ajax({
            url: article_url + thread + "/" + jump_link,
            type: 'POST',
            dataType: 'json',
            contentType: false,
            processData: false,
        })

            .done((data) => {
                let divid = tooltipdiv + data.Article.article_count;
                let reply_article_position = $(this).offset();
                let tooltips_offset = new Object();
                tooltips_offset.left = reply_article_position.left + 30;
                tooltips_offset.top = reply_article_position.top;
                $(".anker_tooltip").append('<div id=' + divid + ' class="tooltips">' + message_html(data.Article.article_count, data.Article.name, data.Article.pub_date, data.Article.userid, data.Article.article) + '</div>');
                $('#' + divid).offset(tooltips_offset)
            })
            .fail((XMLHttpRequest, textStatus, errorThrown) => {
                console.log("XMLHttpRequest : " + XMLHttpRequest.status);
                console.log("textStatus     : " + textStatus);
                console.log("errorThrown    : " + errorThrown.message);
            })
            .always((data) => {
                //console.log("alway");
            })
    });
