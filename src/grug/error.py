from typing import Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SourceSpan:
    line: int
    offset: int
    
    def get_column(self, source_text: str) -> int:
        column = 1;
        if self.offset >= len(source_text):
            raise Exception("expected span to be within source code bounds")

        while column <= self.offset and source_text[self.offset - column] != '\n':
            column += 1;
        
        return column

    def get_source_line(self, source_text: str) -> str:
        line_start_index = self.offset;
        line_end_index = self.offset;
        if self.offset >= len(source_text):
            raise Exception("expected span to be within source code bounds")

        if source_text[line_start_index] == '\n':
            line_start_index -= 1;

        while line_start_index >= 0 and source_text[line_start_index] != '\n':
            line_start_index -= 1;
        while line_end_index < len(source_text) and source_text[line_end_index] != '\n':
            line_end_index += 1;
        
        return source_text[line_start_index + 1:line_end_index].lstrip()

@dataclass
class GrugError(Exception):
    function_name: str
    file_path: Path
    source_line: str
    span: SourceSpan
    error_message: str
    error_string: str
    
    @staticmethod
    def new_tokenizer_error(file_path: Path, source_text: str, err_span: SourceSpan, error_message: str) -> "GrugError":
        line = err_span.line
        column = err_span.get_column(source_text)
        source_line = err_span.get_source_line(source_text)
                
        error_string = f"""\
  in ({file_path}:{line}:{column})\n\
Error: {error_message}\n\
{line} $ {source_line}\
"""
        return GrugError(
            function_name = "",
            file_path = file_path,
            source_line = source_line,
            span = err_span,
            error_message = error_message,
            error_string = error_string
        )
        
    @staticmethod
    def new_compile_error(file_path: Path, current_function: Optional[str], source_text: str, err_span: SourceSpan, error_message: str) -> "GrugError":
        if current_function == None:
            current_function = "member scope"
        line = err_span.line
        column = err_span.get_column(source_text)
        source_line = err_span.get_source_line(source_text)
                
        error_string = f"""\
  in {current_function} ({file_path}:{line}:{column})\n\
Error: {error_message}\n\
{line} $ {source_line}\
"""
        return GrugError(
            function_name = current_function,
            file_path = file_path,
            source_line = source_line,
            span = err_span,
            error_message = error_message,
            error_string = error_string
        )

    @staticmethod
    def new_file_name_error(file_path: Path, error_message: str) -> "GrugError":
        source_line = file_path
        err_span = SourceSpan(1, 0)

        error_string = f"""\
Error: {error_message}\n\
$  {source_line}\
"""
        return GrugError(
            function_name = "",
            file_path = file_path,
            source_line = source_line,
            span = err_span,
            error_message = error_message,
            error_string = error_string
        )

    def __str__(self) -> str:
        return self.error_string
