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
        // Auto-select if only one group
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
      if (description.trim()) {
        body.description = description.trim();
      }
      if (selectedGroupId) {
        body.group_id = selectedGroupId;
      }

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
            : (err.detail as Record<string, string>).detail || JSON.stringify(err.detail);
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
      <main className="md:ml-64 pb-20 md:pb-0 min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Mis Clubes</h1>
            <button
              type="button"
              onClick={() => setShowForm((prev) => !prev)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              {showForm ? "Cancelar" : "Crear club"}
            </button>
          </div>

          {/* Create Club Form */}
          {showForm && (
            <form
              onSubmit={handleSubmit}
              className="mb-6 rounded-lg border border-gray-200 bg-white p-5 shadow-sm space-y-4"
            >
              <h2 className="text-lg font-semibold text-gray-900">
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
                  className="text-sm font-medium text-gray-700"
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
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {submitting ? "Creando..." : "Crear club"}
                </button>
              </div>
            </form>
          )}

          {/* Loading State */}
          {loading && <Skeleton variant="card" count={3} />}

          {/* Empty State */}
          {!loading && clubs.length === 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
              <p className="text-lg font-medium text-gray-900 mb-2">
                No perteneces a ningún club aún
              </p>
              <p className="text-sm text-gray-500">
                Crea uno para comenzar.
              </p>
            </div>
          )}

          {/* Clubs List */}
          {!loading && clubs.length > 0 && (
            <div className="space-y-3">
              {clubs.map((club) => (
                <Link
                  key={club.id}
                  href={`/clubs/${club.id}`}
                  className="block rounded-lg border border-gray-200 bg-white px-5 py-4 shadow-sm hover:shadow-md transition-shadow"
                >
                  <h2 className="text-base font-semibold text-gray-900">
                    {club.name}
                  </h2>
                  {club.description && (
                    <p className="text-sm text-gray-500 mt-1">
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
