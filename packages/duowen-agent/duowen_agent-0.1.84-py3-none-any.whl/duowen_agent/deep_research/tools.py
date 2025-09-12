import logging
import traceback

from pydantic import BaseModel, Field

from duowen_agent.tools.base import BaseTool
from duowen_agent.tools.entity import ContentToolResult


class ChapterContentConfirmationParams(BaseModel):
    content: str = Field(description="为特定章节编写的完整内容")


class ChapterContentConfirmationTool(BaseTool):

    name: str = "chapter_content_confirmation"
    description: str = "将根据已确认的大纲所编写的单个章节内容发送出去进行确认"
    parameters = ChapterContentConfirmationParams

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(self, content) -> ContentToolResult:
        try:
            # 确认章节内容的逻辑
            # 这里可以添加具体的确认逻辑
            return ContentToolResult(content="已确认的章节内容")
        except Exception as e:
            logging.error(
                f"Failed to confirm chapter content: {e}, traceback: {traceback.format_exc()}"
            )
            return ContentToolResult(content="无法确认章节内容")


class WritingPlanConfirmationParams(BaseModel):
    content: str = Field(description="包含用户请求、主题和关键信息的初始内容")


class WritingPlanConfirmationTool(BaseTool):

    name: str = "writing_plan_confirmation"
    description: str = (
        "基于用户提供的初始内容或主题，生成一份详细的报告大纲（写作计划），并将此计划发送进行确认。"
    )
    parameters = WritingPlanConfirmationParams

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(self, content) -> ContentToolResult:
        try:
            # 生成报告大纲的逻辑
            # 这里可以添加具体的生成逻辑
            return ContentToolResult(content="已确认的写作计划")
        except Exception as e:
            logging.error(
                f"Failed to generate writing plan: {e}, traceback: {traceback.format_exc()}"
            )
            return ContentToolResult(content="无法生成写作计划")
