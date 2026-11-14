"""Piccole compatibilità tra lo Streamlit del PC e quello di stlite (Android)."""

from __future__ import annotations


def ensure_component_runtime() -> None:
    """
    I componenti st.components.v2 chiamano ``Runtime.exists()`` e
    ``Runtime.instance()``. Nello Streamlit di stlite (app Android) la classe
    Runtime non li ha: ci sono solo le funzioni ``streamlit.runtime.exists()``
    e ``streamlit.runtime.get_instance()``. Qui li aggiungiamo alla classe,
    così i componenti funzionano anche sul telefono. Sul PC non cambia nulla.
    """
    from streamlit import runtime
    from streamlit.runtime import Runtime

    if not hasattr(Runtime, "exists") and hasattr(runtime, "exists"):
        Runtime.exists = staticmethod(runtime.exists)
    if not hasattr(Runtime, "instance") and hasattr(runtime, "get_instance"):
        Runtime.instance = staticmethod(runtime.get_instance)
