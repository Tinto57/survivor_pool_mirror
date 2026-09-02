const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isValidEmail(email: string): boolean {
    return EMAIL_REGEX.test(email);
}

export type PasswordRequirement = {
    id: string;
    label: string;
    test: (password: string) => boolean;
};

export const PASSWORD_REQUIREMENTS: PasswordRequirement[] = [
    { id: "length", label: "Au moins 8 caractères", test: (p) => p.length >= 8 },
    { id: "lower", label: "Une minuscule", test: (p) => /[a-z]/.test(p) },
    { id: "upper", label: "Une majuscule", test: (p) => /[A-Z]/.test(p) },
    { id: "digit", label: "Un chiffre", test: (p) => /\d/.test(p) },
    { id: "special", label: "Un caractère spécial", test: (p) => /[^A-Za-z0-9]/.test(p) },
];

export function isStrongPassword(password: string): boolean {
    return PASSWORD_REQUIREMENTS.every((r) => r.test(password));
}
