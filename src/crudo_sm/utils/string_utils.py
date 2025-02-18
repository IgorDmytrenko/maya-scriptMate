"""
    String manipulation function
"""

import re

def convert_to_title_case(name: str) -> str:
    """
        Convert PasclaCase or camelCase string to separated string
        param: string = name
    """
    return ''.join(' ' + char if char.isupper() else char for char in name).strip()


def format_menu_name(title: str) -> str:
    pattern = r"[^\w]|\_+" 
    return re.sub(
            pattern, 
            "_", 
            title
        )

