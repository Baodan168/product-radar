"""带状态的字段值。

audit-report P3：缺失数据、抓取失败和真实数值现在混在一起——
字段缺失时默认成空串或 0，页面上「利润 0」和「利润算失败了」
长得一模一样，但这两件事对选品判断完全不是一回事。

所以凡是可能拿不到的数据，都用 Field 包一层，让渲染层能区分：
    ok              有值，正常显示
    missing         数据源里就没有这个字段
    failed          取数过程报错了（error 里带原因）
    not_applicable  这个场景下本来就不该有值
"""
from dataclasses import dataclass, field
from typing import Any, Optional

OK = 'ok'
MISSING = 'missing'
FAILED = 'failed'
NOT_APPLICABLE = 'not_applicable'


@dataclass
class Field:
    value: Any = None
    status: str = MISSING
    error: Optional[str] = None

    @property
    def is_ok(self) -> bool:
        return self.status == OK

    def to_dict(self) -> dict:
        return {'value': self.value, 'status': self.status, 'error': self.error}


def ok(value) -> Field:
    return Field(value=value, status=OK)


def missing(reason: str = None) -> Field:
    return Field(value=None, status=MISSING, error=reason)


def failed(error: str) -> Field:
    return Field(value=None, status=FAILED, error=str(error))


def not_applicable(reason: str = None) -> Field:
    return Field(value=None, status=NOT_APPLICABLE, error=reason)


@dataclass
class CardData:
    """一张卡的数据。

    卡整体可能失败（比如数据源文件读不到），这时 status 不是 ok，
    渲染层显示「数据不可用 + 原因」，而不是显示一堆 0。
    """
    status: str = OK
    error: Optional[str] = None
    payload: dict = field(default_factory=dict)

    @property
    def is_ok(self) -> bool:
        return self.status == OK

    @classmethod
    def fail(cls, error: str) -> 'CardData':
        return cls(status=FAILED, error=str(error))

    @classmethod
    def absent(cls, reason: str) -> 'CardData':
        return cls(status=MISSING, error=reason)
