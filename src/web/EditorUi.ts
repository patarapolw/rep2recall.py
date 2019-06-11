import { Vue, Component, Watch } from "vue-property-decorator";
import h from "hyperscript";
import { Columns, DateFormat } from "./shared";
import { fetchJSON, quizDataToContent } from "./util";
import DatetimeNullable from "./editor/DatetimeNullable";
import EntryEditor from "./editor/EntryEditor";
import swal from "sweetalert";
import toastr from "toastr";
import flatpickr from "flatpickr";

@Component({
    components: {DatetimeNullable, EntryEditor},
    template: h(".stretched.editor-window", [
        h(".editor-control", [
            h(".editor-nav", [
                h("button.btn", {attrs: {
                    "v-on:click": "offset = 0"
                }}, "<<"),
                h("button.btn", {attrs: {
                    "v-on:click": "offset -= limit"
                }}, "<"),
                h("span", "{{editorLabel}}"),
                h("button.btn", {attrs: {
                    "v-on:click": "offset += limit"
                }}, ">"),
                h("button.btn", {attrs: {
                    "v-on:click": "offset = NaN"
                }}, ">>")
            ]),
            h(".editor-button-space", [
                h("b-button.editor-button", {attrs: {
                    "variant": "outline-success",
                    "v-b-modal.new-entry-modal": ""
                }}, "New card"),
                h("span", {attrs: {
                    "v-if": "checkedIds.size > 0"
                }}, [
                    h("b-button.editor-button", {attrs: {
                        "variant": "outline-primary",
                        "v-b-modal.edit-entry-modal": "",
                        "v-if": "checkedIds.size === 1"
                    }}, "Edit"),
                    h("b-dropdown.mr-3", {attrs: {
                        "split": "",
                        "variant": "outline-secondary",
                        "v-on:click": "changeDeck",
                        "text": "Change Deck"
                    }}, [
                        h("b-dropdown-item", {attrs: {
                            "v-on:click": "editTags(true)",
                            "href": "#"
                        }}, "Add tags"),
                        h("b-dropdown-item", {attrs: {
                            "v-on:click": "editTags(false)",
                            "href": "#"
                        }}, "Remove tags")
                    ]),
                    h("b-button.editor-button", {attrs: {
                        "variant": "outline-danger",
                        "v-on:click": "deleteCards"
                    }}, "Delete"),
                ])
            ]),
            h(".editor-input", [
                h("input.form-control", {
                    placeholder: "Type here to search",
                    attrs: {
                        "v-model": "q",
                        "v-on:keyup": "onSearchbarKeypress",
                        "spellcheck": "false",
                        "autocomplete": "off",
                        "autocorrect": "off",
                        "autocapitalize": "off"
                    }
                })
            ])
        ]),
        h("table.table.table-hover#editorTable", {attrs: {
            ":style": "{width: tableWidth + 'px'}"
        }}, [
            h("colgroup", [
                h("col", {attrs: {
                    ":style": "{width: colWidths.checkbox + 'px'}",
                }}),
                h("col", {attrs: {
                    "v-for": "c in cols",
                    ":style": "{width: c.width + 'px'}",
                    ":key": "c.name"
                }}),
                h("col", {attrs: {
                    "v-if": "hasSource",
                    "v-for": "c in hasSourceExtraCols",
                    ":style": "{width: colWidths.extra + 'px'}",
                    ":key": "c"
                }}),
                h("col", {attrs: {
                    "v-for": "c in extraCols",
                    ":style": "{width: colWidths.extra + 'px'}",
                    ":key": "'data.' + c"
                }}),
                h("col", {attrs: {
                    ":style": "{width: '150px'}"
                }})
            ]),
            h("thead", [
                h("tr", [
                    h("th", [
                        h("div", [
                            h("input", {type: "checkbox", attrs: {
                                "v-on:click": "onCheckboxClicked($event)",
                                "ref": "checkbox.main",
                                ":checked": "checkedIds.size > 0",
                                "v-show": "!allCardsSelected"
                            }}),
                            h("i.fas.fa-check-double", {attrs: {
                                "v-if": "allCardsSelected",
                                "v-on:click": "allCardsSelected = false; checkedIds.clear()"
                            }})
                        ])
                    ]),
                    h("th", {attrs: {
                        "v-for": "c in cols",
                        ":key": "c.name",
                        "scope": "col"
                    }}, [
                        h("a", {attrs: {
                            "href": "#",
                            "v-on:click": "onTableHeaderClicked(c.name)"
                        }}, "{{ c.label }}"),
                        h("span", {attrs: {
                            "v-if": "sortBy === c.name"
                        }}, "{{ desc ? ' ▲' : ' ▼'}}")
                    ]),
                    h("th", {attrs: {
                        "v-if": "hasSource",
                        "v-for": "c in hasSourceExtraCols",
                        ":key": "c",
                        "scope": "col"
                    }}, [
                        h("a", {attrs: {
                            "href": "#",
                            "v-on:click": "onTableHeaderClicked(c)"
                        }}, "{{ c[0].toLocaleUpperCase() + c.substr(1) }}"),
                        h("span", {attrs: {
                            "v-if": "sortBy === c"
                        }}, "{{ desc ? ' ▲' : ' ▼'}}")
                    ]),
                    h("th", {attrs: {
                        "v-for": "c in extraCols",
                        ":key": "'data.' + c",
                        "scope": "col"
                    }}, [
                        h("a", {attrs: {
                            "href": "#",
                            "v-on:click": "onTableHeaderClicked('data.' + c)",
                            ":style": "{display: 'inline-block', width: (colWidths.extra - 50) + 'px'}"
                        }}, "{{c}}"),
                        h("span", {attrs: {
                            "v-if": "sortBy === ('data.' + c)"
                        }}, "{{ desc ? ' ▲' : ' ▼'}}")
                    ]),
                    h("th")
                ])
            ]),
            h("tbody", [
                h("tr.fixed-header-offset"),
                h("tr", {attrs: {
                    "v-for": "d in data",
                    ":key": "d.id",
                    "v-on:click": "onTableRowClicked(d.id)",
                    ":class": "{selected: checkedIds.has(d.id)}"
                }}, [
                    h("td", {style: {width: "50px"}}, [
                        h("div", [
                            h("input", {type: "checkbox", attrs: {
                                "v-on:click.native": "onCheckboxClicked($event, d.id)",
                                ":checked": "checkedIds.has(d.id)"
                            }})
                        ])
                    ]),
                    h("td", {attrs: {
                        "v-for": "a in getOrderedDict(d)",
                        ":key": "a[0]",
                    }}, [
                        h("iframe.html-frame", {attrs: {
                            "v-if": "a[2].type === 'html'",
                            ":srcdoc": "getHtml(d, a[0])",
                            "height": "150",
                            "width": "350",
                            "frameBorder": "0"
                        }}),
                        h(".wrapper", {attrs: {
                            "v-else": "",
                        }}, [
                            h(".wrapped", {attrs: {
                                "v-if": "a[2].type === 'datetime'"
                            }}, "{{ stringifyDate(a[1]) }}"),
                            h(".wrapped", {attrs: {
                                "v-else-if": "a[2].type === 'tag'"
                            }}, [
                                h("p", {attrs: {
                                    "v-for": "b in a[1]",
                                    ":key": "b",
                                    "v-html": "toHtmlAndBreak(b)"
                                }})
                            ]),
                            h(".wrapped", {attrs: {
                                "v-else": "",
                                "v-html": "toHtmlAndBreak(a[1])"
                            }})
                        ])
                    ]),
                    h("td", {attrs: {
                        "v-if": "hasSource",
                        "v-for": "c in hasSourceExtraCols",
                        ":key": "c"
                    }}, [
                        h(".wrapper", {attrs: {
                            ":style": "{width: (colWidths.extra - 20) + 'px'}"
                        }}, [
                            h(".wrapped", {attrs: {
                                "v-html": "toHtmlAndBreak(d[c])"
                            }})
                        ])
                    ]),
                    h("td", {attrs: {
                        "v-for": "c in extraCols",
                        ":key": "'data.' + c"
                    }}, [
                        h(".wrapper", {attrs: {
                            ":style": "{width: (colWidths.extra - 20) + 'px'}"
                        }}, [
                            h("pre.wrapped", "{{ d.data[c] }}")
                        ])
                    ]),
                    h("td")
                ])
            ])
        ]),
        h("entry-editor", {attrs: {
            "id": "new-entry-modal",
            "title": "Create new entry",
            "v-on:ok": "onEntrySaved"
        }}),
        h("entry-editor", {attrs: {
            "id": "edit-entry-modal",
            "title": "Edit entry",
            ":entry-id": "Array.from(checkedIds)[0]",
            "v-on:ok": "onEntrySaved"
        }}),
        h("img.page-loader", {attrs: {
            "src": "Spinner-1s-200px.svg",
            "v-if": "isLoading"
        }})
    ]).outerHTML
})
export default class EditorUi extends Vue {
    private cols = Columns;
    private extraCols: string[] = [];
    private hasSource = false;
    private q = "";
    private offset = 0;
    private limit = 10;
    private count = 0;
    private sortBy = "deck";
    private desc = false;
    private data: any[] = [];
    private canFetch = true;
    private checkedIds: Set<number> = new Set();
    private allCardsSelected = false;
    private isLoading = false;

    private readonly hasSourceExtraCols = [
        "source",
        // "model",
        "template"
    ]
    private readonly colWidths = {
        checkbox: 50,
        extra: 250
    }

    public mounted() {
        this.fetchData();
    }

    public updated() {
        if (this.canFetch) {
            this.fetchData();
        }
    }

    get editorLabel() {
        const from = this.count === 0 ? 0 : this.offset + 1;
        let to = this.offset + this.data.length;
        if (to < from) {
            to = from;
        }

        return `${from.toLocaleString()}-${to.toLocaleString()} of ${this.count.toLocaleString()}`;
    }

    get tableWidth(): number {
        return (
            this.colWidths.checkbox +
            this.cols.map((c) => c.width).reduce((a, v) => a + v) 
            + ((this.extraCols.length + 2) * this.colWidths.extra));
    }

    private getOrderedDict(d: any): any[][] {
        const output: any[][] = [];
        this.cols.forEach((c) => {
            output.push([c.name, d[c.name], c]);
        });

        return output;
    }

    private stringifyDate(d?: string): string {
        return d ? flatpickr.formatDate(new Date(d), DateFormat) : "";
    }

    private toHtmlAndBreak(s?: string): string {
        const div = document.createElement("div");
        div.innerText = s || "";
        return div.innerHTML.replace(/(\_)/g, "$1<wbr/>");
    }

    private async onEntrySaved() {
        this.reset();
        this.sortBy = this.checkedIds.size > 0 ? "modified" : "created";
        this.desc = true;
        this.fetchData();
    }

    private async deleteCards() {
        const r = await swal({
            text: "Are you sure you want to delete the following cards",
            buttons: [true, true],
            dangerMode: true
        })

        if (r) {
            this.isLoading = true;
            await fetchJSON("/api/editor/", {ids: Array.from(this.checkedIds)}, "DELETE");
            this.fetchData();
        }
    }

    private async changeDeck() {
        const deck = await swal({
            text: "What do you want to rename the deck to?",
            content: {
                element: "input"
            }
        });

        if (deck) {
            this.isLoading = true;
            await fetchJSON("/api/editor/", {
                ids: Array.from(this.checkedIds),
                update: {deck}
            }, "PUT")

            this.fetchData();
        }
    }

    private async editTags(isAdd: boolean) {
        const tags = await swal({
            text: `Please enter tag names you want to ${isAdd ? "add" : "remove"}.`,
            content: {
                element: "input",
                attributes: {
                    placeholder: "Separated by spaces"
                }
            }
        });

        if (tags) {
            this.isLoading = true;
            await fetchJSON(`/api/editor/editTags`, {
                ids: Array.from(this.checkedIds),
                tags: tags.split(" "),
                isAdd
            }, "PUT")

            this.fetchData();
        }
    }

    private onSearchbarKeypress(evt: any) {
        if (evt.key === "Enter") {
            this.fetchData();
        }
    }

    private onCheckboxClicked(evt: any, id?: number) {
        const checkboxMain = this.$refs["checkbox.main"] as HTMLInputElement;

        if (id) {
            const checkboxCurrent = evt.target as HTMLInputElement;
            if (checkboxCurrent.checked) {
                this.checkedIds.add(id);
            } else {
                this.checkedIds.delete(id);
            }
            console.log(this.checkedIds);
            this.calculateCheckboxMainStatus();
        } else {
            checkboxMain.indeterminate = false;
            if (checkboxMain.checked) {
                this.data.forEach((d) => {
                    this.checkedIds.add(d.id);
                });

                if (this.count > this.limit) {
                    toastr.warning("Do you want to select all cards?", "", {
                        closeButton: true,
                        positionClass: "toast-top-center",
                        closeHtml: h("button", "Select all").outerHTML,
                        onCloseClick: async () => {
                            this.isLoading = true;
                            const {ids} = await fetchJSON("/api/quiz/", {q: this.q, type: "all"});
                            this.checkedIds = new Set(ids);
                            this.allCardsSelected = true;
                            this.isLoading = false;
                        }
                    }).css({
                        width: "400px",
                        "max-width": "400px"
                    });
                }
            } else {
                this.allCardsSelected = false;
                this.checkedIds.clear();
            }
        }

        this.$forceUpdate();
    }

    private onTableHeaderClicked(name: string) {
        if (this.sortBy === name) {
            this.desc = !this.desc
        } else {
            this.sortBy = name
            this.desc = false
        }
    }

    private onTableRowClicked(id: number) {
        const availableIds = new Set(this.data.map((row) => row.id));

        this.checkedIds.forEach((c) => {
            if (!availableIds.has(c)) {
                this.checkedIds.delete(c);
            }
        });

        if (this.checkedIds.has(id)) {
            this.checkedIds.delete(id);
        } else {
            this.checkedIds.add(id);
        }

        this.calculateCheckboxMainStatus();
        this.$forceUpdate();
    }

    private getHtml(data: any, side: "front" | "back" | "note"): string {
        return quizDataToContent(data, side);
    }

    private calculateCheckboxMainStatus() {
        const checkboxMain = this.$refs["checkbox.main"] as HTMLInputElement;
        this.allCardsSelected = false;
        checkboxMain.indeterminate = this.checkedIds.size > 0 && this.checkedIds.size < this.data.length;
    }

    private reset(clearSearchParams: boolean = true) {
        if (clearSearchParams) {
            this.q = "";
            this.offset = 0;
        }

        this.allCardsSelected = false;
        const checkboxMain = this.$refs["checkbox.main"] as HTMLInputElement;
        checkboxMain.indeterminate = false;
        this.checkedIds.clear();
    }

    @Watch("offset")
    @Watch("sortBy")
    @Watch("desc")
    private async fetchData() {
        this.canFetch = false;

        if (isNaN(this.offset)) {
            this.offset = this.count - this.limit;
        } else if (this.offset < 0) {
            this.offset = 0;
        }

        this.isLoading = true;

        const r = await fetchJSON("/api/editor/", {q: this.q, offset: this.offset, limit: this.limit, 
            sortBy: this.sortBy, desc: this.desc});

        this.data = r.data;
        this.count = r.count;

        this.reset(false);
        document.getElementById("editorTable")!.scrollIntoView();

        this.extraCols = [];
        for (const d of this.data) {
            if (d.data) {
                for (const k of Object.keys(d.data)) {
                    if (this.extraCols.indexOf(k) === -1) {
                        this.extraCols.push(k);
                    }
                }
            }
        }
        this.hasSource = (this.extraCols.length > 0);
        this.isLoading = false;
    }
}
