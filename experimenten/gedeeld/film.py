"""De indeling van de filmpjes in fragmenten."""

import numpy as np
import pandas as pd


def fragments(frames: pd.DataFrame) -> pd.DataFrame:
    """Per bestand: bij welk fragment het hoort (Video 1 tot en met 8), hoeveel seconden het bestand na het begin van het
    fragment begint (fragment 2, 4 en 8 staan in delen), en hoe lang het hele fragment is."""
    rows, start = [], {}
    for video, f in frames.groupby("video", sort=True):
        group = "Video " + video.split(" [")[0].split()[-1].rstrip("abc")
        rows.append({"video": video, "fragment": group, "offset": start.get(group, 0.0)})
        start[group] = start.get(group, 0.0) + len(f) * float(np.median(np.diff(f["time_s"])))
    result = pd.DataFrame(rows)
    result["lengte"] = result["fragment"].map(start)
    return result
