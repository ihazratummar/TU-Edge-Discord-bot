from enum import  Enum



class DbConstant(Enum):
    DATABASE_NAME = "TUEdge"

    """
    Collection Enums
    """
    USER_COLLECTION ="user_collection"


class TradeType(Enum):
    CRYPTO = "crypto"
    CRYPTO_FUTURES = "crypto futures"
    STOCK = "stock"
    FOREX = "forex"
    INDICES_FUTURES = "indices futures"

tradeType = list(TradeType)
type_list = [trade_type.value for trade_type in tradeType]