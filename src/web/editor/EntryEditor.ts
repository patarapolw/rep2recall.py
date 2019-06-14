import { Vue, Component, Prop, Emit } from "vue-property-decorator";
import h from "hyperscript";
import { Columns, IColumn } from "../shared";
import DatetimeNullable from "./DatetimeNullable";
import { fetchJSON, normalizeArray, dotGetter, dotSetter, fixData, IKv } from "../util";
import TagEditor from "./TagEditor";
import swal from "sweetalert";
import SimpleMde from "./SimpleMde";

@Component({
    components: {DatetimeNullable, TagEditor, SimpleMde},
    template: h("b-modal", {attrs: {
        ":id": "id",
        ":title": "title",
        "size": "lg",
        "v-on:show": "onModalShown",
        "v-on:ok": "onModalOk"
    }}, [
        h("img.page-loader", {attrs: {
            "src": "Spinner-1s-200px.svg",
            "v-if": "isLoading"
        }}),
        h("form.col-12.needs-validation", {attrs: {
            "ref": "form"
        }}, [
            h(".col-12.mb-3", {attrs: {
                "v-for": "c in activeCols",
                ":key": "c ? c.name : 'separator'"
            }}, [
                h(".row", {attrs: {
                    "v-if": "c"
                }}, [
                    h("label.col-form-label.mb-1", {attrs: {
                        ":class": "{'col-sm-2': c.type !== 'html'}"
                    }}, "{{c.label}}"),
                    h("simple-mde", {attrs: {
                        "v-if": "c.type === 'html'",
                        ":value": "update[c.name] || getParsedData(c.name) || ''",
                        "v-on:input": "$set(update, c.name, $event)",
                        ":required": "c.required",
                        ":invalid-feedback": "c.label + 'is required.'",
                        ":data": "data"
                    }}),
                    h("datetime-nullable.col-sm-10", {attrs: {
                        "v-else-if": "c.type === 'datetime'",
                        ":value": "update[c.name] || data[c.name]",
                        "v-on:input": "$set(update, c.name, $event)",
                        ":required": "c.required"
                    }}),
                    h("tag-editor.col-sm-10", {attrs: {
                        "v-else-if": "c.type === 'tag'",
                        ":value": "(update[c.name] || data[c.name]) ? (update[c.name] || data[c.name]).join(' ') : ''",
                        "v-on:input": "$set(update, c.name, $event.split(' '))"
                    }}),
                    h("textarea.form-control.col-sm-10", {attrs: {
                        "v-else-if": "c.type === 'multiline'",
                        ":value": "dotGetter(update, c.name) || dotGetter(data, c.name)",
                        "v-on:input": "dotSetter(update, c.name, $event.target.value)"
                    }}),
                    h("input.form-control.col-sm-10", {attrs: {
                        "v-else": "",
                        ":value": "update[c.name] || data[c.name]",
                        "v-on:input": "$set(update, c.name, $event.target.value)",
                        ":required": "c.required"
                    }}),
                    h(".invalid-feedback", "{{c.label}} is required.")
                ]),
                h("h4.mb-3", {attrs: {
                    "v-else": ""
                }}, "Template data")
            ]),
            h(".col-12.mb-3", {attrs: {
                "v-if": "activeCols.indexOf(null) !== -1"
            }}, [
                h(".row", [
                    h("input.form-control.col-sm-4.no-border", {attrs: {
                        "v-on:keypress": "onExtraRowInput",
                        "placeholder": "Type here to add more keys."
                    }}),
                ])
            ])
        ])
    ]).outerHTML
})
export default class EntryEditor extends Vue {
    @Prop() id!: string;
    @Prop() entryId?: number;
    @Prop() title!: string;
    
    private data: any = {};
    private update: any = {};
    private isLoading = false;

    private dotGetter = dotGetter;
    private dotSetter = dotSetter;

    get activeCols() {
        const cols = Columns.filter((c) => !this.entryId ? c.newEntry !== false : true) as Array<IColumn | null>;

        if (this.entryId) {
            const extraCols: string[] = (this.data.data || []).map((d: IKv) => d.key);

            if (extraCols.length > 0) {
                cols.push(...[
                    null,
                    {
                        name: "source",
                        label: "Source"
                    },
                    {
                        name: "template",
                        label: "Template"
                    }
                ]);
            }

            extraCols.forEach((c) => {
                cols.push({
                    name: `@${c}`,
                    label: c[0].toLocaleUpperCase() + c.substr(1),
                    type: "multiline"
                });
            });
        }

        return cols;
    }

    private getParsedData(key: string) {
        let v: string = this.data[key] || "";

        if (v.startsWith("@rendered\n")) {
            v = "@template\n" + (this.data[`t${key[0].toLocaleUpperCase() + key.substr(1)}`] || "");
        }

        return v;
    }

    private onExtraRowInput(evt: any) {
        const k = evt.target.value;

        if (evt.key === "Enter" && k) {
            let toAdd = true;
            for (const it of this.data.data) {
                if (it.key === k) {
                    toAdd = false;
                }
            }
            if (toAdd) {
                this.data.data.push({
                    key: k,
                    value: ""
                });
            }

            evt.target.value = "";
        }
    }
    
    private async onModalShown() {
        this.data = {};
        this.update = {};
        this.$nextTick(() => {
            normalizeArray(this.$refs.form).classList.remove("was-validated");
        });

        if (this.entryId) {
            this.isLoading = true;

            const data = await fetchJSON("/api/editor/", {cond: {id: this.entryId}});
            Vue.set(this, "data", fixData(data.data[0]));
        }
        
        this.isLoading = false;
    }

    @Emit("ok")
    private async onModalOk(evt: any) {
        for (const c of Columns) {
            if (c.required) {
                if (this.update[c.name] === undefined && !this.data[c.name]) {
                    normalizeArray(this.$refs.form).classList.add("was-validated");
                    evt.preventDefault();
                    return {};
                }
            }
        }

        if (Object.keys(this.update).length > 0) {
            if (this.entryId) {
                const r = await fetchJSON("/api/editor/", {id: this.entryId, update: this.update}, "PUT");
                if (!r.error) {
                    await swal({
                        text: "Updated",
                        icon: "success"
                    });
                }
            } else {
                const r = await fetchJSON("/api/editor/", {create: this.update}, "PUT");
                if (!r.error) {
                    await swal({
                        text: "Created",
                        icon: "success"
                    });
                }
            }
        }

        return this.update;
    }
}
