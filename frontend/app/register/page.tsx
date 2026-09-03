"use client";

import { useState, useRef, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import styles from "../components/AuthForm/AuthForm.module.css";
import { User, Lock, Mail, Eye, EyeOff, Store, MapPin, FileText, Check, X, Loader2, AlertCircle } from "lucide-react";
import { isValidEmail, isStrongPassword, PASSWORD_REQUIREMENTS } from "../lib/validation";
import { ApiError, register } from "../lib/api";
import { homePathForRole, startSession } from "../lib/auth";

const STEP_COUNT = 3;

type GeocodeStatus = "idle" | "loading" | "success" | "error";

type AddressSuggestion = {
    label: string;
    lat: number;
    lon: number;
};

export default function RegisterPage() {
    const router = useRouter();
    const [step, setStep] = useState(1);

    const [firstName, setFirstName] = useState("");
    const [lastName, setLastName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);

    const [business_name, setBusinessName] = useState("");
    const [siren, setSiren] = useState("");
    const [address, setAddress] = useState("");
    const [businessPurpose, setBusinessPurpose] = useState("");

    const [latitude, setLatitude] = useState<number | null>(null);
    const [longitude, setLongitude] = useState<number | null>(null);
    const [geocodeStatus, setGeocodeStatus] = useState<GeocodeStatus>("idle");
    const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    async function fetchSuggestions(query: string) {
        if (query.trim().length < 3) {
            setSuggestions([]);
            setGeocodeStatus("idle");
            return;
        }

        setGeocodeStatus("loading");
        try {
            const res = await fetch(
                `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(query)}&limit=5`
            );
            const data = await res.json();
            const results: AddressSuggestion[] = (data.features ?? []).map(
                (feature: { properties: { label: string }; geometry: { coordinates: [number, number] } }) => ({
                    label: feature.properties.label,
                    lon: feature.geometry.coordinates[0],
                    lat: feature.geometry.coordinates[1],
                })
            );

            setSuggestions(results);
            setShowSuggestions(true);
            setGeocodeStatus(results.length > 0 ? "idle" : "error");
        } catch {
            setSuggestions([]);
            setGeocodeStatus("error");
        }
    }

    function handleAddressChange(value: string) {
        setAddress(value);
        setLatitude(null);
        setLongitude(null);
        setGeocodeStatus("idle");

        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => fetchSuggestions(value), 300);
    }

    function selectSuggestion(suggestion: AddressSuggestion) {
        setAddress(suggestion.label);
        setLatitude(suggestion.lat);
        setLongitude(suggestion.lon);
        setGeocodeStatus("success");
        setSuggestions([]);
        setShowSuggestions(false);
    }

    function goNext() {
        setError(null);

        if (step === 1) {
            if (!email || !password) {
                setError("Merci de remplir tous les champs.");
                return;
            }
            if (!isValidEmail(email)) {
                setError("Adresse email invalide.");
                return;
            }
            if (!isStrongPassword(password)) {
                setError("Le mot de passe ne respecte pas les critères ci-dessous.");
                return;
            }
            if (password !== confirmPassword) {
                setError("Les mots de passe ne correspondent pas.");
                return;
            }
        }

        if (step === 2) {
            if (!firstName || !lastName) {
                setError("Merci de remplir tous les champs.");
                return;
            }
        }

        setStep((s) => Math.min(s + 1, STEP_COUNT));
    }

    function goBack() {
        setError(null);
        setStep((s) => Math.max(s - 1, 1));
    }

    async function handleSubmit(e: FormEvent) {
        e.preventDefault();
        setError(null);

        if (!business_name || !address || !businessPurpose) {
            setError("Merci de remplir tous les champs.");
            return;
        }

        if (!/^\d{9}$/.test(siren)) {
            setError("Le SIREN doit contenir exactement 9 chiffres.");
            return;
        }

        setLoading(true);
        try {
            const { user, token } = await register({
                username: email,
                password,
                first_name: firstName,
                last_name: lastName,
                email,
                role: "partner",
                partner: {
                    business_name,
                    siren,
                    business_purpose: businessPurpose,
                    address,
                    latitude,
                    longitude,
                },
            });

            startSession(user, token);
            router.push(homePathForRole(user.role));
        } catch (err) {
            if (err instanceof ApiError && err.status === 400) {
                setError("Cet email est déjà utilisé par un compte existant.");
                setStep(1);
            } else {
                setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
            }
            setLoading(false);
        }
    }

    return (
        <div className={styles.wrapper}>
            <div className={styles.card}>
                <h1 className={styles.title}>Devenir partenaire</h1>
                <p className={styles.subtitle}>
                    Créez votre compte partenaire Ticket Tout. Les salariés reçoivent leurs
                    identifiants directement de leur employeur.
                </p>

                <div className={styles.steps}>
                    {Array.from({ length: STEP_COUNT }, (_, i) => i + 1).map((n) => (
                        <div className={styles.step} key={n}>
                            <div
                                className={`${styles.stepCircle} ${
                                    n === step
                                        ? styles.stepCircleActive
                                        : n < step
                                        ? styles.stepCircleDone
                                        : ""
                                }`}
                            >
                                {n < step ? <Check size={14} /> : n}
                            </div>
                            {n < STEP_COUNT && (
                                <div className={`${styles.stepLine} ${n < step ? styles.stepLineDone : ""}`} />
                            )}
                        </div>
                    ))}
                </div>

                <form onSubmit={step === STEP_COUNT ? handleSubmit : (e) => e.preventDefault()}>
                    {step === 1 && (
                        <>
                            <h2 className={styles.stepTitle}>Identifiants</h2>

                            <div className={styles.field}>
                                <label className={styles.label} htmlFor="email">
                                    Email
                                </label>
                                <div className={styles.inputWrapper}>
                                    <Mail />
                                    <input
                                        id="email"
                                        type="email"
                                        className={styles.input}
                                        placeholder="jean.dupont@email.fr"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        autoComplete="email"
                                    />
                                </div>
                            </div>

                            <div className={styles.field}>
                                <label className={styles.label} htmlFor="password">
                                    Mot de passe
                                </label>
                                <div className={styles.inputWrapper}>
                                    <Lock />
                                    <input
                                        id="password"
                                        type={showPassword ? "text" : "password"}
                                        className={styles.input}
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        autoComplete="new-password"
                                    />
                                    <button
                                        type="button"
                                        className={styles.passwordToggle}
                                        onClick={() => setShowPassword((v) => !v)}
                                        aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                                    >
                                        {showPassword ? <EyeOff /> : <Eye />}
                                    </button>
                                </div>

                                <ul className={styles.passwordHints}>
                                    {PASSWORD_REQUIREMENTS.map((req) => {
                                        const valid = req.test(password);
                                        return (
                                            <li
                                                key={req.id}
                                                className={`${styles.passwordHint} ${valid ? styles.passwordHintValid : ""}`}
                                            >
                                                {valid ? <Check /> : <X />}
                                                {req.label}
                                            </li>
                                        );
                                    })}
                                </ul>
                            </div>

                            <div className={styles.field}>
                                <label className={styles.label} htmlFor="confirmPassword">
                                    Confirmer le mot de passe
                                </label>
                                <div className={styles.inputWrapper}>
                                    <Lock />
                                    <input
                                        id="confirmPassword"
                                        type={showPassword ? "text" : "password"}
                                        className={styles.input}
                                        placeholder="••••••••"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        autoComplete="new-password"
                                    />
                                </div>
                            </div>
                        </>
                    )}

                    {step === 2 && (
                        <>
                            <h2 className={styles.stepTitle}>Informations personnelles</h2>

                            <div className={styles.fieldRow}>
                                <div className={styles.field}>
                                    <label className={styles.label} htmlFor="firstName">
                                        Prénom
                                    </label>
                                    <div className={styles.inputWrapper}>
                                        <User />
                                        <input
                                            id="firstName"
                                            type="text"
                                            className={styles.input}
                                            placeholder="Jean"
                                            value={firstName}
                                            onChange={(e) => setFirstName(e.target.value)}
                                            autoComplete="given-name"
                                        />
                                    </div>
                                </div>

                                <div className={styles.field}>
                                    <label className={styles.label} htmlFor="lastName">
                                        Nom
                                    </label>
                                    <div className={styles.inputWrapper}>
                                        <User />
                                        <input
                                            id="lastName"
                                            type="text"
                                            className={styles.input}
                                            placeholder="Dupont"
                                            value={lastName}
                                            onChange={(e) => setLastName(e.target.value)}
                                            autoComplete="family-name"
                                        />
                                    </div>
                                </div>
                            </div>
                        </>
                    )}

                    {step === 3 && (
                        <>
                            <h2 className={styles.stepTitle}>Votre entreprise</h2>

                            <div className={styles.field}>
                                <label className={styles.label} htmlFor="business_name">
                                    Nom de l&apos;entreprise
                                </label>
                                <div className={styles.inputWrapper}>
                                    <Store />
                                    <input
                                        id="business_name"
                                        type="text"
                                        className={styles.input}
                                        placeholder="Entreprise Martin"
                                        value={business_name}
                                        onChange={(e) => setBusinessName(e.target.value)}
                                        autoComplete="organization"
                                    />
                                </div>
                            </div>

                            <div className={styles.field}>
                                <label className={styles.label} htmlFor="siren">
                                    Siren
                                </label>
                                <div className={styles.inputWrapper}>
                                    <Store />
                                    <input
                                        id="siren"
                                        type="text"
                                        inputMode="numeric"
                                        pattern="\d{9}"
                                        className={styles.input}
                                        placeholder="423855196"
                                        value={siren}
                                        onChange={(e) => setSiren(e.target.value.replace(/\D/g, "").slice(0, 9))}
                                        autoComplete="off"
                                        maxLength={9}
                                    />
                                </div>
                            </div>

                            <div className={styles.field}>
                                <label className={styles.label} htmlFor="address">
                                    Adresse
                                </label>
                                <div className={styles.autocompleteWrapper}>
                                    <div className={styles.inputWrapper}>
                                        <MapPin />
                                        <input
                                            id="address"
                                            type="text"
                                            className={styles.input}
                                            placeholder="12 rue de la Paix, 75002 Paris"
                                            value={address}
                                            onChange={(e) => handleAddressChange(e.target.value)}
                                            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                                            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                                            autoComplete="off"
                                        />
                                    </div>

                                    {showSuggestions && suggestions.length > 0 && (
                                        <ul className={styles.suggestions}>
                                            {suggestions.map((suggestion) => (
                                                <li
                                                    key={suggestion.label}
                                                    className={styles.suggestionItem}
                                                    onMouseDown={() => selectSuggestion(suggestion)}
                                                >
                                                    <MapPin />
                                                    {suggestion.label}
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </div>

                                {geocodeStatus === "loading" && (
                                    <p className={styles.geocodeStatus}>
                                        <Loader2 className={styles.spin} />
                                        Recherche d&apos;adresses...
                                    </p>
                                )}

                                {geocodeStatus === "success" && (
                                    <p className={`${styles.geocodeStatus} ${styles.geocodeStatusSuccess}`}>
                                        <Check />
                                        Adresse localisée
                                        {latitude !== null && longitude !== null && (
                                            <span>
                                                {" "}
                                                ({latitude.toFixed(4)}, {longitude.toFixed(4)})
                                            </span>
                                        )}
                                    </p>
                                )}

                                {geocodeStatus === "error" && (
                                    <p className={`${styles.geocodeStatus} ${styles.geocodeStatusError}`}>
                                        <AlertCircle />
                                        Aucune adresse trouvée, vérifiez la saisie.
                                    </p>
                                )}
                            </div>

                            <div className={styles.field}>
                                <label className={styles.label} htmlFor="businessPurpose">
                                    Activité de l&apos;entreprise
                                </label>
                                <div className={`${styles.inputWrapper} ${styles.inputWrapperTop}`}>
                                    <FileText />
                                    <textarea
                                        id="businessPurpose"
                                        className={`${styles.input} ${styles.textarea}`}
                                        placeholder="Décrivez brièvement l'activité de votre entreprise"
                                        value={businessPurpose}
                                        onChange={(e) => setBusinessPurpose(e.target.value)}
                                    />
                                </div>
                            </div>
                        </>
                    )}

                    {error && <p className={styles.error}>{error}</p>}

                    {step === 1 && (
                        <button type="button" className={styles.submit} onClick={goNext}>
                            Continuer
                        </button>
                    )}

                    {step > 1 && step < STEP_COUNT && (
                        <div className={styles.buttonsRow}>
                            <button type="button" className={styles.backButton} onClick={goBack}>
                                Retour
                            </button>
                            <button type="button" className={styles.submit} onClick={goNext}>
                                Continuer
                            </button>
                        </div>
                    )}

                    {step === STEP_COUNT && (
                        <div className={styles.buttonsRow}>
                            <button type="button" className={styles.backButton} onClick={goBack}>
                                Retour
                            </button>
                            <button type="submit" className={styles.submit} disabled={loading}>
                                {loading ? "Création..." : "Créer mon compte"}
                            </button>
                        </div>
                    )}
                </form>

                <p className={styles.switch}>
                    Déjà un compte ? <Link href="/login">Se connecter</Link>
                </p>
            </div>
        </div>
    );
}
