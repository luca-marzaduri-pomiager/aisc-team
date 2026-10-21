/** Presentation label only; keep the original package ID in requests and state. */
export function packageLabel(name: string): string {
    return name.replace(/^aisc-plugin-/i, '').replace(/-/g, ' ');
}
