import umap
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import re
import pandas as pd

from ..coremap import Coremap


# ----------------------------
# Helpers
# ----------------------------
def natural_key(name):
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', name)]

def typename(o):
    return o.__class__.__name__

def children_of(o):
    return getattr(o, "children", []) or []

def short(o):
    if typename(o) == "Core":
        return getattr(o, "ranking_algo", "Core")
    elif typename(o) == "Clustered_Core":
        return getattr(o, "cluster_algo", "Clustered_Core")
    elif typename(o) == "Propagated_Data":
        return getattr(o, "propagate_algo", "Propagated")
    return typename(o)

def cores(corespect):
    return [c for c in children_of(corespect) if typename(c) == "Core"]

def clustered_children(core):
    return [c for c in children_of(core) if typename(c) == "Clustered_Core"]

def propagated_children(clustered_core):
    return [p for p in children_of(clustered_core) if typename(p) == "Propagated_Data"]

def build_global_color_map(corespect):
    """Collect all labels across Clustered_Core.core_labels and Propagated_Data.final_labels and assign a stable color."""
    all_labels = set()
    for co in cores(corespect):
        for cc in clustered_children(co):
            labs_cc = getattr(cc, "core_labels", [])
            if labs_cc is not None and len(np.asarray(labs_cc)) > 0:
                all_labels.update(map(str, np.unique(labs_cc)))
            for pd in propagated_children(cc):
                labs_pd = getattr(pd, "final_labels", [])
                if labs_pd is not None and len(np.asarray(labs_pd)) > 0:
                    all_labels.update(map(str, np.unique(labs_pd)))
    all_labels = sorted(all_labels, key=natural_key)
    palette = (
        px.colors.qualitative.Plotly
        + px.colors.qualitative.D3
        + px.colors.qualitative.Set1
        + px.colors.qualitative.Set2
        + px.colors.qualitative.Set3
        + px.colors.qualitative.T10
        + px.colors.qualitative.Dark24
        + px.colors.qualitative.Light24
    )
    if not all_labels:
        return {}
    return {lab: palette[i % len(palette)] for i, lab in enumerate(all_labels)}

# ----------------------------
    # Color map builder (for overriding labels if given to detailed_viewer)
# ----------------------------
def _color_map_from_labels(lbls):
    labs_sorted = sorted(map(str, np.unique(lbls)), key=natural_key)
    palette = (
        px.colors.qualitative.Plotly
        + px.colors.qualitative.D3
        + px.colors.qualitative.Set1
        + px.colors.qualitative.Set2
        + px.colors.qualitative.Set3
        + px.colors.qualitative.T10
        + px.colors.qualitative.Dark24
        + px.colors.qualitative.Light24
    )
    return {lab: palette[i % len(palette)] for i, lab in enumerate(labs_sorted)}

# ----------------------------
# Trace factory
# ----------------------------
def traces_for_object(o, color_map,global_init_embedding=None, labels=None,mode='three_steps'):
    """
    Build plotly traces for object o.
    - Core: local subset embedding via viz_core(o); hide base
    - Clustered_Core: local subset embedding via viz_core(o); hide base
    - Propagated_Data: multiple local subset embeddings via viz_layer_prop(o); one slider-step per returned embedding; hide base

    If `labels` is provided (length == o.X.shape[0]), use it to label/color ALL overlay traces (Core / Clustered_Core / Propagated)
    """
    traces = []
    t = typename(o)


    if t == "Core":
        idx = np.asarray(getattr(o, "core_nodes", []), int)
        if idx.size:
            tr = go.Scatter(
                x=np.array([]), y=np.array([]),
                mode="markers",
                name="core_nodes",
                marker=dict(color="red", size=5, line=dict(width=0), opacity=0.6),
                visible=False
            )
            tr.meta = dict(uses_local_coords=True)  # local → hide base
            traces.append(tr)



    elif t == "Clustered_Core":
        idx = np.asarray(getattr(o, "core_nodes", []), int)
        labs = np.asarray(getattr(o, "core_labels", []), int)
        if idx.size:
            empty_df = pd.DataFrame(columns=["x", "y"])
            fig = px.scatter(
                empty_df,
                x="x", y="y",
                labels={"x": "UMAP-1", "y": "UMAP-2"}
            )
            for tr in fig.data:
                tr.name = f"{tr.name}"
                tr.visible = False
                tr.marker.update(size=5)
                tr.meta = dict(uses_local_coords=True)  # local → hide base
                traces.append(tr)




    elif t == "Propagated_Data":
        # Expect viz_layer_prop(o) -> list of dicts: {node_index: (x, y)}
        if labels is None:
            labs_full = np.asarray(getattr(o, "final_labels", []), int)
        else:
            labs_full = np.asarray(labels, int)

        from collections import Counter
        print(Counter(o.final_labels))
        print(Counter(labs_full))

        cmap = Coremap(X=o.X, round_info=o.round_info, labels=o.final_labels,global_init_embedding=global_init_embedding,mode=mode)

        emb_list = []
        emb_keys = []
        dict_viz = cmap.anchored_map()  # keys "cores", "layer1", "layer2", ...
        # first generate cores_clustered
        emb_list.append(dict_viz["cores"])
        for keys_idx, key_name in enumerate(dict_viz.keys()):
            if keys_idx !=0:
                emb_keys.append(key_name)
            emb_list.append(dict_viz[key_name])

        for step_idx, emb_dict in enumerate(emb_list):
            if not emb_dict:
                continue
            # stable order
            idxs = np.fromiter(emb_dict.keys(), dtype=int, count=len(emb_dict))
            XY = np.array(list(emb_dict.values()), dtype=float)
            if labs_full.size and idxs.size:
                labs_step = labs_full[idxs]
                if step_idx == 0:
                    # Neutral core nodes with single legend entry; hidden by default (slider will show)
                    tr = go.Scatter(
                        x=XY[:, 0],
                        y=XY[:, 1],
                        mode="markers",
                        name="core_nodes",
                        marker=dict(color="black", size=5, opacity=0.3),
                        visible=False,
                        showlegend=True
                    )
                    tr.meta = dict(uses_local_coords=True, pd_step=step_idx)
                    traces.append(tr)
                else:
                    label_key = "labels" if labels is not None else "final_labels"
                    fig = px.scatter(
                        x=XY[:, 0], y=XY[:, 1],
                        color=labs_step.astype(str),
                        labels={"x": "UMAP-1", "y": "UMAP-2", "color": label_key},
                        color_discrete_map=color_map or None,
                        opacity=0.8
                    )
                    for tr in fig.data:
                        tr.name = f"{tr.name}"
                        tr.visible = False
                        tr.marker.update(size=5)
                        tr.meta = dict(uses_local_coords=True, pd_step=step_idx)
                        traces.append(tr)
            else:
                tr = go.Scatter(
                    x=XY[:, 0], y=XY[:, 1],
                    mode="markers",
                    name=f"step {step_idx}",
                    marker=dict(size=5, opacity=0.8),
                    visible=False
                )
                tr.meta = dict(uses_local_coords=True, pd_step=step_idx)
                traces.append(tr)
        return traces, emb_keys
            

    return traces


# ----------------------------
# Main figure builder
# ----------------------------
def detailed_viewer(corespect, labels=None,global_init_embedding=None,mode='three_steps'):
    """
    Build the interactive CoreMAP viewer.

    If `labels` is provided (length == corespect.X.shape[0]),
    use it to label/color ALL overlay traces (Core / Clustered_Core / Propagated)
    while keeping the base cloud unlabeled/gray.
    """
    # ----------------------------
    # Validate & prep override labels (optional)
    # ----------------------------



    n_points = getattr(corespect, "X", None).shape[0]
    labels_override = None
    if labels is not None:
        labels_arr = np.asarray(labels)
        if labels_arr.ndim != 1 or labels_arr.shape[0] != n_points:
            raise ValueError(
                f"`labels` must be a 1D array of length {n_points} (got {labels_arr.shape})."
            )
        # try to use integer labels if possible (play nice with downstream casts)
        try:
            labels_override = labels_arr.astype(int)
        except Exception:
            labels_override = labels_arr  # fallback (will still be cast to str later where used)

    
    # ----------------------------
    # Global UMAP (base only)
    # ----------------------------

    if global_init_embedding is None:
        reducer = umap.UMAP(n_components=2, init='spectral')
        X_umap = reducer.fit_transform(corespect.X)

    else:
        X_umap = global_init_embedding


    # Decide color map: override vs original
    if labels_override is not None:
        global_color_map = _color_map_from_labels(labels_override)
    else:
        global_color_map = build_global_color_map(corespect)

    # ----------------------------
    # Slider names per PD
    # ----------------------------
    slider_names = {}  # {Propagated_Data: [step names]}

    # Base scatter (global cloud) — never relabeled
    base = go.Scatter(
        x=X_umap[:, 0], y=X_umap[:, 1],
        mode="markers", name="All data points",
        marker=dict(color="gray", size=4, opacity=0.3),
        showlegend=True
    )
    fig = go.Figure(data=[base])

    overlay_traces, owners, owner_uses_local = [], [], []
    pd_num_steps = {}  # number of PD steps (from traces_for_object metadata)

    # child -> parent map
    parent = {}
    def register_parent(child, par):
        try:
            parent[child] = par
        except TypeError:
            pass

    # ----------------------------
    # Build all traces
    # ----------------------------
    for co in cores(corespect):
        # Core traces do not use labels for color, safe to call as-is
        trs = traces_for_object(co, global_color_map)
        overlay_traces.extend(trs); owners.extend([co]*len(trs))
        owner_uses_local.extend([getattr(tr, "meta", {}).get("uses_local_coords", False) for tr in trs])

        for cc in clustered_children(co):
            register_parent(cc, co)

            # If overriding labels, temporarily replace cc.core_labels
            if labels_override is not None:
                _old_cc_core_labels = getattr(cc, "core_labels", None)
                setattr(cc, "core_labels", labels_override)

            try:
                trs = traces_for_object(cc, global_color_map)
            finally:
                # Restore original attribute
                if labels_override is not None:
                    if _old_cc_core_labels is None:
                        try: delattr(cc, "core_labels")
                        except Exception: pass
                    else:
                        setattr(cc, "core_labels", _old_cc_core_labels)

            overlay_traces.extend(trs); owners.extend([cc]*len(trs))
            owner_uses_local.extend([getattr(tr, "meta", {}).get("uses_local_coords", False) for tr in trs])

            for pd in propagated_children(cc):
                register_parent(pd, cc)
                start = len(overlay_traces)

                # # If overriding labels, temporarily replace pd.final_labels
                # if labels_override is not None:
                #     _old_pd_final_labels = getattr(pd, "final_labels", None)
                #     setattr(pd, "final_labels", labels_override)

                trs, step_names = traces_for_object(pd, global_color_map, global_init_embedding=X_umap, labels=labels_override,mode=mode)

                #
                # try:
                #     trs, step_names = traces_for_object(pd, global_color_map, global_init_embedding=X_umap)
                # finally:
                #     # Restore original attribute
                #     if labels_override is not None:
                #         if _old_pd_final_labels is None:
                #             try: delattr(pd, "final_labels")
                #             except Exception: pass
                #         else:
                #             setattr(pd, "final_labels", _old_pd_final_labels)

                # names on the slider (we keep existing behavior)
                slider_names[pd] = ["All", "Core", "ClusteredCore"] + step_names

                overlay_traces.extend(trs); owners.extend([pd]*len(trs))
                owner_uses_local.extend([getattr(tr, "meta", {}).get("uses_local_coords", False) for tr in trs])

                # Extract PD step count from meta
                steps = set()
                for k in range(start, len(overlay_traces)):
                    meta = getattr(overlay_traces[k], "meta", {})
                    if owners[k] is pd and "pd_step" in meta:
                        steps.add(meta["pd_step"])
                pd_num_steps[pd] = (1 + max(steps)) if steps else 1

    # ----------------------------
    # Stable legend order
    # ----------------------------
    if overlay_traces:
        triplets = list(zip(overlay_traces, owners, owner_uses_local))
        triplets.sort(key=lambda p: natural_key(p[0].name))
        overlay_traces_sorted, owners, owner_uses_local = zip(*triplets)
        overlay_traces_sorted = list(overlay_traces_sorted)
        owners = list(owners)
        owner_uses_local = list(owner_uses_local)
        fig.add_traces(overlay_traces_sorted)

    # ----------------------------
    # Visibility helpers
    # ----------------------------
    def visible_none():
        # base only
        return [True] + [False]*len(overlay_traces)

    def parent_of(obj):
        return parent.get(obj, None)

    def core_of(pd):
        cc = parent_of(pd)
        if cc is None: return None
        return parent_of(cc)

    def cc_of(pd):
        return parent_of(pd)

    # single-owner mask (hide base if local)
    def vis_mask_for(obj):
        mask = [True] + [False]*len(overlay_traces)
        hide_base = False
        for i, own in enumerate(owners):
            if own is obj:
                mask[1+i] = True
                hide_base = hide_base or owner_uses_local[i]
        if hide_base:
            mask[0] = False
        return mask

    # PD step mask (local → base off)
    def vis_pd_step(pd, step_idx):
        mask = [False] + [False]*len(overlay_traces)
        for i, own in enumerate(owners):
            if own is pd:
                meta = getattr(overlay_traces_sorted[i], "meta", {})
                if meta.get("pd_step") == step_idx:
                    mask[1+i] = True
        return mask

    # Unified slider state (kept for Core/Clustered menus):
    # k = 0 → All points
    # k = 1 → Core (local)
    # k = 2 → Clustered_Core (local)
    # k >= 3 → Propagated_Data step (k-3)
    def vis_slider_state(pd, k):
        if k == 0:
            return visible_none()
        if k == 1:
            co = core_of(pd)
            return vis_mask_for(co) if co is not None else visible_none()
        if k == 2:
            cc = cc_of(pd)
            return vis_mask_for(cc) if cc is not None else visible_none()
        return vis_pd_step(pd, k - 3)

    # PD-only slider state (for Propagated_Data sliders)
    # k = 0 → All points
    # k >= 1 → PD step (k-1)
    def vis_slider_state_pd_only(pd, k):
        if k == 0:
            return visible_none()
        return vis_pd_step(pd, k - 1)

    # ----------------------------
    # Buttons & Sliders
    # ----------------------------
    y_row1, y_row2, y_row3 = 1.29, 1.21, 1.13
    x_buttons = 0.15
    updatemenus = []

    # Row 1: Core selector
    core_list = cores(corespect)
    buttons_row1 = [
        dict(label="Reset", method="update",
             args=[{"visible": visible_none()},
                   {**{f"updatemenus[{i}].visible": (i == 0) for i in range(0, 999)},
                      **{f"sliders[{i}].visible": False for i in range(0, 999)}}])
    ]
    updatemenus.append(dict(
        type="buttons", direction="right",
        x=x_buttons, y=y_row1, xanchor="left", yanchor="top",
        buttons=buttons_row1, pad={"r":8,"t":4}, visible=True
    ))
    row1_index = 0

    # Row 2: per-Core menus (Clustered_Core)
    row2_for_core = {}
    for co in core_list:
        kids = clustered_children(co)
        if kids:
            btns = [dict(label=short(cc), method="relayout", args=[{}]) for cc in kids]
            updatemenus.append(dict(
                type="buttons", direction="right",
                x=x_buttons, y=y_row2, xanchor="left", yanchor="top",
                buttons=btns, visible=False, pad={"r":8,"t":4}
            ))
        else:
            updatemenus.append(dict(
                type="buttons", direction="right",
                x=x_buttons, y=y_row2, xanchor="left", yanchor="top",
                buttons=[dict(label="(no children)", method="relayout", args=[{}])],
                visible=False, pad={"r":8,"t":4}
            ))
        row2_for_core[co] = len(updatemenus) - 1

    # Row 3: per-Clustered_Core menus (Propagated)
    row3_for_cc = {}
    propagated_list = []
    for co in core_list:
        for cc in clustered_children(co):
            pd_kids = propagated_children(cc)
            if pd_kids:
                propagated_list.extend(pd_kids)
                btns = [dict(
                    label=short(pd),
                    method="update",
                    # On click: start at first PD step (index 1; 0 is All)
                    args=[{"visible": vis_slider_state_pd_only(pd, 1)}, {}]
                ) for pd in pd_kids]
                updatemenus.append(dict(
                    type="buttons", direction="right",
                    x=x_buttons, y=y_row3, xanchor="left", yanchor="top",
                    buttons=btns, visible=False, pad={"r":8,"t":4}
                ))
            else:
                updatemenus.append(dict(
                    type="buttons", direction="right",
                    x=x_buttons, y=y_row3, xanchor="left", yanchor="top",
                    buttons=[dict(label="(no children)", method="relayout", args=[{}])],
                    visible=False, pad={"r":8,"t":4}
                ))
            row3_for_cc[cc] = len(updatemenus) - 1

    # Sliders: one per PD → ONLY "All" + PD steps
    sliders = []
    slider_index_for_pd = {}

    def make_slider_for_pd(pd, emb_keys):
        n_pd = pd_num_steps.get(pd, 1)
        total = 1 + n_pd  # All + PD steps
        labels_for_steps = emb_keys  # use provided list (we'll index into it)

        steps = []
        for k in range(total):
            steps.append(dict(
                method="update",
                args=[{"visible": vis_slider_state_pd_only(pd, k)}, {}],
                label=labels_for_steps[k] if k < len(labels_for_steps) else str(k)
            ))

        sld = dict(
            active=0,  # start on "All"
            currentvalue=dict(prefix="", visible=False),
            pad={"t": 6, "b": 0},
            y=-0.1,  # below the plot
            x=0.15,
            len=0.75,
            visible=False,
            steps=steps
        )
        return sld

    for pd in propagated_list:
        slider_index_for_pd[pd] = len(sliders)
        sliders.append(make_slider_for_pd(pd, slider_names[pd]))

    # Wire Row 1 (Core)
    for co in core_list:
        idx_row2 = row2_for_core[co]
        buttons_row1.append(dict(
            label=short(co),
            method="update",
            args=[{"visible": vis_mask_for(co)},
                  {**{f"updatemenus[{i}].visible": False for i in range(1, len(updatemenus))},
                   f"updatemenus[{idx_row2}].visible": True,
                   f"updatemenus[{row1_index}].visible": True,
                   **{f"sliders[{i}].visible": False for i in range(len(sliders))}}]
        ))

    # Wire Row 2 (Clustered_Core)
    for co in core_list:
        idx_row2 = row2_for_core[co]
        kids = clustered_children(co)
        if not kids:
            continue
        for j, cc in enumerate(kids):
            idx_row3 = row3_for_cc[cc]
            updatemenus[idx_row2]["buttons"][j]["method"] = "update"
            updatemenus[idx_row2]["buttons"][j]["args"] = [
                {"visible": vis_mask_for(cc)},
                {**{f"updatemenus[{i}].visible": False for i in range(1, len(updatemenus))},
                 f"updatemenus[{idx_row2}].visible": True,
                 f"updatemenus[{idx_row3}].visible": True,
                 f"updatemenus[{row1_index}].visible": True,
                 **{f"sliders[{i}].visible": False for i in range(len(sliders))}}
            ]

    # Wire Row 3 (Propagated_Data)
    for co in core_list:
        for cc in clustered_children(co):
            idx_row3 = row3_for_cc[cc]
            pd_kids = propagated_children(cc)
            for j, pd in enumerate(pd_kids):
                s_idx = slider_index_for_pd.get(pd, None)
                co_for_pd = core_of(pd)
                idx_row2_core = row2_for_core.get(co_for_pd, None)

                start_idx = 0  # "All"
                updatemenus[idx_row3]["buttons"][j]["args"] = [
                    {"visible": vis_slider_state_pd_only(pd, start_idx)},
                    {
                        **{f"updatemenus[{i}].visible": False for i in range(1, len(updatemenus))},
                        f"updatemenus[{idx_row3}].visible": True,
                        f"updatemenus[{row1_index}].visible": True,
                        **({f"updatemenus[{idx_row2_core}].visible": True} if idx_row2_core is not None else {}),
                        **{f"sliders[{i}].visible": (i == s_idx) for i in range(len(sliders))},
                        **({f"sliders[{s_idx}].active": start_idx} if s_idx is not None else {})
                    }
                ]

    # Row labels
    row_labels = [
        dict(text="Core", x=0.01, y=y_row1 - 0.02,
             xref="paper", yref="paper", showarrow=False,
             align="right", yanchor="top"),
        dict(text="Clustered_Core", x=0.01, y=y_row2 - 0.02,
             xref="paper", yref="paper", showarrow=False,
             align="right", yanchor="top"),
        dict(text="Propagated", x=0.01, y=y_row3 - 0.02,
             xref="paper", yref="paper", showarrow=False,
             align="right", yanchor="top"),
    ]

    # Layout (fixed canvas; legend outside)
    fig.update_layout(
        template="plotly_white",
        updatemenus=updatemenus,
        annotations=row_labels,
        sliders=sliders,
        title=dict(
            text="CoreMAP Visualizer",
            x=0.5, xanchor="center"
        ),
        margin=dict(t=360, r=300, l=110, b=110),
        height=950, width=1100,
        xaxis_title="UMAP-1", yaxis_title="UMAP-2",
        legend=dict(
            orientation="v",
            yanchor="top", y=0.99,
            xanchor="left", x=1.02,
            font=dict(size=12),
            itemsizing="constant",
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="black", borderwidth=1
        )
    )
    fig.update_traces(marker=dict(size=6), selector=dict(mode="markers"))
    return fig


# ----------------------------
# HTML saver
# ----------------------------
def save_coremap_html(fig, path: str):
    fig.write_html(
        path,
        include_plotlyjs="cdn",
        full_html=True,
        config={"responsive": False}
    )
