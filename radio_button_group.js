console.log(this.value, "got selected");
if (cb_obj.value == "Daily") {
    source.data["dates"] = df_dict_d["dates"];
    source.data["selected"] = df_dict_d["selected"];
    source.data["World"] = df_dict_d["World"];
} else if (cb_obj.value == "Total") {
    source.data["dates"] = df_dict_t["dates"];
    source.data["selected"] = df_dict_t["selected"];
    source.data["World"] = df_dict_t["World"];
}
source.change.emit();
