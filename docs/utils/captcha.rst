========
Captchas
========

.. automodule:: inyoka.utils.captcha

    .. todo::

        Audio captchas are not yet supported but an implementation
        is on the roadmap.

    .. note::

        Uses some code of PyCAPTCHA by Micah Dowty.


.. _captcha-api:

Captcha API
===========

.. autoclass:: Captcha
    :members: render_image, get_response

.. autofunction:: generate_word

.. autofunction:: random_color
