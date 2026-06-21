```diff
diff --git a/app.py b/app.py
index 2d9a111..8bd42aa 100644
--- a/app.py
+++ b/app.py
@@
 import streamlit as st
+def _speaker_split_defaults():
+    if "speaker_segments" not in st.session_state:
+        st.session_state["speaker_segments"] = []
+    if "speaker_labels" not in st.session_state:
+        st.session_state["speaker_labels"] = {}
+
+def _save_speaker_segments(segments):
+    st.session_state["speaker_segments"] = segments
+    st.session_state["speaker_labels"] = {
+        item["id"]: item.get("speaker", "unknown")
+        for item in segments
+    }
+
+def render_speaker_split_panel():
+    _speaker_split_defaults()
+    st.subheader("Speaker split")
+    edited = st.data_editor(st.session_state["speaker_segments"])
+    if st.button("Apply speaker split"):
+        _save_speaker_segments(edited)
+        st.success("Saved")
+
 def render_editor():
     st.title("Shorts editor")
     mode = st.sidebar.radio(
         "Mode",
-        ["Layers", "Manual captions", "Sound"],
+        ["Layers", "Manual captions", "Sound", "Speaker split"],
     )
@@
     if mode == "Sound":
         render_sound_panel()
+    if mode == "Speaker split":
+        render_speaker_split_panel()
```
