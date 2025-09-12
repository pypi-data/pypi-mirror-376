import uuid


def responsive_pair(desktop_html: str, mobile_html: str, md_min_px: int = 768) -> str:
    """Return both DOM trees with CSS that shows exactly one, scoped to a unique wrapper."""
    uid = uuid.uuid4().hex[:8]
    cls = f"resp-pair-{uid}"
    css = f"""
<style>
.{cls} ._desktop {{ display: none; }}
.{cls} ._mobile  {{ display: block; }}
@media (min-width:{md_min_px}px) {{
  .{cls} ._desktop {{ display: block; }}
  .{cls} ._mobile  {{ display: none;  }}
}}
</style>
"""
    return (
        css
        + f'<div class="{cls}">'
        + f'  <div class="_mobile">{mobile_html}</div>'
        + f'  <div class="_desktop">{desktop_html}</div>'
        + f'</div>'
    )
