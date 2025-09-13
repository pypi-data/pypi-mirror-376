from ..entities.error_message import ErrorMessage
from ..interfaces.error_formatter import ErrorFormatter


class TelegramFormatter(ErrorFormatter):
    def format_message(self, error: ErrorMessage) -> str:
        formatted_message = f"""🔴 {error.level.value} 
        📅 {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        📁 {error.file_path}
        💬 {error.message}"""

        if error.stack_trace:
            formatted_message += f"""📋 Stack trace: {error.stack_trace}"""

        return formatted_message
