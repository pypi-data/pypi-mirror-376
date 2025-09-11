from collective.contact_behaviors import _
from plone.autoform.directives import read_permission
from plone.autoform.interfaces import IFormFieldProvider
from plone.schema.email import Email
from plone.supermodel import directives
from plone.supermodel import model
from zope import schema
from zope.interface import provider


PERMISSION = "collective.contact_behaviors.contact_info.view"


@provider(IFormFieldProvider)
class IContactInfo(model.Schema):
    directives.fieldset(
        "contact_info",
        label=_("label_contact_info", default="Contact Information"),
        fields=("contact_phone", "contact_email", "contact_website"),
    )

    read_permission(
        contact_phone=PERMISSION, contact_email=PERMISSION, contact_website=PERMISSION
    )

    contact_phone = schema.TextLine(
        title=_("label_contact_phone", default="Phone Number"),
        description=_(
            "description_contact_phone",
            default=("Internationalized phone number with country code and area code"),
        ),
        required=False,
    )

    contact_email = Email(
        title=_("label_contact_email", default="E-mail"), required=False
    )

    contact_website = schema.URI(
        title=_("label_contact_website", default="Website"), required=False
    )
