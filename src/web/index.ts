import h from "hyperscript";
import "./index.scss";
import Vue from "vue";
import VueRouter from "vue-router";
import BootstrapVue from "bootstrap-vue";
// @ts-ignore
import VueSimplemde from "vue-simplemde";
import "bootstrap";
import $ from "jquery";
import QuizUi from "./QuizUi";
import EditorUi from "./EditorUi";
import ImportUi from "./ImportUi";
import "./contextmenu";
import SettingsUi from "./SettingsUi";
import { slowClickHandler } from "./util";

$(() => {
    // @ts-ignore
    $('.tooltip-enabled').tooltip();
    $(document.body).on("click", "button", slowClickHandler);
});


Vue.use(VueRouter);
Vue.use(BootstrapVue);
Vue.use(VueSimplemde);

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
        h(".navbar.float-left", [
            h("router-link.far.fa-question-circle.tooltip-enabled.nav-icon", {
                title: "Quiz",
                attrs: {to: "/quiz"}
            }),
            h("router-link.far.fa-edit.tooltip-enabled.nav-icon", {
                title: "Editor",
                attrs: {to: "/editor"}
            }),
            h("router-link.fas.fa-file-import.tooltip-enabled.nav-icon", {
                title: "Import",
                attrs: {to: "/import"}
            }),
            h("router-link.fas.fa-cog.tooltip-enabled.nav-icon", {
                title: "Settings",
                attrs: {to: "/settings"}
            }),
            h("a.fab.fa-github.tooltip-enabled.nav-icon", {
                title: "About",
                href: "https://github.com/patarapolw/rep2recall-py",
                target: "_blank"
            })
        ]),
        h(".body", [
            h("router-view")
        ])
    ]).outerHTML
}).$mount("#App");
