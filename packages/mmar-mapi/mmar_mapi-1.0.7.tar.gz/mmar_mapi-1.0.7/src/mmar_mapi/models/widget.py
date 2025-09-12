from typing import Self, Literal

from more_itertools import chunked
from pydantic import BaseModel, model_validator


class Widget(BaseModel):
    type: Literal["widget"] = "widget"
    buttons: list[list[str]] | None = None
    ibuttons: list[list[str]] | None = None

    @model_validator(mode="after")
    def check(self) -> Self:
        if not self.buttons and not self.ibuttons:
            raise ValueError("Empty widget is not allowed!")
        if not self.ibuttons:
            return self
        for row in self.ibuttons:
            for btn in row:
                if ":" in btn:
                    continue
                raise ValueError(f"Expected buttons like `<callback>:<caption>`, found: {btn}")
        return self

    @staticmethod
    def make_inline_buttons(ibuttons: dict[str, str], by=1) -> "Widget":
        return _make_inline_buttons(ibuttons=ibuttons, by=by)


def _make_inline_buttons(ibuttons: dict[str, str], by=1) -> "Widget":
    ibs0 = [f"{key}:{val}" for key, val in ibuttons.items()]
    ibs = list(chunked(ibs0, n=by))
    res = Widget(ibuttons=ibs)
    return res
