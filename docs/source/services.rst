========
Services
========

Services… Services these days represent an API for other applications beyond
our own or implement interfaces for our JavaScript code to implement AJAX
services and such stuff.

Inyoka supports these kind of services in an easy way.  To define a service or
API is nearly the same work as to define a view controller or an admin provider.

Let's assume we have the following model::

    class Tag(db.Model):
        __tablename__ = 'forum_tag'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(20), nullable=False, index=True, unique=True)

Now we want to implement an API to return all known tags.  We need define a
:class:`~inyoka.core.routing.IServiceProvider` to do so.  It's API is quite
the same as you know from :class:`~inyoka.core.routing.IController` as it's
nearly the same thing.  Both implement APIs, for human beings on the one hand
and for machines and applications on the other hand.

Before we define such an service provider we prepare our model to be
serializable::

    class Tag(db.Model, SerializableObject):
        __tablename__ = 'forum_tag'

        # serializer properties
        object_type = 'forum.tag'
        public_fields = ('id', 'name')

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(20), nullable=False, index=True, unique=True)

As you see we just mixed in a new class:
:class:`~inyoka.core.serializer.SerializableObject`.  This class tells our
internal serializer what ID the model has and what columns to serialize.  This
is required to have an interface for various serializers.  For now Inyoka
supports some kind of debug serializer that returns HTML but it supports JSON and
XML too.

Now that we made our model serializable we can define the service provider::

    class ForumServiceController(IServiceProvider):
        name = 'forum'

        url_rules = [
            Rule('/get_tags/', endpoint='get_tags'),
            Rule('/get_tags/<int:limit>', endpoint='get_tags'),
        ]

        @service('get_tags')
        def get_tags(self, request, limit=10):
            tags = Tag.query.limit(limit).all()
            return tags

That's it, you can now call ``forum.inyoka.local:5000/_api/get_tags`` and see
the debug output.  To see how the serialized output performs in JSON or XML,
you can add ``?format=json`` or ``?format=xml`` to the url and see how it
looks.

Isn't that easy?

Admin Service API
=================

To define a service API for the admin pages only is nearly the same API.
Since our admin interface is filled by multiple applications the service API
needs to be adapted to the common admin API.  A simple example::

    class ForumAdminServiceProvider(IAdminServiceProvider):
        name = 'forum'

        url_rules = [
            Rule('/get_tags/', endpoint='get_tags'),
        ]

        @service('get_tags')
        def get_tags(self, request):
            q = request.args.get('q')
            if not q:
                tags = Tag.query.all()[:10]
            else:
                tags = Tag.query.filter(Tag.name.startswith(q))[:10]
            return tags

As you see the only difference is that you inherit from
:class:`~inyoka.admin.api.IAdminServiceProvider` instead of
:class:`~inyoka.core.serializer.IServiceProvider` and define the `name`
attribute properly as you do on all other admin interfaces too.


Services API
~~~~~~~~~~~~

This is an automatic generated list of all registered services.

.. inyokaservices::
