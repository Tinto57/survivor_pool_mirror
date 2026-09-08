/**
 * Génération de documents .rtf côté client : Word l'ouvre nativement, sans
 * dépendance ni aller-retour serveur. Le Markdown ne convient pas pour un
 * livrable "à coller dans un document Word" — le RTF, si.
 */

function escapeRtf(text: string): string {
    let out = "";
    for (const char of text) {
        const code = char.codePointAt(0)!;
        if (char === "\\" || char === "{" || char === "}") {
            out += `\\${char}`;
        } else if (code === 10) {
            out += "\\line ";
        } else if (code < 128) {
            out += char;
        } else {
            // Échappement Unicode RTF : toute la table hors ASCII passe par là,
            // pas seulement les caractères accentués français.
            const signed = code > 32767 ? code - 65536 : code;
            out += `\\u${signed}?`;
        }
    }
    return out;
}

export function rtfTitle(text: string): string {
    return `{\\pard\\sa240\\sb0\\b\\fs36 ${escapeRtf(text)}\\par}`;
}

export function rtfHeading1(text: string): string {
    return `{\\pard\\sa160\\sb320\\b\\fs28 ${escapeRtf(text)}\\par}`;
}

export function rtfHeading2(text: string): string {
    return `{\\pard\\sa120\\sb240\\b\\fs24 ${escapeRtf(text)}\\par}`;
}

export function rtfParagraph(text: string, opts?: { italic?: boolean; bold?: boolean }): string {
    const style = `${opts?.bold ? "\\b " : ""}${opts?.italic ? "\\i " : ""}`;
    return `{\\pard\\sa160\\fs20 ${style}${escapeRtf(text)}\\par}`;
}

export function rtfBullet(text: string): string {
    return `{\\pard\\fi-240\\li480\\sa80\\fs20 \\u8226?\\tab ${escapeRtf(text)}\\par}`;
}

export function rtfSubBullet(text: string): string {
    return `{\\pard\\fi-240\\li960\\sa60\\fs20 \\u8211?\\tab ${escapeRtf(text)}\\par}`;
}

export function rtfSpacer(): string {
    return `{\\pard\\sa120\\fs10 \\par}`;
}

export function buildRtfDocument(title: string, blocks: string[]): string {
    const header =
        "{\\rtf1\\ansi\\ansicpg1252\\deff0\\deflang1036" +
        "{\\fonttbl{\\f0\\fswiss\\fcharset0 Arial;}}" +
        "\\f0";
    const body = [rtfTitle(title), ...blocks].join("\n");
    return `${header}\n${body}\n}`;
}

export function downloadRtf(filename: string, content: string): void {
    const blob = new Blob([content], { type: "application/rtf" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename.endsWith(".rtf") ? filename : `${filename}.rtf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
