```diff
diff --git a/app.py b/app.py
index 2d9a111..5cc42bb 100644
--- a/app.py
+++ b/app.py
@@
 import streamlit as st
+from src.ui.speaker_split_panel import render_speaker_split_panel
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

diff --git a/src/ui/speaker_split_panel.py b/src/ui/speaker_split_panel.py
new file mode 100644
--- /dev/null
+++ b/src/ui/speaker_split_panel.py
@@
+from dataclasses import dataclass, field
+
+
+@dataclass
+class SpeakerSplitState:
+    segments: list[dict] = field(default_factory=list)
+    labels: dict[str, str] = field(default_factory=dict)
+
+    def apply(self, segments: list[dict]) -> None:
+        self.segments = segments
+        self.labels = {
+            item["id"]: item.get("speaker", "unknown")
+            for item in segments
+        }
+
+
+def render_speaker_split_panel(state: SpeakerSplitState | None = None):
+    state = state or SpeakerSplitState()
+    return {
+        "title": "Speaker split",
+        "segments": state.segments,
+        "on_apply": state.apply,
+    }

diff --git a/tests/ui/test_speaker_split_panel.py b/tests/ui/test_speaker_split_panel.py
new file mode 100644
--- /dev/null
+++ b/tests/ui/test_speaker_split_panel.py
@@
+from src.ui.speaker_split_panel import SpeakerSplitState, render_speaker_split_panel
+
+
+def test_speaker_split_state_owns_labels():
+    state = SpeakerSplitState()
+    state.apply([{"id": "s1", "speaker": "narrator"}])
+    assert state.labels == {"s1": "narrator"}
+
+
+def test_render_exposes_apply_handler():
+    panel = render_speaker_split_panel(SpeakerSplitState())
+    assert panel["title"] == "Speaker split"
+    assert callable(panel["on_apply"])
```
