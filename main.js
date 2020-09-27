console.log(cb_obj.value, "got selected");
console.log(df_dict[cb_obj.value]);
source.data["dates"] = df_dict["dates"];
console.log(source.data["dates"]);
source.data["selected"] = df_dict[cb_obj.value];
source.change.emit();

