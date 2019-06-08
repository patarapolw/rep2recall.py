import { Vue, Component, Watch } from "vue-property-decorator";
import h from "hyperscript";
import TreeviewItem, { ITreeViewItem } from "./quiz/TreeviewItem";
import { fetchJSON, shuffle, quizDataToContent, slowClick } from "./util";
import swal from "sweetalert";
import EntryEditor from "./editor/EntryEditor";
import $ from "jquery";

@Component({
    components: { TreeviewItem, EntryEditor },
    template: h(".container.mt-3", [
        h("div.ml-3", [
            h("i", "Click or right-click deck names to start reviewing.")
        ]),
        h("input.form-control", {
            placeholder: "Type here to search",
            attrs: {
                "v-model": "q",
                "v-on:keyup": "onInputKeypress",
                "spellcheck": "false",
                "autocomplete": "off",
                "autocorrect": "off",
                "autocapitalize": "off"
            }
        }, "{{ q }}"),
        h(".treeview", [
            h("img.small-spinner", {
                src: "Spinner-1s-200px.svg",
                attrs: {
                    ":style": "{display: isLoading ? 'block' : 'none'}"
                }
            }),
            h("ul", [
                h("treeview-item", {attrs: {
                    "v-for": "c in data",
                    ":key": "c.fullName",
                    ":data": "c",
                    ":q": "q",
                    ":parent-is-open": "true",
                    ":on-review": "onReview",
                    ":on-delete": "onDelete"
                }})
            ])
        ]),
        h("b-modal.quiz-modal", {attrs: {
            "id": "quiz-modal",
            "scrollable": "",
            "hide-header": "",
            "v-on:show": "onQuizShown",
            "v-on:hide": "getTreeViewData"
        }}, [
            h("iframe", {attrs: {
                ":srcdoc": "quizContent",
                "height": "500",
                "width": "450",
                "frameBorder": "0"
            }}),
            h(".w-100.d-flex.justify-content-between", {attrs: {
                "slot": "modal-footer",
            }}, [
                h("div", {style: {width: "50px"}}, [
                    h("button.btn.btn-secondary.quiz-previous", {attrs: {
                        "v-if": "currentQuizIndex > 0",
                        "v-on:click": "onQuizPreviousButtonClicked"
                    }}, "<")
                ]),
                h("div", [
                    h("button.btn.ml-2.quiz-toggle", {attrs: {
                        "v-if": "currentQuizIndex >= 0",
                        "v-on:click": "quizShownAnswer = !quizShownAnswer",
                        ":class": "quizShownAnswer ? 'btn-secondary' : 'btn-primary'"
                    }}, "{{quizShownAnswer ? 'Hide' : 'Show'}}"),
                    h("button.btn.btn-success.ml-2.quiz-right", {attrs: {
                        "v-if": "quizShownAnswer",
                        "v-on:click": "onQuizRightButtonClicked"
                    }}, "Right"),
                    h("button.btn.btn-danger.ml-2.quiz-wrong", {attrs: {
                        "v-if": "quizShownAnswer",
                        "v-on:click": "onQuizWrongButtonClicked"
                    }}, "Wrong"),
                    h("b-button.ml-2.quiz-edit", {attrs: {
                        "variant": "info",
                        "v-if": "quizShownAnswer",
                        "v-b-modal.edit-entry-modal": ""
                    }}, "Edit"),
                ]),
                h("div", {style: {width: "50px"}}, [
                    h("b-button.float-right.quiz-next", {attrs: {
                        "v-if": "quizIds.length > 0",
                        "v-on:click": "onQuizNextButtonClicked",
                        ":variant": "currentQuizIndex < quizIds.length - 1 ? 'secondary' : 'success'"
                    }}, ">")
                ])
            ])
        ]),
        h("entry-editor", {attrs: {
            "id": "edit-entry-modal",
            "title": "Edit entry",
            ":entry-id": "quizIds[currentQuizIndex]",
            "v-on:ok": "onEntrySaved"
        }})
    ]).outerHTML
})
export default class QuizUi extends Vue {
    private isLoading = true;
    private data: ITreeViewItem[] = [];
    private q = "";

    private quizIds: number[] = [];
    private currentQuizIndex: number = -1;
    private quizContent = "";
    private quizShownAnswer = false;
    private quizData: any = {};

    private selectedDeck = "";

    constructor(props: any) {
        super(props);
        $(document.body).on("keydown", "#quiz-modal", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                const $toggle = $(".quiz-toggle");
                if ($toggle.length > 0) {
                    slowClick($toggle);
                } else {
                    slowClick($(".quiz-next"));
                }
            } else if (e.key === "Backspace" || e.key === "ArrowLeft") {
                slowClick($(".quiz-previous"));
            } else if (e.key === "1") {
                slowClick($(".quiz-right"));
            } else if (e.key === "2") {
                slowClick($(".quiz-wrong"));
            } else if (e.key === "3") {
                slowClick($(".quiz-edit"));
            } else if (e.key === "ArrowDown") {
                slowClick($(".quiz-toggle"));
            } else if (e.key === "ArrowRight") {
                slowClick($(".quiz-next"));
            }
        });
    }

    public mounted() {
        this.getTreeViewData();
    }

    public update() {
        this.getTreeViewData();
    }

    private onInputKeypress(evt: any) {
        if (evt.key === "Enter") {
            this.getTreeViewData();
        }
    }

    private onQuizShown() {
        this.currentQuizIndex = -1;
        this.quizIds = [];
        this.quizShownAnswer = false;
        this.quizContent = "";
    }

    private async onReview(deck: string, type?: string) {
        this.$bvModal.show("quiz-modal");

        const {ids} = await fetchJSON("/api/quiz/", {deck, q: this.q, type})

        this.quizIds = shuffle(ids);
        this.quizContent = h("div", `${ids.length.toLocaleString()} entries to go...`).outerHTML;
        if (ids.length === 0) {
            const [nextHour, nextDay] = await Promise.all([
                fetchJSON("/api/quiz/", {deck, q: this.q, type, due: "1h"}),
                fetchJSON("/api/quiz/", {deck, q: this.q, type, due: "1d"})
            ]);

            this.quizContent += h("div", [
                h("div", `Pending next hour: ${nextHour.ids.length.toLocaleString()}`),
                h("div", `Pending next day: ${nextDay.ids.length.toLocaleString()}`)
            ]).outerHTML;
        }
    }

    private async onDelete(deck: string): Promise<boolean> {
        const r = await swal({
            text: `Are you sure you want to delete ${deck}?`,
            icon: "warning",
            dangerMode: true,
            buttons: [true, true]
        })

        if (r) {
            const {ids} = await fetchJSON("/api/quiz/", {deck, q: this.q, type: "all"})
            await fetchJSON("/api/editor/", {ids}, "DELETE");
            await swal({
                text: `Deleted ${deck}`,
                icon: "success"
            });
            this.$forceUpdate();
            return true;
        }

        return false;
    }

    private async onQuizPreviousButtonClicked() {
        if (this.currentQuizIndex > 0) {
            this.currentQuizIndex--;
            await this.renderQuizContent();
        }
    }

    private async onQuizNextButtonClicked() {
        if (this.currentQuizIndex < this.quizIds.length - 1) {
            this.currentQuizIndex += 1;
            await this.renderQuizContent();
        } else {
            await swal({
                text: "Quiz is done!",
                icon: "success"
            });
            this.$bvModal.hide("quiz-modal");
        }
    }

    @Watch("quizShownAnswer")
    private onQuizShowButtonClicked() {
        if (this.quizShownAnswer) {
            this.quizContent = quizDataToContent(this.quizData, "back");
        } else {
            this.quizContent = quizDataToContent(this.quizData, "front");
        }
    }

    private async onQuizRightButtonClicked() {
        if (this.quizShownAnswer) {
            const id = this.quizIds[this.currentQuizIndex];
            await fetchJSON("/api/quiz/right", {id}, "PUT")
            await this.onQuizNextButtonClicked();
        }
    }

    private async onQuizWrongButtonClicked() {
        if (this.quizShownAnswer) {
            const id = this.quizIds[this.currentQuizIndex];
            await fetchJSON("/api/quiz/wrong", {id}, "PUT")
            await this.onQuizNextButtonClicked();
        }
    }

    private async onEntrySaved(data: any) {
        await fetchJSON("/api/editor/", {id: data.id, update: data}, "PUT");
        Object.assign(this.quizData, data);
    }

    private async getTreeViewData() {
        this.isLoading = true;
        this.data = await fetchJSON("/api/quiz/treeview", {q: this.q});
        this.isLoading = false;
    }

    private async renderQuizContent() {
        this.quizShownAnswer = false;
        const id = this.quizIds[this.currentQuizIndex];
        if (id) {
            this.quizData = await fetchJSON("/api/quiz/render", {id});
            this.quizContent = quizDataToContent(this.quizData, "front");
        }
    }
}
