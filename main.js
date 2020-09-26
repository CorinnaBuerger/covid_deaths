console.log(cb_obj.value, "got selected");
console.log(df_dict[cb_obj.value]);
graph.data.x = df_dict["dates"];
graph.data.y = df_dict[cb_obj.value];
graph.change.emit();

