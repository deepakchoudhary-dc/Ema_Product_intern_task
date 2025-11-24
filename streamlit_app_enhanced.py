"""Helper entrypoint that reuses `streamlit_app.py`.
Run `streamlit run streamlit_app.py` for the full experience.
This file imports the main module so that legacy links keep working.
"""

import streamlit_app  # noqa: F401  (re-export side effects)
