/* Change ellipsis elements of a pagination to a link, which when clicked
 * turns into an input field where any page number to be changed to can be
 * entered.
 *
 * For this the pagination module on server side provides an url template,
 * where the page number can be inserted. This is passed to JavaScript via
 * an input hidden field. If a pagination does not provide a template input,
 * no link is created.
 */


$(function () {
  $('.pagination .ellipsis').each(function (i) {

    var restore_ellipsis = (function (ellipsis) {
      /* restore the ellipsis to its original state */
      ellipsis.children('form').remove();
      ellipsis.children('a').show().focus();
      return false;
    })

    var ellipsis = $(this);
    if ( !ellipsis.next('input.url-template').size() )
      /* for ellipsis elements where there is no template for whatever reason:
       * continue with the next one.  */
      return true;

    ellipsis.wrapInner('<a href="#" />')
    ellipsis.children('a').click(function () {
      var link = $(this);
      link.hide().after('<form action="#"><input size="2"/></form>');
      link.next('form')
        .css('display', 'inline')
        .submit(function () {
          var page = parseInt(Number(this.elements[0].value));

          if ( isNaN(page) || page < 1 ) {
            return restore_ellipsis(ellipsis);
          }

          if ( page == 1) {
            /* we cannot always use the template here, but since there is
             * always a link to the first page we use that.  */
            page1 = $(this).parent().siblings('.page1');
            if ( page1.hasClass('current') )
              return restore_ellipsis(ellipsis);
            else
              window.location.href = page1[0].href;

          } else {
            template = $(this).parent().next('input.url-template')[0].value
            window.location.href = template.replace(/!/, page);
          }

          return false;
        })
        .children('input').focus();
      return false;
    });
  });
});
