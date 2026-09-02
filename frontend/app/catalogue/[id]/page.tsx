import PartnerDetail from "./PartnerDetail";

export function generateStaticParams() {
    return [{ id: "1" }];
}

export default function Page() {
    return <PartnerDetail />;
}
