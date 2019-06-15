import h from "hyperscript";
import "./index.scss";
import Vue from "vue";
import VueRouter from "vue-router";
import BootstrapVue from "bootstrap-vue";
import "bootstrap";
import $ from "jquery";
import QuizUi from "./QuizUi";
import EditorUi from "./EditorUi";
import ImportUi from "./ImportUi";
import "./contextmenu";
import SettingsUi from "./SettingsUi";
import { slowClick } from "./util";

$(() => {
    // @ts-ignore
    $('.tooltip-enabled').tooltip({trigger: "hover"});
    $(document.body).on("mousedown", "button", (evt) => {
        const $this = $(evt.target);
        $this.prop("disabled", true);
        slowClick($this);
    })
});


Vue.use(VueRouter);
Vue.use(BootstrapVue);

const router = new VueRouter({
    routes: [
        {path: "/", component: QuizUi},
        {path: "/quiz", component: QuizUi},
        {path: "/editor", component: EditorUi},
        {path: "/import", component: ImportUi},
        {path: "/settings", component: SettingsUi}
    ]
});

const app = new Vue({
    router,
    template: h(".stretched", [
        h("ul.nav.flex-column", [
            h("li.nav-item", [
                h("router-link.far.fa-question-circle.nav-icon.nav-link.tooltip-enabled", {
                    title: "Quiz",
                    attrs: {to: "/quiz"}
                })
            ]),
            h("li.nav-item", [
                h("router-link.far.fa-edit.nav-icon.nav-link.tooltip-enabled", {
                    title: "Editor",
                    attrs: {to: "/editor"}
                }),
            ]),
            h("li.nav-item", [
                h("router-link.fas.fa-file-import.nav-icon.nav-link.tooltip-enabled", {
                    title: "Import",
                    attrs: {to: "/import"}
                }),
            ]),
            h("li.nav-item", [
                h("router-link.fas.fa-cog.nav-icon.nav-link.tooltip-enabled", {
                    title: "Settings",
                    attrs: {to: "/settings"}
                }),
            ]),
            h("li.nav-item", [
                h("a.fab.fa-github.nav-icon.nav-link.tooltip-enabled", {
                    title: "About",
                    href: "https://github.com/patarapolw/rep2recall-py",
                    target: "_blank"
                })
            ])
        ]),
        h(".body", [
            h("router-view")
        ])
    ]).outerHTML
}).$mount("#App");
