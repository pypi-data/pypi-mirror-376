from pydantic import BaseModel
from typing import List, Optional, Literal

class TestCaseStep(BaseModel):
    """
    测试步骤
    """
    step_number: int  # 步骤编号
    action: str  # 执行操作
    expected_result: str  # 期望结果


class TestCase(BaseModel):
    """
    单个测试用例
    """
    path: str
    name: str
    steps: List[TestCaseStep]
    priority: Literal["p0","p1","p2","p3"]
    preconditions: Optional[str] = None
    remark: Optional[str] = None


class TestCaseList(BaseModel):
    """
    测试用例集
    """
    feature: str
    test_cases: List[TestCase]