# -*- coding: utf-8 -*-
"""
    inyoka.core.forms.fields
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Form fields based on WTForms.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from wtforms.fields import BooleanField as OrigBooleanField, DecimalField, DateField, \
    DateTimeField, FieldList, FloatField, FormField, HiddenField, \
    IntegerField, PasswordField, RadioField, SelectField, SelectMultipleField, \
    SubmitField, TextField, TextAreaField, FileField
from wtforms.fields import Field
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
from inyoka.core.api import _
from inyoka.core.forms import widgets
from inyoka.core.forms import validators

date_re = re.compile(r'(?P<year>[0-9]{4})([-/.])(?P<month>[0-9]{2})\2'
                     r'(?P<day>[0-9]{2})$')


class BooleanField(OrigBooleanField):
    def _value(self):
        if self.raw_data:
            return unicode(self.raw_data[0])
        else:
            return u'true'


class HiddenIntegerField(IntegerField):
    widget = widgets.HiddenInput()


class RecaptchaField(Field):
    widget = widgets.RecaptchaWidget()

    #: Set if validation fails.
    recaptcha_error = None

    def __init__(self, *args, **kwargs):
        super(RecaptchaField, self).__init__(*args, **kwargs)
        self.validators.append(validators.is_valid_recaptcha())


class ModelSelectField(QuerySelectField):
    """
    Similar to QuerySelectField, only for model classes.

    Using this field is only meaningful when using scoped sessions in
    SQLAlchemy, because otherwise model instances do not know how to make
    queries of themselves. This field is simply a convenience for using
    `Model.query` as the factory for QuerySelectMultipleField.

    """
    def __init__(self, label=u'', validators=None, model=None, **kwargs):
        assert model is not None, "Must specify a model."
        query_factory = lambda: model.query
        super(ModelSelectField, self).__init__(label, validators,
            query_factory=query_factory, **kwargs)


class CommaSeparated(Field):
    widget = widgets.TextInput()

    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(',')]
        else:
            self.data = []


class AutocompleteField(QuerySelectMultipleField):
    """A modified comma separated field that renders jQuery autocomplete"""
    widget = widgets.TokenInput()

    def _value(self):
        if self.data:
            return u', '.join(self.get_label(obj) for obj in self.data)
        else:
            return u''

    def process_formdata(self, valuelist):
        self._formdata = set(filter(None, [x.strip() for x in valuelist[0].split(',')]))

    def _get_data(self):
        formdata = self._formdata
        if formdata is not None:
            data = []
            for pk, obj in self._get_object_list():
                label = self.get_label(obj)
                if not formdata:
                    break
                elif label in formdata:
                    formdata.remove(label)
                    data.append(obj)
            if formdata:
                self._invalid_formdata = True
            self._set_data(data)
        return self._data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)


class RangeField(FieldList):
    """
    This field renders a field twice, it's `data` is a tuple of the two values.
    By default, the field is a common-or-garden `TextField`; for changing this,
    inherit this class and set `_unboud_field` (see `DatePeriodField`).
    """
    widget = widgets.RangeWidget(u'Between %s and %s')
    _unbound_field = TextField('')

    def __init__(self, *args, **kwargs):
        FieldList.__init__(self, self._unbound_field, *args, min_entries=2,
            **kwargs)

    @property
    def data(self):
        if self.entries[0].data or self.entries[1].data:
            return (self.entries[0].data, self.entries[1].data)


class DatePeriodField(RangeField):
    _unbound_field = TextField('', [validators.Regexp(date_re,
            message=_(u'Must be a valid date')), validators.Optional()])
