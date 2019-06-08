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

    while (new Date().getSeconds() - start < 10) {
        try {
            const res = await fetch(new URL(url, `http://localhost:${ServerPort}`).href, {
                method,
                headers: {
                    "Content-Type": "application/json; charset=utf-8"
                },
                body: JSON.stringify(data)
            });

            try {
                return await res.json();
            } catch (e) {
                if (res.status < 400) {
                    return res.status;
                } else {
                    throw e;
                }
            }
        } catch (e) {
            await new Promise((resolve) => {
                setTimeout(resolve, 1000);
            })
        }
    }

    // @ts-ignore
    const r = await swal({
        text: "Cannot connect to server. Retry?",
        icon: "error",
        buttons: true
    })

    if (r) {
        return await fetchJSON(url, data, method);
    }
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
    regex: /(src|href=")([^"]+)(")/g,
    replace: `$1http://localhost:${ServerPort}/$2$3`
}

showdown.extension('anchorAttributes', anchorAttributes);
showdown.extension('fixLinks', fixLinks);
const mdConverter = new showdown.Converter({
    tables: true,
    extensions: ['anchorAttributes', 'fixLinks']
});

export function md2html(s: string): string {
    return mdConverter.makeHtml(s);
}

export function html2md(s: string): string {
    return s;
    // return s.replace(/<script[^>]*>.*<\/script>/gs, "");
}

export function makeCamelSpaced(s: string): string {
    const tokens: string[] = [];
    let previousStart = -1;

    s.split("").forEach((c, i) => {
        if (c === c.toLocaleUpperCase()) {
            tokens.push(s.substr(previousStart + 1, i));
            previousStart = i - 1;
        }
    });

    if (previousStart < s.length - 2) {
        tokens.push(s.substr(previousStart + 1));
    }

    return tokens.map((t) => t[0].toLocaleUpperCase() + t.substr(1)).join(" ");
}

export function normalizeArray(item: any, forced: boolean = true) {
    if (Array.isArray(item)) {
        if (forced || item.length == 1) {
            return item[0];
        }
    }

    return item;
}

export function quizDataToContent(data: any, side: "front" | "back" | "note"): string {
    const m = /@([^\n]+)\n(.+)/s.exec(data[side]);

    return `
    ${!data.css ? `<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">` : ""}
    <style>${data.css || ""}</style>
    ${m ? m[2] : md2html(data[side] || "")}
    ${!data.js ? `<script src="https://code.jquery.com/jquery-3.4.1.min.js" integrity="sha256-CSXorXvZcTkaix6Yvo6HppcZGetbYMGWSFlBw8HfCJo=" crossorigin="anonymous"></script>` : ""}
    <script>${data.js || ""}</script>
    `;
}

export function slowClick($selector: JQuery, doClick: boolean = true, duration: number = 100) {
    $selector.addClass("animated");
    $selector.css({
        "animation-duration": `${duration}ms`
    });
    setTimeout(() => {
        if (doClick) {
            $selector.click();
        }
        $selector.removeClass("animated");
    }, duration);
    return $selector;
}
