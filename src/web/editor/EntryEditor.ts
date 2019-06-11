import { Vue, Component, Prop, Emit } from "vue-property-decorator";
import h from "hyperscript";
import { Columns } from "../shared";
import DatetimeNullable from "./DatetimeNullable";
import { fetchJSON, normalizeArray, html2md } from "../util";
import TagEditor from "./TagEditor";
import swal from "sweetalert";

@Component({
    components: {DatetimeNullable, TagEditor},
    template: h("b-modal", {attrs: {
        ":id": "id",
        ":title": "title",
        ":size": "size",
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
                ":key": "c.name"
            }}, [
                h(".row", [
                    h("label.col-form-label.mb-1", {attrs: {
                        ":class": "{'col-sm-2': (['string', 'number', 'tag', 'datetime'].indexOf(c.type) !== -1)}"
                    }}, "{{c.label}}"),
                    h(".w-100", {attrs: {
                        "v-if": "c.type === 'html'",
                    }}, [
                        h(".w-100", {attrs: {
                            ":class": "c.required ? 'form-required' : 'form-not-required'"
                        }}, [
                            h("markdown-editor", {attrs: {
                                ":ref": "c.name",
                                ":configs": "{spellChecker: false, status: false}",
                                ":value": "update[c.name] || data[c.name]",
                                "v-on:input": "$set(update, c.name, $event)"
                            }})
                        ]),
                        h("input.form-control.flatten", {attrs: {
                            ":required": "c.required",
                            ":value": "update[c.name] || data[c.name]"
                        }}),
                        h(".invalid-feedback", "{{c.label}} is required.")
                    ]),
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
                    h("input.form-control.col-sm-10", {attrs: {
                        "v-else": "",
                        ":value": "update[c.name] || data[c.name]",
                        "v-on:input": "$set(update, c.name, $event.target.value)",
                        ":required": "c.required"
                    }}),
                    h(".invalid-feedback", "{{c.label}} is required.")
                ])
            ]),
            h(".col-12", {attrs: {
                "v-if": "data.data"
            }}, [
                h("h4.mb-3", "Template data"),
                h(".row.mb-3", {attrs: {
                    "v-for": "c in hasSourceExtraCols",
                    ":key": "c"
                }}, [
                    h("label.col-form-label.col-sm-2", "{{ c[0].toLocaleUpperCase() + c.substr(1) }}"),
                    h("input.form-control.col-sm-10", {attrs: {
                        ":value": "data[c]",
                        "readonly": ""
                    }})
                ]),
                h(".row.mb-3", {attrs: {
                    "v-for": "key in Object.keys(data.data)",
                    ":key": "key"
                }}, [
                    h("label.col-form-label.mb-1.col-sm-2", "{{ key }}"),
                    h("textarea.form-control.col-sm-10", {attrs: {
                        ":value": "data.data[key]",
                        "readonly": ""
                    }})
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

    private readonly size = "lg";
    private readonly cols = Columns;
    private readonly hasSourceExtraCols = [
        "source",
        // "model",
        "template"
    ]

    get activeCols() {
        return this.cols.filter((c) => !this.entryId ? c.newEntry !== false : true);
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
            Vue.set(this, "data", data.data[0])
            this.cols.forEach((c) => {
                if (c.type === "html") {
                    const mde = normalizeArray(this.$refs[c.name]).simplemde;
                    mde.value(html2md(this.data[c.name] || ""));
                }
            });
        }
        
        this.isLoading = false;
    }

    @Emit("ok")
    private async onModalOk(evt: any) {
        for (const c of this.cols) {
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
                console.log(this.entryId);
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
