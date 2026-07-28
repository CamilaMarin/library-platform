export default function PrivacyPage() {
  return (
    <div
      className="flex min-h-screen items-center justify-center px-4 py-8"
      style={{ background: "var(--color-parchment)" }}
    >
      <div
        className="w-full max-w-3xl rounded-xl p-8"
        style={{
          background: "var(--color-cream)",
          border: "1px solid var(--color-border)",
          boxShadow: "0 4px 24px -4px rgba(28, 16, 8, 0.14)",
        }}
      >
        <h1
          className="text-2xl font-bold mb-6"
          style={{
            fontFamily: "var(--font-playfair), Georgia, serif",
            color: "var(--color-walnut)",
          }}
        >
          Política de Privacidad — EntreLíneas
        </h1>

        <div className="space-y-4 text-sm" style={{ color: "var(--color-ink-soft)" }}>
          <p>
            EntreLíneas se compromete a proteger tus datos personales conforme a
            la Ley 21.719 sobre Protección de Datos Personales de Chile.
          </p>

          <h2
            className="text-base font-semibold mt-6"
            style={{ color: "var(--color-walnut)" }}
          >
            1. Datos que recopilamos
          </h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>Nombre y correo electrónico (para autenticación)</li>
            <li>Libros y copias que registras (para gestión de biblioteca)</li>
            <li>Reseñas que escribes (con visibilidad que tú controlas)</li>
            <li>Membresías de grupos familiares</li>
          </ul>

          <h2
            className="text-base font-semibold mt-6"
            style={{ color: "var(--color-walnut)" }}
          >
            2. Finalidad del tratamiento
          </h2>
          <p>
            Tus datos se utilizan exclusivamente para proveer la funcionalidad
            de la plataforma: gestión de biblioteca personal, préstamos entre
            miembros de tu grupo, y participación en clubes de lectura.
          </p>

          <h2
            className="text-base font-semibold mt-6"
            style={{ color: "var(--color-walnut)" }}
          >
            3. Tus derechos ARCO
          </h2>
          <p>Tienes derecho a:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>
              <strong style={{ color: "var(--color-ink)" }}>Acceso:</strong>{" "}
              Exportar todos tus datos en cualquier momento
            </li>
            <li>
              <strong style={{ color: "var(--color-ink)" }}>
                Rectificación:
              </strong>{" "}
              Corregir tu nombre o email
            </li>
            <li>
              <strong style={{ color: "var(--color-ink)" }}>
                Cancelación:
              </strong>{" "}
              Eliminar tu cuenta y todos tus datos
            </li>
            <li>
              <strong style={{ color: "var(--color-ink)" }}>Oposición:</strong>{" "}
              Oponerte a tratamientos no esenciales
            </li>
          </ul>
          <p>
            Puedes ejercer estos derechos desde la sección de Configuración de
            tu cuenta.
          </p>

          <h2
            className="text-base font-semibold mt-6"
            style={{ color: "var(--color-walnut)" }}
          >
            4. Compartición de datos
          </h2>
          <p>
            Ningún dato es público. Toda compartición es explícita: solo se
            comparte con el grupo o club que tú elijas. No vendemos ni
            transferimos datos a terceros.
          </p>

          <h2
            className="text-base font-semibold mt-6"
            style={{ color: "var(--color-walnut)" }}
          >
            5. Retención
          </h2>
          <p>
            Tus datos se conservan mientras tu cuenta esté activa. Al eliminar
            tu cuenta, todos los datos personales son borrados permanentemente,
            incluyendo archivos digitales.
          </p>

          <h2
            className="text-base font-semibold mt-6"
            style={{ color: "var(--color-walnut)" }}
          >
            6. Contacto
          </h2>
          <p>Para consultas sobre privacidad: dpo@entrelineas.cl</p>

          <p
            className="mt-8 text-xs"
            style={{ color: "var(--color-ink-faint)" }}
          >
            Última actualización: Julio 2026 · Versión 1.0
          </p>
        </div>
      </div>
    </div>
  );
}
