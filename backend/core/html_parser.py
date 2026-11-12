import re
from bs4 import BeautifulSoup
import pandas as pd

class CompassHtmlParser:
    def __init__(self):
        self.hash_pattern = re.compile(r'\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}[_\s]|\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b')

    def clean_text(self, text):
        if not text:
            return ""
        cleaned = self.hash_pattern.sub("", text)
        return cleaned.strip()

    def parse_table(self, html_content):
        soup = BeautifulSoup(html_content, "lxml")
        table = soup.find("table", class_=lambda x: x and "qms-structure-table" in x)
        if not table:
            table = soup.find("table")
            if not table:
                raise ValueError("Process-flow table (qms-structure-table) could not be found.")

        rows = table.find_all("tr")
        parsed_rows = []

        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells or len(cells) < 9 or cells[0].name == "th":
                continue

            sl_no = self.clean_text(cells[0].get_text())
            activity_title = self.clean_text(cells[2].get_text())
            successor = self.clean_text(cells[3].get_text())

            # Inputs (Col 4)
            inputs_dict = {}
            for link in cells[4].find_all("a"):
                inputs_dict[self.clean_text(link.get_text())] = link.get("href", "")
            for li in cells[4].find_all("li"):
                txt = self.clean_text(li.get_text())
                if txt not in inputs_dict:
                    inputs_dict[txt] = "IOwithoutLink"

            # Outputs (Col 6)
            outputs_dict = {}
            for link in cells[6].find_all("a"):
                outputs_dict[self.clean_text(link.get_text())] = link.get("href", "")
            for li in cells[6].find_all("li"):
                txt = self.clean_text(li.get_text())
                if txt not in outputs_dict:
                    outputs_dict[txt] = "IOwithoutLink"

            # RASIC (Col 7)
            rasic_data = []
            role_headers = cells[7].find_all("b")
            for header in role_headers:
                role_type = self.clean_text(header.get_text())
                curr = header.next_sibling
                while curr and curr.name != "b":
                    if curr.name == "div" or getattr(curr, "find_all", None):
                        for anchor in curr.find_all("a"):
                            rasic_data.append({
                                "Role": role_type,
                                "RoleName": self.clean_text(anchor.get_text()),
                                "RoleLink": anchor.get("href", "")
                            })
                    curr = curr.next_sibling
            df_rasic = pd.DataFrame(rasic_data, columns=["Role", "RoleName", "RoleLink"])

            # Dependencies (Col 8)
            dep_data = []
            dep_headers = cells[8].find_all("b")
            for header in dep_headers:
                dep_type = self.clean_text(header.get_text()).replace("(", "").replace(")", "").replace(" ", "_")
                curr = header.next_sibling
                while curr and curr.name != "b":
                    if curr.name == "div" or getattr(curr, "find_all", None):
                        for anchor in curr.find_all("a"):
                            dep_data.append({
                                "Dep_Type": dep_type,
                                "Dep_Name": self.clean_text(anchor.get_text()),
                                "Dep_Link": anchor.get("href", "")
                            })
                    curr = curr.next_sibling
            df_dep = pd.DataFrame(dep_data, columns=["Dep_Type", "Dep_Name", "Dep_Link"])

            parsed_rows.append({
                "Nr": sl_no,
                "Title": activity_title,
                "Next": successor,
                "InputDic": inputs_dict,
                "OutputDic": outputs_dict,
                "RASIC": df_rasic,
                "Dependencies": df_dep
            })

        return pd.DataFrame(parsed_rows)
