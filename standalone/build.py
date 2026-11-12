"""Build the single-file offline app: inline the vendored libraries into app.html."""

from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "EK_kalkulyator.html"


def lib(name: str) -> str:
    return (HERE / "vendor" / name).read_text(encoding="utf-8").replace("</script", "<\\/script")


html = (HERE / "app.html").read_text(encoding="utf-8")
html = html.replace("/*__PLOTLY__*/", lib("plotly-basic.min.js")).replace("/*__XLSX__*/", lib("xlsx.mini.min.js"))
OUT.write_text(html, encoding="utf-8")
print(f"{OUT.name}: {OUT.stat().st_size / 1e6:.2f} MB")
