import pandas as pd

class ProcessComparisonEngine:
    def compare_dicts(self, dict_new, dict_old):
        added_count = 0
        deleted_count = 0
        diff_structure = {}

        all_keys = set(dict_new.keys()).union(set(dict_old.keys()))
        for key in all_keys:
            link = dict_new.get(key) if key in dict_new else dict_old.get(key)
            if key not in dict_new:
                diff_structure[key] = {"link": link, "status": "Deleted"}
                deleted_count += 1
            elif key not in dict_old:
                diff_structure[key] = {"link": link, "status": "Added"}
                added_count += 1
            else:
                diff_structure[key] = {"link": link, "status": "Unchanged"}

        return diff_structure, added_count, deleted_count

    def compare_sub_tables(self, df_new, df_old, key_col, group_col):
        added_count = 0
        deleted_count = 0
        diff_rows = []

        if df_new.empty and df_old.empty:
            return pd.DataFrame(), 0, 0

        new_keys = set(zip(df_new[group_col], df_new[key_col])) if not df_new.empty else set()
        old_keys = set(zip(df_old[group_col], df_old[key_col])) if not df_old.empty else set()

        for group, name in new_keys.union(old_keys):
            row_new = df_new[(df_new[group_col] == group) & (df_new[key_col] == name)] if not df_new.empty else pd.DataFrame()
            row_old = df_old[(df_old[group_col] == group) & (df_old[key_col] == name)] if not df_old.empty else pd.DataFrame()

            link = ""
            if not row_new.empty:
                link = row_new.iloc[0]["RoleLink" if "RoleLink" in df_new.columns else "Dep_Link"]
            elif not row_old.empty:
                link = row_old.iloc[0]["RoleLink" if "RoleLink" in df_old.columns else "Dep_Link"]

            if (group, name) in new_keys and (group, name) not in old_keys:
                diff_rows.append({group_col: group, key_col: name, "Link": link, "Status": "Added"})
                added_count += 1
            elif (group, name) in old_keys and (group, name) not in new_keys:
                diff_rows.append({group_col: group, key_col: name, "Link": link, "Status": "Deleted"})
                deleted_count += 1
            else:
                diff_rows.append({group_col: group, key_col: name, "Link": link, "Status": "Unchanged"})

        return pd.DataFrame(diff_rows), added_count, deleted_count
