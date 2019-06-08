import { Vue, Component, Prop } from "vue-property-decorator";
import h from "hyperscript";
import { Columns, IColumn } from "../shared";
import DatetimeNullable from "./DatetimeNullable";
import { makeCamelSpaced, fetchJSON, normalizeArray, html2md } from "../util";

@Component({
    components: {DatetimeNullable},
    template: h("b-modal", {attrs: {
        ":id": "id",
        ":title": "title",
        ":size": "size",
        "v-on:show": "onModalShown",
        "v-on:ok": "onModalOk"
    }}, [
        h("form.col-12.needs-validation", {attrs: {
            "ref": "form"
        }}, [
            h(".col-12.mb-3", {attrs: {
                "v-for": "c in activeCols",
                ":key": "c.name"
            }}, [
                h(".row", [
                    h("label.col-form-label.mb-1", {attrs: {
                        ":class": "{'col-sm-2': (['string', 'number', 'list', 'datetime'].indexOf(c.type) !== -1)}"
                    }}, "{{ c.label || makeCamelSpaced(c.name) }}"),
                    h(".w-100", {attrs: {
                        "v-if": "c.type === 'html'",
                    }}, [
                        h(".w-100", {attrs: {
                            ":class": "c.required ? 'form-required' : 'form-not-required'"
                        }}, [
                            h("markdown-editor", {attrs: {
                                ":ref": "c.name",
                                ":configs": "{spellChecker: false, status: false}",
                                "v-model": "data[c.name]"
                            }})
                        ]),
                        h("input.form-control.flatten", {attrs: {
                            "v-model": "data[c.name]",
                            ":required": "c.required"
                        }}),
                        h(".invalid-feedback", "{{ c.label || makeCamelSpaced(c.name) }} is required.")
                    ]),
                    h("datetime-nullable.col-sm-10", {attrs: {
                        "v-else-if": "c.type === 'datetime'",
                        "v-model": "data[c.name]",
                        ":required": "c.required"
                    }}),
                    h("input.form-control.col-sm-10", {attrs: {
                        "v-else": "",
                        ":placeholder": "c.type === 'list' ? 'Please input tags separated by spaces' : ''",
                        ":value": "c.type === 'list' ? (data[c.name] || []).join(' ') : data[c.name]",
                        "v-on:input": "onInputChanged($event, c)",
                        ":required": "c.required"
                    }}),
                    h(".invalid-feedback", "{{ c.label || makeCamelSpaced(c.name) }} is required.")
                ])
            ]),
            h("h4.mb-3", "Template data"),
            h(".col-12", {attrs: {
                "v-if": "data.data"
            }}, [
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

    private readonly size = "lg";
    private readonly cols = Columns;
    private readonly makeCamelSpaced = makeCamelSpaced

    get activeCols() {
        return this.cols.filter((c) => !this.entryId ? c.newEntry !== false : true);
    }
    
    private onModalShown() {
        this.data = {};
        this.$nextTick(() => {
            normalizeArray(this.$refs.form).classList.remove("was-validated");
        });

        if (this.entryId) {
            fetchJSON("/api/editor/", {q: {id: this.entryId}}).then((data) => {
                Vue.set(this, "data", data.data[0])
                this.cols.forEach((c) => {
                    if (c.type === "html") {
                        const mde = normalizeArray(this.$refs[c.name]).simplemde;
                        mde.value(html2md(this.data[c.name] || ""));
                    }
                })
            });
        }
    }

    private onModalOk(evt: any) {
        for (const c of this.cols) {
            if (c.required) {
                if (!this.data[c.name]) {
                    normalizeArray(this.$refs.form).classList.add("was-validated");
                    evt.preventDefault();
                    return;
                }
            }
        }
    }

    private onInputChanged(evt: any, col: IColumn) {
        if (col.type === "list") {
            const tags: string[] = evt.target.value.split(" ")
            Vue.set(this.data, col.name, tags.filter((t, i) => tags.indexOf(t) === i).sort());
        } else {
            Vue.set(this.data, col.name, evt.target.value);
        }
    }
}
