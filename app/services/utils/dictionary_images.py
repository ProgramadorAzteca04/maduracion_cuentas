# export_image_dict_rootrel.py
from pathlib import Path
import json, re, unicodedata
from typing import Dict, Iterable

def _slugify(name: str) -> str:
    stem = Path(name).stem
    s = unicodedata.normalize("NFKD", stem)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^0-9a-zA-Z]+", "_", s).strip("_").lower() or "img"

def _has_any_marker(base: Path, files: Iterable[str], globs: Iterable[str], dirs: Iterable[str]) -> bool:
    for f in files:
        if (base / f).exists(): return True
    for g in globs:
        if any(base.glob(g)): return True
    for d in dirs:
        p = base / d
        if p.exists() and p.is_dir(): return True
    return False

def find_project_root(start: Path | None = None) -> Path:
    FILES = (".git", "pyproject.toml", "requirements.txt", "Pipfile",
             "poetry.lock", "setup.cfg", "package.json", "manage.py", ".env")
    GLOBS = ("README", "README.*", "readme", "readme.*", ".env.*")
    DIRS  = (".git", "venv", ".venv", "app", "src")
    here = (start or Path(__file__)).resolve()
    cur = here if here.is_dir() else here.parent
    for parent in [cur, *cur.parents]:
        if _has_any_marker(parent, FILES, GLOBS, DIRS):
            return parent
    return Path.cwd().resolve()

def build_image_map_rootrel(
    source_images_dir: str | Path,
    include_subdirs_in_key: bool = False,
    strict_outside: bool = True,
    project_root: Path | None = None,
) -> Dict[str, str]:
    """
    Devuelve {clave: 'ruta/dentro/del/proyecto.png'} en formato POSIX **sin barra inicial**.
    """
    project_root = (project_root or find_project_root()).resolve()
    src = (project_root / source_images_dir) if not Path(source_images_dir).is_absolute() else Path(source_images_dir)
    src = src.resolve()
    if not src.exists():
        raise FileNotFoundError(f"No existe la carpeta: {src}")

    files = sorted(src.glob("**/*.png"))
    out: Dict[str, str] = {}
    counts: Dict[str, int] = {}

    for p in files:
        if p.suffix.lower() != ".png":
            continue

        # clave
        if include_subdirs_in_key:
            parts = [_slugify(part) for part in p.relative_to(src).with_suffix("").parts]
            base = ".".join(parts)
        else:
            base = _slugify(p.stem)
        counts[base] = counts.get(base, 0) + 1
        key = base if counts[base] == 1 else f"{base}_{counts[base]}"

        # ruta POSIX relativa a la raíz del proyecto, SIN barra inicial (ej. "app/img/...").
        try:
            rel_to_root = p.resolve().relative_to(project_root)  # Path relativo
        except ValueError:
            if strict_outside:
                raise ValueError(f"La imagen está fuera del proyecto: {p}")
            rel_to_root = p.resolve()  # absoluto del SO (se guardará absoluto)
        value = rel_to_root.as_posix()

        out[key] = value
    return out

def export_image_dict_rootrel(
    source_images_dir: str | Path,
    export_rel_dir: str | Path = "app/images",
    filename_json: str = "images.json",
    also_python_module: bool = False,
    python_module_name: str = "images_catalog.py",
    include_subdirs_in_key: bool = False,
    strict_outside: bool = True,
    project_root: Path | None = None,
) -> Path:
    project_root = (project_root or find_project_root()).resolve()
    mapping = build_image_map_rootrel(
        source_images_dir, include_subdirs_in_key, strict_outside, project_root
    )
    export_dir = (project_root / export_rel_dir).resolve()
    export_dir.mkdir(parents=True, exist_ok=True)

    json_path = export_dir / filename_json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    if also_python_module:
        py_path = export_dir / python_module_name
        with open(py_path, "w", encoding="utf-8") as f:
            f.write("# Auto-generado. Rutas relativas a la raíz (sin barra inicial).\nIMAGE_MAP = ")
            json.dump(mapping, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"✅ Módulo: {py_path}")

    print(f"✅ Raíz detectada: {project_root}")
    print(f"✅ Exportado: {json_path} (total: {len(mapping)})")
    return json_path

# Resolver en tiempo de ejecución (soporta con o sin barra por seguridad)
def resolve_in_project(root_rel_path: str, project_root: Path | None = None) -> Path:
    pr = (project_root or find_project_root()).resolve()
    return (pr / root_rel_path.lstrip("/\\")).resolve()

if __name__ == "__main__":
    export_image_dict_rootrel(
        source_images_dir="app/img",      # tu carpeta con PNGs dentro del proyecto
        export_rel_dir="app/images",         # dónde escribir el JSON/Módulo
        filename_json="images.json",
        also_python_module=True,
        include_subdirs_in_key=False,        # True -> claves tipo "buttons.submit_enabled"
        strict_outside=True,                 # error si algo está fuera del proyecto
        project_root=None,                   # autodetectar
    )
