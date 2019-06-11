import showdown from "showdown";
import { ServerPort } from "./shared";
import swal from "sweetalert";

export function shuffle(a: any[]) {
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

export function toTitle(s: string) {
    return s[0].toLocaleUpperCase() + s.slice(1);
}

export async function fetchJSON(url: string, data: any = {}, method: string = "POST"): Promise<any> {
    const start = new Date().getSeconds();
    let error = "Cannot connect to server.";

    while (new Date().getSeconds() - start < 10) {
        try {
            const res = await fetch(new URL(url, `http://localhost:${ServerPort}`).href, {
                method,
                headers: {
                    "Content-Type": "application/json; charset=utf-8"
                },
                body: JSON.stringify(data)
            });

            let result = {} as any;

            try {
                result = await res.json();
                if (result.error) {
                    await swal({
                        text: result.error,
                        icon: "error"
                    });
                }
            } catch (e) {
                await swal({
                    text: res.statusText,
                    icon: "error"
                });
                return {error: e};
            }

            return result;
        } catch (e) {
            console.error(e);

            error = e.toString();
            await new Promise((resolve) => {
                setTimeout(resolve, 1000);
            })
        }
    }

    await swal({
        text: error,
        icon: "error"
    });
}

const anchorAttributes = {
    type: 'output',
    regex: /()\((.+=".+" ?)+\)/g,
    replace: (match: any, $1: string, $2: string) => {
        return $1.replace('">', `" ${$2}>`);
    }
};

const fixLinks = {
    type: "output",
    regex: /((?:src|href)="\/)([^"]+)(")/g,
    replace: `$1http://localhost:${ServerPort}/$2$3`
}

const furiganaParser = {
    type: "output",
    regex: /{([^}]+)}\(([^)]+)\)/g,
    replace: "<ruby>$1<rp>(</rp><rt>$2</rt><rp>)</rp></ruby>"
}

showdown.extension('anchorAttributes', anchorAttributes);
showdown.extension('fixLinks', fixLinks);
showdown.extension('furiganaParser', furiganaParser);
const mdConverter = new showdown.Converter({
    tables: true,
    extensions: ['anchorAttributes', 'fixLinks', 'furiganaParser']
});

export function md2html(s: string): string {
    return mdConverter.makeHtml(s);
}

function fixHtml(s: string): string {
    for (const fix of [fixLinks, furiganaParser]) {
        s = s.replace(fix.regex, fix.replace)
    };
    return s;
}

export function html2md(s: string): string {
    // return s;
    return removeTag(s, "script");
}

export function normalizeArray(item: any, forced: boolean = true) {
    if (Array.isArray(item)) {
        if (forced || item.length == 1) {
            return item[0];
        }
    }

    return item;
}

export function quizDataToContent(data: any, side: "front" | "back" | "note" | "backAndNote"): string {
    function cleanHtml(s: string) {
        const m = /^@([^\n]+)\n(.+)$/s.exec(s);
        return m ? fixHtml(m[2]) : md2html(s);
    }

    function cleanCssJs(s: string, type: "css" | "js") {
        const m = /^@([^\n]+)\n(.+)$/s.exec(s);
        if (m) {
            return m[1] === "raw" ? m[2] : (type === "css" ? `<style>${m[2]}</style>` : `<script>${m[2]}</script>`)
        } else {
            return type === "css" ? `<style>${s}</style>` : `<script>${s}</script>`;
        }
    }

    return `
    ${data.css ? cleanCssJs(data.css, "css") :`<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">`}
    ${side === "backAndNote" ? 
    cleanHtml(data.back || "") + "\n<br/>\n" + cleanHtml(data.note || "") : cleanHtml(data[side] || "")}
    ${!data.js ? `<script src="https://code.jquery.com/jquery-3.4.1.min.js" integrity="sha256-CSXorXvZcTkaix6Yvo6HppcZGetbYMGWSFlBw8HfCJo=" crossorigin="anonymous"></script>` : cleanCssJs(data.js, "js")}
    `;
}

export function slowClickHandler(evt: any) {
    // console.log(evt.originalEvent);
    const duration = 100;

    if (evt.originalEvent !== undefined) {
        const $selector = $(evt.target);
        // $selector.prop("disabled", true);

        $selector.addClass("animated");
        $selector.css({
            "animation-duration": `${duration}ms`
        });

        setTimeout(() => {
            // $selector.prop("disabled", false);
            $selector.removeClass("animated");
        }, duration);
    }
}

export function slowClick($selector: JQuery) {
    const duration = 100;

    $selector.addClass("animated");
    $selector.css({
        "animation-duration": `${duration}ms`
    });
    setTimeout(() => {
        $selector.click();
        $selector.removeClass("animated");
    }, duration);

    return $selector;
}

export function removeTag(s: string, tag: string): string {
    return s.replace(new RegExp(`<${tag}[^>]*>.*</${tag}>`, "gs"), "")
}
