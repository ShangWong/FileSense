import os
from dataclasses import dataclass
from enum import Enum

import fitz
import pandas as pd
import mammoth


def _get_file_extension(file_path: str):
    # Use os.path.splitext to split the file path into the base name and the extension
    _, file_extension = os.path.splitext(file_path)
    # Return the file extension without the leading dot
    return file_extension[1:].lower() if file_extension else None


class FileType(Enum):
    TEXT = 1
    IMAGE = 2


@dataclass
class PreprocessedFile:
    file_type: FileType
    content: str


class Preprocessor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def process(self) -> str:
        raise NotImplementedError("Subclass must implement abstract method")

    @classmethod
    def create(cls, file_path: str):
        ext = _get_file_extension(file_path)
        if ext in ("txt", "py", "ini", "md"):
            return TxtPreprocessor(file_path)
        elif ext == "pdf":
            return PdfPreprocessor(file_path)
        elif ext in ("xls", "xlsx"):
            return XlsPreprocessor(file_path)
        elif ext in ("doc", "docx"):
            return DocPreprocessor(file_path)
        else:
            raise NotImplementedError(f"Preprocessor for {ext} is not implemented.")


class TxtPreprocessor(Preprocessor):
    def __init__(self, file_path: str):
        super().__init__(file_path)

    def process(self) -> str:
        with open(self.file_path, "r", encoding="utf-8") as file:
            return PreprocessedFile(file_type=FileType.TEXT, content=file.read().replace("\n", " "))


class PdfPreprocessor(Preprocessor):
    def __init__(self, file_path: str):
        super().__init__(file_path)

    def process(self) -> str:
        doc = fitz.open(self.file_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        return PreprocessedFile(file_type=FileType.TEXT, content=text.replace("\n", " "))


class XlsPreprocessor(Preprocessor):
    def __init__(self, file_path: str):
        super().__init__(file_path)

    def process(self) -> str:
        # Read the Excel file
        df = pd.read_excel(self.file_path)

        # Convert the DataFrame to an HTML table
        html_table = df.to_html(index=False)

        return PreprocessedFile(file_type=FileType.TEXT, content=html_table)


class DocPreprocessor(Preprocessor):
    def __init__(self, file_path: str):
        super().__init__(file_path)

    def process(self) -> str:
        with open(self.file_path, "rb") as doc_file:
            result = mammoth.convert_to_markdown(doc_file)
            markdown = result.value  # The generated markdown
        return PreprocessedFile(file_type=FileType.TEXT, content=markdown.replace("\n", " "))
