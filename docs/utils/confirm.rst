=============================
Inyoka Confirmation Utilities
=============================

.. automodule:: inyoka.utils.confirm


.. _confirm-usage:

Confirmation Utilities Usage
============================

Firstly we create a handler that handles the confirmation
stuff that needs to be done:

.. sourcecode:: python

    def change_email(request):
        if request.method == 'POST':
            c = Confirm('change_email', 7, {
                    'user': request.user.id,
                    'email': request.POST['email']
                })
            db.session.add(c)
            db.session.commit()
            send_mail(request.user, 'Confirm your email address',
                      'Please click this link: %s' % c.url)

Well, once we've done that we can integrate that into our view function:

.. sourcecode:: python

    @view('change_email')
    def set_email(data):
        user = User.query.get(data['user'])
        if user is None:
            flash('This user has been deleted!')
        else:
            user.email = data['email']
            flash('Your email has been changed to %s' % data['email'])
        return redirect_to('portal/index')

.. _confirm-api:


Often used functions
--------------------

.. autofunction:: register_confirm

.. autofunction:: store_confirm

.. autofunction:: call_confirm

Exceptions
----------

.. autoexception:: Expired
