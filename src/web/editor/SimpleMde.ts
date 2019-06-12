import { Vue, Component, Prop } from "vue-property-decorator";
import h from "hyperscript";
import SimpleMDE from "simplemde";
import { normalizeArray, quizDataToContent, ankiMustache } from "../util";
import $ from "jquery";

@Component({
    template: h(".w-100.markdown-editor", [
        h(".w-100", {attrs: {
            ":class": "required ? 'form-required' : 'form-not-required'"
        }}, [
            h("textarea", {attrs: {
                "ref": "mde",
                ":value": "value"
            }})
        ]),
        h("input.form-control.flatten", {attrs: {
            ":required": "required",
            ":value": "value"
        }}),
        h(".invalid-feedback", "{{ invalidFeedback || '' }}")
    ]).outerHTML
})
export default class SimpleMde extends Vue {
    @Prop() required?: boolean;
    @Prop() value?: string;
    @Prop() invalidFeedback?: string;
    @Prop() data: any;

    private mde!: SimpleMDE;

    public mounted() {
        this.mde = new SimpleMDE({
            element: normalizeArray(this.$refs.mde),
            spellChecker: false,
            status: false,
            previewRender: (s: string) => {
                return h("iframe", {
                    "srcdoc": quizDataToContent(this.data, null, ankiMustache(s, this.data)),
                    "frameBorder": "0"
                }).outerHTML;
            }
        });
        this.mde.codemirror.on("change", (_: any, c: any) => {
            if (c.origin !== "setValue") {
                this.$emit("input", this.mde.value());
            }
        });
    }

    public updated() {
        this.mde.value(this.value || "");
    }
}
