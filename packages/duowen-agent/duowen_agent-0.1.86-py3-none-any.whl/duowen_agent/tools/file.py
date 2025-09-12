import re
from typing import Optional

from pydantic import BaseModel, Field

from duowen_agent.agents.state import Resources
from duowen_agent.error import ToolError
from duowen_agent.llm import OpenAIChat, tokenizer, MessagesSet
from duowen_agent.tools.base import BaseTool
from duowen_agent.utils.core_utils import stream_to_string, remove_think


def file_path_repair(file_path):
    if file_path.startswith("/workspace/"):
        return file_path
    elif file_path.startswith("/") and not file_path.startswith("/workspace/"):
        raise ToolError("文件路径必须以 /workspace/ 开头")
    else:
        return "/workspace/" + file_path


class CreateFileParams(BaseModel):
    file_path: str = Field(
        description="Path to the file to be created, relative to /workspace (e.g., 'src/main.py')"
    )
    content: str = Field(description="The content to write to the file")
    permissions: Optional[str] = Field(
        description="File permissions in octal format (e.g., '644')", default="644"
    )


class CreateFile(BaseTool):
    name: str = "create-file"
    description: str = (
        "Create a new file with the provided contents at a given path in the workspace. The path must be relative to /workspace (e.g., 'src/main.py' for /workspace/src/main.py)"
    )
    parameters = CreateFileParams

    def __init__(self, resources: Resources, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resources = resources

    def _run(self, file_path, content, permissions="644") -> str:
        _file_path = file_path_repair(file_path)
        self.resources.file_add(_file_path, content, permissions)
        return f"File '{_file_path}' created successfully."


class FileStrReplaceParams(BaseModel):
    file_path: str = Field(
        description="Path to the target file, relative to /workspace (e.g., 'src/main.py')"
    )
    old_str: str = Field(description="Text to be replaced (must appear exactly once)")
    new_str: str = Field(description="Replacement text")


class FileStrReplace(BaseTool):
    name: str = "file-str-replace"
    description: str = (
        "Replace specific text in a file. The file path must be relative to /workspace (e.g., 'src/main.py' for /workspace/src/main.py). Use this when you need to replace a unique string that appears exactly once in the file."
    )
    parameters = FileStrReplaceParams

    def __init__(self, resources: Resources, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resources = resources

    def _run(self, file_path, old_str, new_str) -> str:
        _file_path = file_path_repair(file_path)
        if not self.resources.file_exists(_file_path):
            return f"文件 '{_file_path}' 不存在."
        if self.resources.file_str_replace(_file_path, old_str, new_str):
            return f"替换文件 '{_file_path}' 内容成功"
        else:
            return f"内容 '{old_str}' 未在文件内 '{_file_path}'发现."


class FileFullRewriteParams(BaseModel):
    file_path: str = Field(
        description="Path to the file to be rewritten, relative to /workspace (e.g., 'src/main.py')"
    )
    content: str = Field(
        description="The new content to write to the file, replacing all existing content"
    )
    permissions: Optional[str] = Field(
        description="File permissions in octal format (e.g., '644')", default="644"
    )


class FileFullRewrite(BaseTool):
    name: str = "file-full-rewrite"
    description: str = (
        "Completely rewrite an existing file with new content. The file path must be relative to /workspace (e.g., 'src/main.py' for /workspace/src/main.py). Use this when you need to replace the entire file content or make extensive changes throughout the file."
    )
    parameters = FileFullRewriteParams

    def __init__(self, resources: Resources, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resources = resources

    def _run(self, file_path, content, permissions="664") -> str:
        _file_path = file_path_repair(file_path)
        if not self.resources.file_exists(_file_path):
            return f"文件 '{_file_path}' 不存在."
        self.resources.file_full_rewrite(_file_path, content, permissions)
        return f"文件 '{_file_path}' 完全重写成功."


class FileDeleteParams(BaseModel):
    file_path: str = Field(
        description="Path to the file to be deleted, relative to /workspace (e.g., 'src/main.py')"
    )


class FileDelete(BaseTool):
    name: str = "file-delete"
    description: str = (
        "Delete a file at the given path. The path must be relative to /workspace (e.g., 'src/main.py' for /workspace/src/main.py)"
    )
    parameters = FileDeleteParams

    def __init__(self, resources: Resources, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resources = resources

    def _run(self, file_path) -> str:
        _file_path = file_path_repair(file_path)
        if not self.resources.file_exists(_file_path):
            return f"文件 '{_file_path}' 不存在."
        self.resources.file_delete(_file_path)
        return f"文件 '{_file_path}' 删除成功."


class GrepFileParams(BaseModel):
    file_path: str = Field(
        description="Path to the file to search in, relative to /workspace (e.g., 'src/main.py')"
    )
    pattern: str = Field(description="The pattern to search for (regular expression)")
    max_results: Optional[int] = Field(
        description="Maximum number of results to return (default: 20)", default=20
    )


class GrepFile(BaseTool):
    name: str = "grep-file"
    description: str = (
        "Search for a pattern in a file using regular expressions. The file path must be relative to /workspace (e.g., 'src/main.py' for /workspace/src/main.py). Returns matching lines with line numbers."
    )
    parameters = GrepFileParams

    def __init__(self, resources: Resources, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resources = resources

    def _run(self, file_path, pattern, max_results=20) -> str:
        _file_path = file_path_repair(file_path)
        if not self.resources.file_exists(_file_path):
            return f"文件 '{_file_path}' 不存在."

        # 读取文件内容
        file_content = self.resources.read_all_file(_file_path)
        lines = file_content.split("\n")

        # 搜索匹配行
        matches = []
        for line_num, line in enumerate(lines, 1):  # 使用 enumerate 获取行号，从1开始
            if re.search(pattern, line):
                matches.append(f"行 {line_num}: {line}")  # 这里包含了行号信息
                if len(matches) >= max_results:
                    break

        if not matches:
            return f"在文件 '{_file_path}' 中未找到模式 '{pattern}' 的匹配项。"

        result = f"在文件 '{_file_path}' 中找到 {len(matches)} 个匹配模式 '{pattern}' 的结果:\n\n"
        result += "\n".join(matches)  # 这里会显示所有匹配行及其行号

        if len(matches) == max_results:
            result += (
                f"\n\n(显示前 {max_results} 个结果，使用 max_results 参数查看更多)"
            )

        return result


class FileReadParams(BaseModel):
    file_path: str = Field(
        description="Path to the file to be read, relative to /workspace (e.g.,'src/main.py')"
    )
    start_line: int = Field(description="Start line number to read from")
    end_line: int = Field(description="End line number to read to")


class FileRead(BaseTool):
    name: str = "file-read"
    description: str = (
        "Read a file at the given path. The path must be relative to /workspace (e.g.,'src/main.py' for /workspace/src/main.py)"
    )
    parameters = FileReadParams

    def __init__(self, resources: Resources, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resources = resources

    def _run(self, file_path, start_line, end_line) -> str:
        _file_path = file_path_repair(file_path)
        if not self.resources.file_exists(_file_path):
            return f"文件 '{_file_path}' 不存在."
        data = self.resources.read_file(_file_path, start_line, end_line)

        if tokenizer.chat_len(data["content"]) <= 4000:

            return f"""读取文件 {_file_path}
文件开始行号: {data["start_line"]}
文件结束行号: {data["end_line"]}
文件总行数: {data["total_lines"]}
文件内容: {data["content"]}
"""
        else:
            return f"文件 '{_file_path}' 内容过长，无法读取."


class AskFileParams(BaseModel):
    file_path: str = Field(
        description="Path to the file to be read, relative to /workspace (e.g.,'src/main.py')"
    )
    question: str = Field(description="The question to ask about the file")


class AskFile(BaseTool):
    name: str = "ask-file"
    description: str = (
        "Ask a question about a file at the given path. The path must be relative to /workspace (e.g.,'src/main.py' for /workspace/src/main.py)"
    )
    parameters = AskFileParams

    def __init__(self, resources: Resources, llm: OpenAIChat, **kwargs):
        super().__init__(**kwargs)
        self.resources = resources
        self.llm = llm

    def _run(self, file_path, question) -> str:
        _file_path = file_path_repair(file_path)
        if not self.resources.file_exists(_file_path):
            return f"文件 '{_file_path}' 不存在."

        data = self.resources.read_all_file(_file_path)
        if tokenizer.chat_len(data) <= (self.llm.token_limit - 20000):
            _prompt = MessagesSet()

            _prompt.add_system(
                f"""
**角色**：你是一个智能助手，名叫Miss R。  
**任务**：基于知识库信息进行总结并回答用户问题。  

**要求与限制**：  
- **严禁虚构内容**，尤其是数字信息。  
- 若知识库信息与用户问题无关，**直接表示**：抱歉，未检索到相关信息。  
- 回答需使用 **Markdown 格式文本**。  
- 使用**用户提问的语言**回答。  
- **严禁虚构内容**，尤其是数字信息。  

### 来自知识库的信息  
{data}  
以上为知识库提供的信息。
"""
            )
            _prompt.add_user(question)
            res = stream_to_string(self.llm.chat_for_stream(_prompt))
            return remove_think(res)
        else:
            return f"文件 '{_file_path}' 内容过长，无法读取."
