(function($) {


/* TokenWidget
 *
 * A widget with autocompletion and the ability to enter multiple values.
 *
 * :param url: The callback url which is used for the autocompletion
 *             (must be a JSON service).
 * :param options: A dictionary with some additional options.
 * */

$.fn.TokenWidget = function (url, options) {
    var settings = $.extend({
        url: url,
        separator: ' '
    }, options);

    return this.each(function () {
        var list = new $.TokenWidgetImpl(this, settings);
    });
};

$.TokenWidgetImpl = function(input, settings) {
    var inputbox = $(input)
        .addClass('TokenWidget')
        .attr('autocomplete', 'off')
        .focusin(function () {
            if (results.children().length)
                results.fadeIn();
        })
        .focusout(function () {
            results.fadeOut();
        })
        .keydown(function (event) {
            if (event.which == 38 || event.which == 40) {
                if (selected) {
                    selected.removeClass('selected');
                    if (event.which == 38)
                        selected = selected.prev().length ? selected.prev() : null;
                    else if (event.which == 40)
                        selected = selected.next().length ? selected.next() : selected;
                }
                else if (event.which == 40)
                    selected = results.find('li[class!="meta"]:first');
                if (selected)
                    selected.addClass('selected');
                return false;
            }
            else if (event.which == 13 && selected) {
                selected.click();
                return false;
            }
            else {
                if (timer)
                    clearTimeout(timer);
                timer = setTimeout(search, 1500);
                inputbox.addClass('search');
            }
        });

    var results = $('<ul class="TokenWidget-results" />')
        .insertAfter(inputbox)
        .hide();
    results.width(inputbox.outerWidth() - (results.outerWidth() - results.width() + 1));

    var selected = null;
    var timer = null;
    var cache = [];

    /* lookup tokens for the auto completion */
    function search() {
        var tokens = inputbox.val().split(settings.separator);
        var query = tokens[tokens.length-1];
        if (!query) {
            inputbox.removeClass('search');
            results.html('').hide();
            return;
        }
        if (cache[query])
            showResults(cache[query], query);
        else {
            $.getJSON(settings.url, {'q': query}, function(data) {
                cache[query] = data;
                showResults(data, query);
            });
        }
    }

    /* display the retrieved data in a list box below the input field */
    function showResults(data, query) {
        results.html('');
        selected = null;
        results.show();
        for (var i=0; i < data.length; ++i) {
            var name = data[i]['name'];
            var highlight = name.match(new RegExp('^' + re_quote(query), 'i'));
            if (highlight) {
                results.append($('<li />')
                        .text(name.substring(highlight[0].length))
                        .prepend($('<strong />').text(highlight[0])));
            } else
                results.append($('<li />').text(name));
            var val = data[i]['id'];
            results.children().last().click(function() {
                addItem(val);
            });
        }
        if (data.length == 0)
            results.append('<li class="meta">No results found</li>');
        inputbox.removeClass('search');
    }

    /* add a selected item from the results popup to the input field */
    function addItem(value) {
        tokens = inputbox.val().split(settings.separator);
        tokens.splice(tokens.length-1, 1, value);
        inputbox.val(tokens.join(settings.separator) + settings.separator);
        results.html('').fadeOut();
    }

    /* quote a regular expression */
    function re_quote(str) {
        return (str+'').replace(/([\\\.\+\*\?\[\^\]\$\(\)\{\}\=\!\<\>\|\:])/g, "\\$1")
    }
};

})(jQuery);
