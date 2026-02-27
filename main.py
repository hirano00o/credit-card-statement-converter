import os
import re
import sys
import unicodedata
from enum import Enum

import pandas as pd


class CardType(Enum):
    AMEX = 1
    VISA = 2


def _get_type(file_path: str) -> CardType:
    meta = pd.read_csv(file_path, encoding="cp932", nrows=1, header=None)
    column_len = meta.shape[1]
    # ヘッダーの列数で判別
    # アメックスは8列
    # 三井住友Visaは3列
    return CardType.AMEX if column_len == 8 else CardType.VISA


def _read_csv(card_type: CardType) -> pd.DataFrame:
    columns = []
    if card_type == CardType.AMEX:
        columns = ["date", "processed", "content", "user", "id", "pay", "pay_in_overseas", "rate"]
    if card_type == CardType.VISA:
        columns = ["date", "content", "amount", "kubun1", "kubun2", "pay", "note"]

    return pd.read_csv(
        file,
        encoding="cp932",
        header=0,
        skipfooter=1,
        names=columns,
        engine="python",
    )


def _translate(df: pd.DataFrame, card_type: CardType) -> pd.DataFrame:
    df["content"] = unicodedata.normalize("NFKC", str(df["content"]))
    if card_type == CardType.VISA:
        if type(df["note"]) != float:
            df["content"] += " (" + unicodedata.normalize("NFKC", str(df["note"])) + ")"
        df["content"] = re.sub(" +", " ", str(df["content"]))

    return df


def _save(df: pd.DataFrame, card_type: CardType, name: str):
    if card_type == CardType.AMEX:
        df.to_csv("amex_" + name, header=False, index=True)
    if card_type == CardType.VISA:
        df.to_csv("mitsui_" + name, header=False, index=True)


if len(sys.argv) < 2:
    print("変換するファイルを1つ以上、指定してください")
    os._exit(1)

for file in sys.argv[1:]:
    card_type = _get_type(file_path=file)

    df = _read_csv(card_type)
    df = df.apply(_translate, card_type=card_type, axis=1)
    df = df.filter(items=["date", "content", "pay"])
    df = df.set_index("date")
    df = df.filter(
        regex="(19|20)([0-9]{2}/(?!((0[2469]|11)/31)|02/(29|30))((0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01]))|([02468][048]|[13579][26])/02/29)",
        axis=0,
    )
    print(df)
    _save(df, card_type, os.path.basename(file))
