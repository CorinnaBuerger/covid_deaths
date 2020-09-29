console.log(cb_obj.value, "got selected");
// indicator that source is currently set to total
console.log("World:", source.data["World"][1]);
if (source.data["World"][1] > 10) {
    source.data["selected"] = df_dict_t[cb_obj.value];
    source.data["dates"] = df_dict_t["dates"];
} else {
    source.data["selected"] = df_dict_d[cb_obj.value];
    source.data["dates"] = df_dict_d["dates"];
}
source.change.emit();
