# Pynums
A library for adding configurable Enum-type objects to python!
I do understand that these aren't exactly Enums, but they work as them all the same :D

If you have any issues or suggestions go to the github issues page and raise one! If you have any ideas the are very much welcome :D

PyPi: https://pypi.org/project/Pynums/ | Github: https://github.com/Ninesideddevelopment/Pynums

## How to create Enums:
    from Pynums import Enum
    
    MyEnum1 = Enum()
    MyEnum2 = Enum()
    
Output:

    hello world

Enums can also be created like this, allowing for more specific arguments:

    from Pynums import Enum
    
    class MyEnum1(Enum):
        def __init__(self, requiredarg, **kwargs):
            self.requiredarg = requiredarg
            super().__init__(**kwargs) # **kwargs are here so that you can add required arguments, as well as any other arguments you may want per Enum.
    
    myenum = MyEnum1(requiredarg="hello", otherarg="world") # Note that "otherarg" will not have any auto-completion as it is created at runtime.
    
    print(myenum.requiredarg, myenum.otherarg)

Output:

    hello world

This allows for functions/methods to take in a Enum, but can also have a value that is only present with that Enum, without having to give the functions/methods an extra parameter.
