export default function PrivacyPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-3xl rounded-lg bg-white p-8 shadow-md">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Política de Privacidad — EntreLíneas
        </h1>

        <div className="prose prose-sm text-gray-700 space-y-4">
          <p>
            EntreLíneas se compromete a proteger tus datos personales conforme a
            la Ley 21.719 sobre Protección de Datos Personales de Chile.
          </p>

          <h2 className="text-lg font-semibold text-gray-900 mt-6">
            1. Datos que recopilamos
          </h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>Nombre y correo electrónico (para autenticación)</li>
            <li>Libros y copias que registras (para gestión de biblioteca)</li>
            <li>Reseñas que escribes (con visibilidad que tú controlas)</li>
            <li>Membresías de grupos familiares</li>
          </ul>

          <h2 className="text-lg font-semibold text-gray-900 mt-6">
            2. Finalidad del tratamiento
          </h2>
          <p>
            Tus datos se utilizan exclusivamente para proveer la funcionalidad
            de la plataforma: gestión de biblioteca personal, préstamos entre
            miembros de tu grupo, y participación en clubes de lectura.
          </p>

          <h2 className="text-lg font-semibold text-gray-900 mt-6">
            3. Tus derechos ARCO
          </h2>
          <p>Tienes derecho a:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Acceso:</strong> Exportar todos tus datos en cualquier momento</li>
            <li><strong>Rectificación:</strong> Corregir tu nombre o email</li>
            <li><strong>Cancelación:</strong> Eliminar tu cuenta y todos tus datos</li>
            <li><strong>Oposición:</strong> Oponerte a tratamientos no esenciales</li>
          </ul>
          <p>
            Puedes ejercer estos derechos desde la sección de Configuración de tu
            cuenta.
          </p>

          <h2 className="text-lg font-semibold text-gray-900 mt-6">
            4. Compartición de datos
          </h2>
          <p>
            Ningún dato es público. Toda compartición es explícita: solo se
            comparte con el grupo o club que tú elijas. No vendemos ni
            transferimos datos a terceros.
          </p>

          <h2 className="text-lg font-semibold text-gray-900 mt-6">
            5. Retención
          </h2>
          <p>
            Tus datos se conservan mientras tu cuenta esté activa. Al eliminar tu
            cuenta, todos los datos personales son borrados permanentemente,
            incluyendo archivos digitales.
          </p>

          <h2 className="text-lg font-semibold text-gray-900 mt-6">
            6. Contacto
          </h2>
          <p>
            Para consultas sobre privacidad: dpo@entrelineas.cl
          </p>

          <p className="mt-8 text-xs text-gray-400">
            Última actualización: Julio 2026 · Versión 1.0
          </p>
        </div>
      </div>
    </div>
  );
}
