export interface IColumn {
    name: string;
    width?: number;
    readOnly?: boolean;
    label: string;
    type?: "string" | "html" | "number" | "datetime" | "tag" | "multiline";
    newEntry?: boolean;
    editEntry?: boolean;
    separator?: string;
    required?: boolean;
    requiredText?: string;
    parse?: (x: string) => any;
    constraint?: (x: any) => boolean;
}

export const Columns: IColumn[] = [
    {name: "deck", width: 200, type: "string", required: true, label: "Deck"},
    {name: "front", width: 400, type: "html", required: true, label: "Front"},
    {name: "back", width: 400, type: "html", label: "Back"},
    {name: "tag", width: 200, type: "tag", separator: " ", label: "Tags"},
    {name: "mnemonic", width: 300, type: "html", label: "Mnemonic"},
    {name: "srsLevel", width: 200, type: "number", label: "SRS Level", newEntry: false},
    {name: "nextReview", width: 250, type: "datetime", label: "Next Review", newEntry: false}
];

export const DateFormat = "Y-M-d H:i";
