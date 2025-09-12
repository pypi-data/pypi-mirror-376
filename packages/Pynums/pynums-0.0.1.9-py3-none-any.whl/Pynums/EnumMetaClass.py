
from EnumMember import EnumMember

class EnumMetaClass(type):
    def __new__(mcls, name, bases, attrs):

        a = {}
        for name, value in attrs.items():
            if not name.startswith("_") and not isinstance(value, EnumMember):
                if isinstance(value, dict):
                    _a = {}
                    for _name, _value in value.items():
                        _a[_name] = _value
                    a[name] = EnumMember()
                    a[name].__dict__.update(_a)
                else:
                    a[name] = EnumMember()
                    a[name].__setattr__("value", value)

        return super().__new__(mcls, name, bases, a)

