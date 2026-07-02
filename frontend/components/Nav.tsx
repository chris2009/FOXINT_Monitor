import Link from "next/link";

const links = [
  { href: "/", label: "Páginas" },
  { href: "/rules", label: "Reglas" },
  { href: "/alerts", label: "Alertas" },
];

export function Nav() {
  return (
    <nav className="border-b px-6 py-3 flex items-center gap-6">
      <span className="font-semibold">OSINT Monitor</span>
      {links.map((link) => (
        <Link key={link.href} href={link.href} className="text-sm text-gray-600 hover:text-black">
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
