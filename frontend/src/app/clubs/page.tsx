"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { InputField } from "@/components/input-field";
import { SelectField } from "@/components/select-field";
import { useToast } from "@/context/toast-context";
import { apiGet, apiPost, ApiError } from "@/lib/api-client";
import type { FamilyGroup } from "@/types";

interface Club {
  id: string;
  name: string;
  description: string | null;
  group_id: string;
  created_at: string;
}

export default function ClubsPage() {
  const [clubs, setClubs] = useState<Club[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [nameError, setNameError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [groups, setGroups] = useState<FamilyGroup[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const { showToast } = useToast();

  useEffect(() => {
    async function fetchData() {
      try {
        const [clubsData, groupsData] = await Promise.all([
          apiGet<Club[]>("/clubs"),
          apiGet<FamilyGroup[]>("/groups"),
        ]);
        setClubs(clubsData);
        setGroups(groupsData);
        if (groupsData.length === 1) {
          setSelectedGroupId(groupsData[0].id);
        }
      } catch {
        setClubs([]);
        setGroups([]);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setNameError("El nombre es obligatorio");
      return;
    }

    if (groups.length > 1 && !selectedGroupId) {
      setNameError("Debes seleccionar un grupo familiar");
      return;
    }

    setSubmitting(true);
    setNameError("");

    try {
      const body: Record<string, string> = { name: name.trim() };
      if (description.trim()) body.description = description.trim();
      if (selectedGroupId) body.group_id = selectedGroupId;

      const newClub = await apiPost<Club>("/clubs", body);
      setClubs((prev) => [newClub, ...prev]);
      setName("");
      setDescription("");
      setShowForm(false);
      showToast("Club creado", "success");
      setSelectedGroupId(groups.length === 1 ? groups[0].id : "");
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          typeof err.detail === "string"
            ? err.detail
            : (err.detail as Record<string, string>).detail ||
              JSON.stringify(err.detail);
        if (detail === "user_has_no_group") {
          setNameError("Debes pertenecer a un grupo familiar para crear un club.");
        } else if (detail === "not_member_of_group") {
          setNameError("No eres miembro del grupo seleccionado.");
        } else {
          setNameError(detail);
        }
      } else {
        showToast("Error al crear el club", "error");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ProtectedRoute>
      <Navigation />
      <main
        className="md:ml-64 pb-20 md:pb-0 min-h-screen"
        style={{ background: "var(--color-parchment)" }}
      >
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h1
              className="text-2xl font-bold"
              style={{
                fontFamily: "var(--font-playfair), Georgia, serif",
                color: "var(--color-walnut)",
              }}
            >
              Mis Clubes
            </h1>
            <button
              type="button"
              onClick={() => setShowForm((prev) => !prev)}
              className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
              style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
              onMouseEnter={(e) =>
                ((e.currentTarget as HTMLButtonElement).style.background =
                  "var(--color-mahogany)")
              }
              onMouseLeave={(e) =>
                ((e.currentTarget as HTMLButtonElement).style.background =
                  "var(--color-walnut)")
              }
            >
              {showForm ? "Cancelar" : "Crear club"}
            </button>
          </div>

          {/* Create Club Form */}
          {showForm && (
            <form
              onSubmit={handleSubmit}
              className="mb-6 rounded-lg p-5 space-y-4"
              style={{
                background: "var(--color-cream)",
                border: "1px solid var(--color-border)",
                boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
              }}
            >
              <h2
                className="text-lg font-semibold"
                style={{
                  fontFamily: "var(--font-playfair), Georgia, serif",
                  color: "var(--color-walnut)",
                }}
              >
                Nuevo club
              </h2>

              <InputField
                label="Nombre"
                name="club-name"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (nameError) setNameError("");
                }}
                error={nameError}
                required
                placeholder="Nombre del club"
              />

              <div className="flex flex-col gap-1">
                <label
                  htmlFor="input-club-description"
                  className="text-sm font-medium"
                  style={{ color: "var(--color-ink-soft)" }}
                >
                  Descripción
                </label>
                <textarea
                  id="input-club-description"
                  name="club-description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Descripción del club (opcional)"
                  rows={3}
                  className="rounded-md border px-3 py-2 text-sm transition-colors focus:outline-none"
                  style={{
                    borderColor: "var(--color-border)",
                    background: "var(--color-cream)",
                    color: "var(--color-ink)",
                  }}
                />
              </div>

              {groups.length > 1 && (
                <SelectField
                  label="Grupo familiar"
                  name="club-group"
                  options={groups.map((g) => ({ value: g.id, label: g.name }))}
                  value={selectedGroupId}
                  onChange={(e) => setSelectedGroupId(e.target.value)}
                  required
                  placeholder="Selecciona un grupo"
                />
              )}

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setName("");
                    setDescription("");
                    setNameError("");
                    setSelectedGroupId(groups.length === 1 ? groups[0].id : "");
                  }}
                  className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
                  style={{
                    border: "1px solid var(--color-border)",
                    color: "var(--color-ink-soft)",
                    background: "transparent",
                  }}
                  onMouseEnter={(e) =>
                    ((e.currentTarget as HTMLButtonElement).style.background =
                      "var(--color-parchment)")
                  }
                  onMouseLeave={(e) =>
                    ((e.currentTarget as HTMLButtonElement).style.background =
                      "transparent")
                  }
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-full px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ background: "var(--color-walnut)", color: "var(--color-cream)" }}
                  onMouseEnter={(e) => {
                    if (!submitting)
                      (e.currentTarget as HTMLButtonElement).style.background =
                        "var(--color-mahogany)";
                  }}
                  onMouseLeave={(e) => {
                    if (!submitting)
                      (e.currentTarget as HTMLButtonElement).style.background =
                        "var(--color-walnut)";
                  }}
                >
                  {submitting ? "Creando..." : "Crear club"}
                </button>
              </div>
            </form>
          )}

          {loading && <Skeleton variant="card" count={3} />}

          {!loading && clubs.length === 0 && (
            <div
              className="rounded-lg p-8 text-center"
              style={{
                background: "var(--color-cream)",
                border: "1px solid var(--color-border)",
              }}
            >
              <p
                className="text-base font-medium mb-2"
                style={{ color: "var(--color-walnut)" }}
              >
                No perteneces a ningún club aún
              </p>
              <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
                Crea uno para comenzar.
              </p>
            </div>
          )}

          {!loading && clubs.length > 0 && (
            <div className="space-y-3">
              {clubs.map((club) => (
                <Link
                  key={club.id}
                  href={`/clubs/${club.id}`}
                  className="block rounded-lg px-5 py-4 transition-all"
                  style={{
                    background: "var(--color-cream)",
                    border: "1px solid var(--color-border)",
                    boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLAnchorElement).style.boxShadow =
                      "0 4px 12px -2px rgba(28,16,8,0.16)";
                    (e.currentTarget as HTMLAnchorElement).style.borderColor =
                      "var(--color-teak)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLAnchorElement).style.boxShadow =
                      "0 1px 3px rgba(28,16,8,0.08)";
                    (e.currentTarget as HTMLAnchorElement).style.borderColor =
                      "var(--color-border)";
                  }}
                >
                  <h2
                    className="text-base font-semibold"
                    style={{
                      fontFamily: "var(--font-playfair), Georgia, serif",
                      color: "var(--color-walnut)",
                    }}
                  >
                    {club.name}
                  </h2>
                  {club.description && (
                    <p
                      className="text-sm mt-1"
                      style={{ color: "var(--color-ink-faint)" }}
                    >
                      {club.description}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
