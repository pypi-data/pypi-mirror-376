
class EnumMember:
    """Base class for all enum members."""
    def __init__(self, **kwargs):


        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"
