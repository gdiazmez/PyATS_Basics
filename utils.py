"""
Common utility elements for test cases

"""

from unicon.core.errors import SubCommandFailure


def apply_template(uut, templates_dir, template_name, **kwargs):
    """
    Apply jinja2 template to a device configuration
    :param uut: Device object
    :param templates_dir: Templates directory
    :param template_name: Template name
    :param kwargs: key-value pairs of jinja2 template variables
    :return: (bool: success, str: message) Tuple indicating whether template was applied successfully and message
    """
    template = uut.api.get_jinja_template(templates_dir=templates_dir, template_name=template_name)

    if template is None:
        return False, 'Template not found: {template}'.format(template=template_name)

    try:
        uut.api.change_configuration_using_jinja_templates(template=template, **kwargs)
    except SubCommandFailure as e:
        return False, str(e)

    return True, 'Succeeded'
