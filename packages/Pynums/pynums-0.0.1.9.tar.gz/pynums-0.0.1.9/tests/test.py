class MyEnum(Enum):
    A = {"": 1, "h": 2}
    B = 1, 2


print(MyEnum.A)
print(MyEnum.B)