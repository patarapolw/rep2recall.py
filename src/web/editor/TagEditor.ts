import { Vue, Component, Prop, Emit } from "vue-property-decorator";
import h from "hyperscript";

@Component({
    template: h(".input-group.col-form-label", [
        h("input.form-control", {attrs: {
            ":value": "computedValue.join(' ')",
            "v-on:input": "onFormInput",
            "placeholder": "Please input tags separated by spaces"
        }}),
        h(".input-group-append", [
            h("button.btn.btn-success.input-group-text", {attrs: {
                ":disabled": "computedValue.indexOf('marked') !== -1",
                "v-on:click": "onMarkButtonClicked"
            }}, "Mark")
        ])
    ]).outerHTML
})
export default class TagEditor extends Vue {
    @Prop() value: string[] = [];

    get computedValue() {
        return this.value.slice();
    }

    @Emit("input")
    private onFormInput(evt: any) {
        const vs = new Set(evt.target.value.split(" "));
        return Array.from(vs).filter((v) => v);
    }

    @Emit("input")
    private onMarkButtonClicked() {
        const vs = new Set(this.computedValue);
        vs.add("marked");
        return Array.from(vs).filter((v) => v);
    }
}
