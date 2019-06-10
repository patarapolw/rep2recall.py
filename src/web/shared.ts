export interface IColumn {
    name: string;
    width: number;
    readOnly?: boolean;
    label: string;
    type?: "string" | "html" | "number" | "datetime" | "tag";
    newEntry?: boolean;
    editEntry?: boolean;
    separator?: string;
    required?: boolean;
    requiredText?: string;
    parse?: (x: string) => any;
    constraint?: (x: any) => boolean;
}

export const Columns: IColumn[] = [
    {name: "deck", width: 150, type: "string", required: true, label: "Deck"},
    {name: "template", width: 150, type: "string", newEntry: false, label: "Template"},
    {name: "front", width: 400, type: "html", required: true, label: "Front"},
    {name: "back", width: 400, type: "html", label: "Back"},
    {name: "tag", width: 150, type: "tag", separator: " ", label: "Tags"},
    {name: "note", width: 300, type: "html", label: "Note"},
    {name: "srsLevel", width: 150, type: "number", label: "SRS Level", newEntry: false},
    {name: "nextReview", width: 350, type: "datetime", label: "Next Review", newEntry: false}
];

export const DateFormat = "Y-M-d H:i";
export const ServerPort = 34972;
