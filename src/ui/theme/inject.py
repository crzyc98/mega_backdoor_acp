"""
Streamlit CSS Injection Helper.

Provides utilities to inject custom CSS into Streamlit pages.
"""

import streamlit as st

from src.ui.theme.css import get_all_css


def inject_theme_css() -> None:
    """
    Inject the complete theme CSS into the current Streamlit page.

    Should be called once at the start of app.py after st.set_page_config().
    """
    css = get_all_css()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def inject_custom_css(css: str) -> None:
    """
    Inject arbitrary custom CSS into the current page.

    Args:
        css: CSS string to inject
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def inject_html(html: str) -> None:
    """
    Inject arbitrary HTML into the current page.

    Args:
        html: HTML string to inject
    """
    st.markdown(html, unsafe_allow_html=True)
