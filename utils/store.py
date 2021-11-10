from dataclasses import dataclass
class Store:
    def __init__(self):
        pass

@dataclass
class StoreItem:
    id_: int
    price: int

