import streamlit as st
from pathlib import Path

# Mark route as not optimized when parameters change
def mark_route_as_not_optimized():
    st.session_state.route_optimized = False

def load_css(file_name: str, **kwargs) -> str:
        """
        Load CSS content from a file.

        Args:
        ----
            file_name (str): The name of the CSS file to load.
            **kwargs: Additional arguments to inject into the CSS.

        Returns:
        -------
            str: The CSS content as a string.

        """
        with Path(file_name).open() as css_file:
            style = css_file.read().format(**kwargs)
            return f"""
                <style>
                    {style}
                </style>
                """