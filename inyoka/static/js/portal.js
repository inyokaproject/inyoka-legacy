$(document).ready(function() {
  $('#random_password_link').click(function() {
    Inyoka.callJSONService("dev/portal/get_random_password", function(data) {
      $('#new_password')
        .attr('value', data.password);
      $('#new_password_confirm')
        .attr('value', data.password);
      if ( ! $('#random_password').length ) {
        $('#random_password_link')
          .html(_('Generate another'))
          .before(_('Generated Password: <code id="random_password"></code> | '));
      }
      $('#random_password').html(data.password);
    });
    return false;
  });
});
