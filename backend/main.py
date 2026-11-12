import os
import re
import tempfile
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

# Load backend/.env into the environment before the core modules read it
load_dotenv()

from core.confluence_client import ConfluenceClient
from core.html_parser import CompassHtmlParser
from core.comparison_engine import ProcessComparisonEngine
from reports.excel_generator import ExcelReportGenerator

app = FastAPI(title="DeltaProView API", version="1.0.0")

# Dev origins for the Vite frontend. Add more via CORS_ORIGINS in .env (comma-separated).
_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

_BASE_DIR = os.path.dirname(__file__)


def _resolve_config_path():
    """
    Pick the config file, in this order:
      1. CONFIG_FILE from .env (name or absolute path)
      2. Any Compass_Config*.xml in backend/ (ignores bkp_* backups, newest file wins)
      3. page_tree_config.xml (small sample, last resort)
    """
    env_name = os.getenv("CONFIG_FILE", "").strip()
    if env_name:
        path = env_name if os.path.isabs(env_name) else os.path.join(_BASE_DIR, env_name)
        if os.path.exists(path):
            return path

    found = [
        os.path.join(_BASE_DIR, f)
        for f in os.listdir(_BASE_DIR)
        if f.lower().startswith("compass_config") and f.lower().endswith(".xml")
    ]
    if found:
        return max(found, key=os.path.getmtime)

    return os.path.join(_BASE_DIR, "page_tree_config.xml")


CONFIG_PATH = _resolve_config_path()
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class CompareRequest(BaseModel):
    page_id: str
    rev1_id: str  # newer revision
    rev2_id: str  # older revision
    method_name: str
    versions_text: str


# ----------------------------------------------------------------------
# Config helpers
# ----------------------------------------------------------------------

def _text(node, tag, default=""):
    child = node.find(tag)
    return (child.text or "").strip() if child is not None and child.text else default


def _parse_page(page):
    """Convert one <Confluence_Page> element into a method dict."""
    revisions = []
    for rev in page.findall("./Page_Revisions/Page_Revision"):
        revisions.append({
            "version": _text(rev, "Revision"),
            "id": _text(rev, "Rev_Page_Id"),
        })
    return {
        "name": _text(page, "Page_Name"),
        "pub_id": _text(page, "Pub_Page_Id"),
        "revisions": revisions,
    }


# Page names look like:
#   "MP-205.11-PS Requirements Elicitation_11.0"   "MP-205.31-(PS) HW Requirements Engineering_6.0"
#   "PA-205-PS Process Area Content_2.0"            "PAS-205-PS Develop Products_3.0"
#   group   -> "PS"      (level 1: process landscape)
#   process -> "MP-205" / "PA-205" / "PAS-205"  (level 2)
#   method  -> full page name (level 3, carries the revisions)
_NAME_RE = re.compile(r"^([A-Za-z]+-\d+)(?:\.\d+)?-\(?([A-Za-z]+)\)?")


def _build_tree(methods):
    """The XML is flat, so build landscape -> process -> method from the page names."""
    landscapes = {}
    for m in methods:
        match = _NAME_RE.match(m["name"])
        process = match.group(1) if match else "Other"
        landscape = match.group(2) if match else "Other"

        l1 = landscapes.setdefault(
            landscape, {"name": landscape, "pub_id": f"L1-{landscape}", "children": {}}
        )
        l2 = l1["children"].setdefault(
            process, {"name": process, "pub_id": f"L2-{landscape}-{process}", "children": []}
        )
        l2["children"].append(m)

    tree = []
    for l1 in sorted(landscapes.values(), key=lambda x: x["name"]):
        l1["children"] = sorted(l1["children"].values(), key=lambda x: x["name"])
        tree.append(l1)
    return tree


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


def _load_methods():
    if not os.path.exists(CONFIG_PATH):
        raise HTTPException(
            status_code=500,
            detail=f"Config file not found: {CONFIG_PATH}. Place Compass_Config_Template_V01.xml in the backend folder.",
        )
    try:
        root = ET.parse(CONFIG_PATH).getroot()
    except ET.ParseError as e:
        raise HTTPException(status_code=500, detail=f"Invalid XML in {os.path.basename(CONFIG_PATH)}: {e}")

    methods = [_parse_page(p) for p in root.iter("Confluence_Page")]
    return [m for m in methods if m["name"] and m["pub_id"]]


@app.get("/api/config")
def get_config():
    """Returns [ {name, pub_id, children: [ {name, pub_id, children: [ {name, pub_id, revisions} ]} ]} ]"""
    return _build_tree(_load_methods())


@app.get("/api/config/debug")
def config_debug():
    """Shows which file is loaded and how it was grouped (open in the browser to troubleshoot)."""
    methods = _load_methods()
    tree = _build_tree(methods)
    return {
        "config_file": CONFIG_PATH,
        "methods_found": len(methods),
        "landscapes": [
            {
                "name": l1["name"],
                "processes": [
                    {"name": l2["name"], "methods": [m["name"] for m in l2["children"]]}
                    for l2 in l1["children"]
                ],
            }
            for l1 in tree
        ],
        "ungrouped_names": [m["name"] for m in methods if not _NAME_RE.match(m["name"])],
    }


@app.post("/api/compare")
def compare_revisions(req: CompareRequest):
    fd, output_file = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)

    client = ConfluenceClient()
    parser = CompassHtmlParser()
    engine = ProcessComparisonEngine()
    generator = ExcelReportGenerator()

    try:
        # 1. Fetch page HTML
        html_new = client.fetch_page_html(req.rev1_id)
        html_old = client.fetch_page_html(req.rev2_id)

        # 2. Parse to DataFrames
        df_new = parser.parse_table(html_new)
        df_old = parser.parse_table(html_old)

        if df_new.empty or df_old.empty:
            raise ValueError("No activity rows were found in one of the selected revisions.")

        # 3. Outer join on Title (keeps original order: new revision first, then removed ones)
        comparisons = []
        summary_stats = {
            "inputs_added": 0, "inputs_deleted": 0,
            "outputs_added": 0, "outputs_deleted": 0,
            "rasic_added": 0, "rasic_deleted": 0,
            "dep_added": 0, "dep_deleted": 0,
        }

        all_titles = list(dict.fromkeys(df_new["Title"].tolist() + df_old["Title"].tolist()))
        for title in all_titles:
            row_new = df_new[df_new["Title"] == title]
            row_old = df_old[df_old["Title"] == title]

            if row_old.empty:
                row = row_new.iloc[0]
                comparisons.append({
                    "Nr": row["Nr"], "Title": title, "Next": row["Next"],
                    "Inputs_Diff": {k: {"link": v, "status": "Added"} for k, v in row["InputDic"].items()},
                    "Outputs_Diff": {k: {"link": v, "status": "Added"} for k, v in row["OutputDic"].items()},
                    "RASIC_Diff": [{"Role": r["Role"], "RoleName": r["RoleName"], "Status": "Added"} for _, r in row["RASIC"].iterrows()],
                    "Dependencies_Diff": [{"Dep_Type": d["Dep_Type"], "Dep_Name": d["Dep_Name"], "Status": "Added"} for _, d in row["Dependencies"].iterrows()],
                    "Status": "Added",
                })
            elif row_new.empty:
                row = row_old.iloc[0]
                comparisons.append({
                    "Nr": row["Nr"], "Title": title, "Next": row["Next"],
                    "Inputs_Diff": {k: {"link": v, "status": "Deleted"} for k, v in row["InputDic"].items()},
                    "Outputs_Diff": {k: {"link": v, "status": "Deleted"} for k, v in row["OutputDic"].items()},
                    "RASIC_Diff": [{"Role": r["Role"], "RoleName": r["RoleName"], "Status": "Deleted"} for _, r in row["RASIC"].iterrows()],
                    "Dependencies_Diff": [{"Dep_Type": d["Dep_Type"], "Dep_Name": d["Dep_Name"], "Status": "Deleted"} for _, d in row["Dependencies"].iterrows()],
                    "Status": "Deleted",
                })
            else:
                r_new = row_new.iloc[0]
                r_old = row_old.iloc[0]

                inp_diff, i_add, i_del = engine.compare_dicts(r_new["InputDic"], r_old["InputDic"])
                out_diff, o_add, o_del = engine.compare_dicts(r_new["OutputDic"], r_old["OutputDic"])
                ras_diff, r_add, r_del = engine.compare_sub_tables(r_new["RASIC"], r_old["RASIC"], "RoleName", "Role")
                dep_diff, d_add, d_del = engine.compare_sub_tables(r_new["Dependencies"], r_old["Dependencies"], "Dep_Name", "Dep_Type")

                summary_stats["inputs_added"] += i_add
                summary_stats["inputs_deleted"] += i_del
                summary_stats["outputs_added"] += o_add
                summary_stats["outputs_deleted"] += o_del
                summary_stats["rasic_added"] += r_add
                summary_stats["rasic_deleted"] += r_del
                summary_stats["dep_added"] += d_add
                summary_stats["dep_deleted"] += d_del

                comparisons.append({
                    "Nr": r_new["Nr"], "Title": title, "Next": r_new["Next"],
                    "Inputs_Diff": inp_diff,
                    "Outputs_Diff": out_diff,
                    "RASIC_Diff": ras_diff.to_dict("records") if not ras_diff.empty else [],
                    "Dependencies_Diff": dep_diff.to_dict("records") if not dep_diff.empty else [],
                    "Status": "Unchanged",
                })

        # 4. Build the Excel report in a unique temp file
        generator.build_report(comparisons, summary_stats, req.method_name, req.versions_text, output_file)

        # The temp file is deleted after the response has been sent
        return FileResponse(
            output_file,
            media_type=XLSX_MIME,
            filename="CompReport.xlsx",
            background=BackgroundTask(os.remove, output_file),
        )
    except Exception as e:
        if os.path.exists(output_file):
            os.remove(output_file)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print(f"[DeltaProView] Using config file: {CONFIG_PATH}")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)