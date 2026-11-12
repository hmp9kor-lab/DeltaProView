import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.comments import Comment

class ExcelReportGenerator:
    def __init__(self):
        self.color_added = "C6E0B4"     # Light Green (ClosedXML: 0xC6E0B4)
        self.color_deleted = "F8CBAD"   # Light Orange (ClosedXML: 0xF8CBAD)
        self.color_header = "8DB4E2"    # Steel Blue (ClosedXML: 0x8DB4E2)
        self.color_activity = "92CDDC"  # Soft Turquoise (ClosedXML: 0x92CDDC)
        self.color_hyperlink = "0563C1" # Classic blue hyperlink

    def build_report(self, comparisons, summary_stats, method_name, versions_text, output_path):
        wb = openpyxl.Workbook()
        
        # 1. Sheet 1: Info-Summary
        ws_info = wb.active
        ws_info.title = "Info-Summary"
        ws_info.views.sheetView[0].showGridLines = True
        
        font_bold = Font(name="Segoe UI", size=11, bold=True)
        fill_header = PatternFill(start_color=self.color_header, fill_type="solid")
        
        ws_info["A1"] = "Method Comparison Remarks"
        ws_info["A1"].font = font_bold
        ws_info["A1"].fill = fill_header
        
        ws_info["A2"] = "Method Name"
        ws_info["A2"].font = font_bold
        ws_info["B2"] = method_name
        
        ws_info["A3"] = "Versions Compared"
        ws_info["A3"].font = font_bold
        ws_info["B3"] = versions_text
        
        ws_info["A4"] = "Color Coding"
        ws_info["A4"].font = font_bold
        ws_info["B4"] = "Modified/New"
        ws_info["B4"].fill = PatternFill(start_color=self.color_added, fill_type="solid")
        ws_info["B5"] = "Deleted"
        ws_info["B5"].fill = PatternFill(start_color=self.color_deleted, fill_type="solid")

        # Stats Dashboard matching .NET summary
        ws_info["A8"] = "Comparison Summary :"
        ws_info["A8"].font = font_bold
        ws_info["A8"].fill = fill_header
        
        stats_rows = [
            ("Inputs Added", summary_stats.get("inputs_added", 0)),
            ("Inputs Deleted", summary_stats.get("inputs_deleted", 0)),
            ("Outputs Added", summary_stats.get("outputs_added", 0)),
            ("Outputs Deleted", summary_stats.get("outputs_deleted", 0)),
            ("Rasic Roles Added", summary_stats.get("rasic_added", 0)),
            ("Rasic Roles Deleted", summary_stats.get("rasic_deleted", 0)),
            ("Guidence elements Added", summary_stats.get("dep_added", 0)),
            ("Guidence elements Deleted", summary_stats.get("dep_deleted", 0)),
        ]
        
        row_idx = 9
        for label, val in stats_rows:
            ws_info.cell(row=row_idx, column=2, value=label)
            ws_info.cell(row=row_idx, column=3, value=val)
            row_idx += 1

        # Activity Wise summary title
        ws_info.cell(row=18, column=1, value="Comparison Summary Activity Wise :").font = font_bold
        ws_info.cell(row=18, column=1).fill = fill_header
        ws_info.cell(row=18, column=2, value="Note : Activity wise comparison summary considers only modified activities").font = font_bold

        ws_info.column_dimensions['A'].width = 35
        ws_info.column_dimensions['B'].width = 65
        
        # 2. Sheet 2: CompReport (Detailed Comparison Grid)
        ws_comp = wb.create_sheet(title="CompReport")
        ws_comp.views.sheetView[0].showGridLines = True
        
        headers = ["Sl No", "Activity", "Successor", "Inputs", "Outputs", "RASIC", "Dependencies"]
        for col_idx, h in enumerate(headers, 1):
            cell = ws_comp.cell(row=1, column=col_idx, value=h)
            cell.font = Font(name="Segoe UI", size=12, bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            
        ws_comp.row_dimensions[1].height = 25
        ws_comp.freeze_panes = "C2"
        
        # Populate compared process rows dynamically
        current_row = 2
        for comp in comparisons:
            sl_no = comp.get("Nr", "")
            title = comp.get("Title", "")
            next_act = comp.get("Next", "")
            inputs_diff = comp.get("Inputs_Diff", {})
            outputs_diff = comp.get("Outputs_Diff", {})
            rasic_diff = comp.get("RASIC_Diff", [])
            dep_diff = comp.get("Dependencies_Diff", [])
            status = comp.get("Status", "Unchanged")
            
            # Draw standard flat text values
            ws_comp.cell(row=current_row, column=1, value=sl_no)
            ws_comp.cell(row=current_row, column=2, value=title)
            ws_comp.cell(row=current_row, column=3, value=next_act)
            
            # Apply corporate additions / deletions colors to the main activity row
            if status == "Added":
                ws_comp.cell(row=current_row, column=2).fill = PatternFill(start_color=self.color_added, fill_type="solid")
            elif status == "Deleted":
                ws_comp.cell(row=current_row, column=2).fill = PatternFill(start_color=self.color_deleted, fill_type="solid")
                
            # Populating sub-matrices on different vertical rows
            # Inputs
            sub_row = current_row
            for inp_key, details in inputs_diff.items():
                cell = ws_comp.cell(row=sub_row, column=4, value=inp_key)
                if details["status"] == "Added":
                    cell.fill = PatternFill(start_color=self.color_added, fill_type="solid")
                elif details["status"] == "Deleted":
                    cell.fill = PatternFill(start_color=self.color_deleted, fill_type="solid")
                sub_row += 1
                
            # Outputs
            sub_row = current_row
            for out_key, details in outputs_diff.items():
                cell = ws_comp.cell(row=sub_row, column=5, value=out_key)
                if details["status"] == "Added":
                    cell.fill = PatternFill(start_color=self.color_added, fill_type="solid")
                elif details["status"] == "Deleted":
                    cell.fill = PatternFill(start_color=self.color_deleted, fill_type="solid")
                sub_row += 1
                
            # RASIC Roles
            sub_row = current_row
            for r in rasic_diff:
                ws_comp.cell(row=sub_row, column=6, value=f"{r['Role']}: {r['RoleName']}")
                if r["Status"] == "Added":
                    ws_comp.cell(row=sub_row, column=6).fill = PatternFill(start_color=self.color_added, fill_type="solid")
                elif r["Status"] == "Deleted":
                    ws_comp.cell(row=sub_row, column=6).fill = PatternFill(start_color=self.color_deleted, fill_type="solid")
                sub_row += 1
                
            # Dependencies
            sub_row = current_row
            for d in dep_diff:
                ws_comp.cell(row=sub_row, column=7, value=f"{d['Dep_Type']}: {d['Dep_Name']}")
                if d["Status"] == "Added":
                    ws_comp.cell(row=sub_row, column=7).fill = PatternFill(start_color=self.color_added, fill_type="solid")
                elif d["Status"] == "Deleted":
                    ws_comp.cell(row=sub_row, column=7).fill = PatternFill(start_color=self.color_deleted, fill_type="solid")
                sub_row += 1
                
            # Calculate height of this multi-row group
            max_rows_used = max(1, len(inputs_diff), len(outputs_diff), len(rasic_diff), len(dep_diff))
            current_row += max_rows_used
            
            # Apply separation border line below this activity block
            for c in range(1, 8):
                ws_comp.cell(row=current_row-1, column=c).border = Border(bottom=Side(style='medium', color='000000'))
                
        ws_comp.column_dimensions['A'].width = 8
        ws_comp.column_dimensions['B'].width = 30
        ws_comp.column_dimensions['C'].width = 30
        ws_comp.column_dimensions['D'].width = 35
        ws_comp.column_dimensions['E'].width = 35
        ws_comp.column_dimensions['F'].width = 35
        ws_comp.column_dimensions['G'].width = 35
        
        wb.save(output_path)
        return output_path
