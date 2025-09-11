{% if obj.display %}

..
    SPDX-License-Identifier: CC-BY-SA-4.0
    Copyright Tumult Labs 2025

.. py:{{ obj.type }}:: {{ obj.short_name }}{% if obj.args %}({{ obj.args }}){% endif %}

   {% if obj.imported %}
   :canonical: {{ obj.obj["original_path"] }}
   {% endif %}

   {% if obj.bases %}

   {% set visible_bases = obj.bases|reject("is_mixin_class")|reject("is_base_builder")|list %}
   {% if visible_bases %}
   Bases: {% for base in visible_bases %}{{ base|link_objs }}{% if not loop.last %}, {% endif %}{% endfor %}
   {% endif %}

   {% endif %}

   {% if obj.docstring %}
   {{ obj.docstring|prepare_docstring|indent(3) }}
   {% endif %}

   {% set is_exception = obj.type is equalto ("exception") %}
   {% set visible_classes = obj.classes|selectattr("is_private_member", "false")|selectattr("rendered")|list %}
   {% set visible_attributes = obj.attributes|selectattr("is_private_member", "false")|selectattr("rendered")|list %}
   {% set visible_properties = obj.properties|selectattr("is_private_member", "false")|selectattr("rendered")|list %}
   {% set visible_methods = obj.methods|selectattr("is_private_member", "false")|selectattr("rendered")|list %}
   {% set num_visible_items = visible_classes|length + visible_attributes|length + visible_methods|length %}

   {% if not is_exception %}
   {% if num_visible_items > 10 %}
   {% if visible_classes %}
   .. list-table:: Classes

      {% for klass in visible_classes %}
      * - :class:`.{{ klass.short_name }}`
        - {{ klass.summary }}
      {% endfor %}

   {% endif %}

   {% for klass in visible_classes %}
   {{ klass.rendered|indent(3) }}
   {% endfor %}

   {% if visible_attributes %}
   .. list-table:: Attributes

      {% for attribute in visible_attributes %}
      * - :attr:`.{{ attribute.short_name }}`
        - {{ attribute.summary }}
      {% endfor %}

   {% endif %}

   {% if visible_properties %}
   .. list-table:: Properties

      {% for property in visible_properties %}
      * - :attr:`{{ property.name }}`
        - {{ property.summary }}
      {% endfor %}

   {% endif %}
   {% if visible_methods %}
   .. list-table:: Methods

      {% for method in visible_methods %}
      * - :meth:`.{{ method.short_name }}`
        - {{ method.summary }}
      {% endfor %}
   {% endif %}
   {% endif %}

   {% for attribute in visible_attributes %}
   {{ attribute.rendered|indent(3) }}
   {% endfor %}

   {% for property in visible_properties %}
   {{ property.rendered|indent(3) }}
   {% endfor %}

   {% if obj.methods | selectattr("short_name", "equalto", "__init__") | reject("nodoc") | list %}
   .. automethod:: __init__
   {% endif %}

   {% for method in visible_methods %}
   {{ method.rendered|indent(3) }}
   {% endfor %}
   {% endif %}
   {% endif %}
