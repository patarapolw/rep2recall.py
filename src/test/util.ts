import { inspect } from "util";

export function pp(obj: any) {
    console.log(inspect(obj, { depth: null, colors: true }))
}