"use client";

import { useEffect, useState, useCallback } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { InputField } from "@/components/input-field";
import { useToast } from "@/context/toast-context";
import { apiGet, apiPost } from "@/lib/api-client";
import type { FamilyGroup, GroupMembership, GroupMember } from "@/types";

// Shared button style helpers
const btnPrimary: React.CSSProperties = {
  background: "var(--color-walnut)",
  color: "var(--color-cream)",
};
const btnOutline: React.CSSProperties = {
  background: "transparent",
  border: "1px solid var(--color-border)",
  color: "var(--color-ink-soft)",
};

export default function GroupsPage() {
  const { showToast } = useToast();

  const [groups, setGroups] = useState<FamilyGroup[]>([]);
  const [invitations, setInvitations] = useState<GroupMembership[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [creatingGroup, setCreatingGroup] = useState(false);
  const [expandedGroupId, setExpandedGroupId] = useState<string | null>(null);
  const [members, setMembers] = useState<Record<string, GroupMember[]>>({});
  const [inviteEmail, setInviteEmail] = useState<Record<string, string>>({});
  const [invitingGroupId, setInvitingGroupId] = useState<string | null>(null);
  const [showInviteForm, setShowInviteForm] = useState<string | null>(null);

  const fetchGroups = useCallback(async () => {
    setLoading(true);
    try {
      const [groupsData, invitationsData] = await Promise.all([
        apiGet<FamilyGroup[]>("/groups"),
        apiGet<GroupMembership[]>("/groups/invitations"),
      ]);
      setGroups(groupsData);
      setInvitations(invitationsData);
    } catch {
      setGroups([]);
      setInvitations([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  const fetchMembers = useCallback(async (groupId: string) => {
    try {
      const data = await apiGet<GroupMember[]>(`/groups/${groupId}/members`);
      setMembers((prev) => ({ ...prev, [groupId]: data }));
    } catch {
      setMembers((prev) => ({ ...prev, [groupId]: [] }));
    }
  }, []);

  const handleToggleGroup = (groupId: string) => {
    if (expandedGroupId === groupId) {
      setExpandedGroupId(null);
    } else {
      setExpandedGroupId(groupId);
      if (!members[groupId]) fetchMembers(groupId);
    }
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;

    setCreatingGroup(true);
    try {
      const group = await apiPost<FamilyGroup>("/groups", {
        name: newGroupName.trim(),
      });
      setGroups((prev) => [group, ...prev]);
      setNewGroupName("");
      setShowCreateForm(false);
      showToast("Grupo creado", "success");
    } catch {
      // handled by api-client
    } finally {
      setCreatingGroup(false);
    }
  };

  const handleInviteMember = async (groupId: string) => {
    const email = inviteEmail[groupId]?.trim();
    if (!email) return;

    setInvitingGroupId(groupId);
    try {
      await apiPost(`/groups/${groupId}/invitations`, { email });
      setInviteEmail((prev) => ({ ...prev, [groupId]: "" }));
      setShowInviteForm(null);
      showToast("Invitación enviada", "success");
    } catch {
      // handled by api-client
    } finally {
      setInvitingGroupId(null);
    }
  };

  const handleAcceptInvitation = async (invitation: GroupMembership) => {
    try {
      await apiPost(
        `/groups/${invitation.group_id}/invitations/${invitation.id}/accept`
      );
      setInvitations((prev) => prev.filter((inv) => inv.id !== invitation.id));
      showToast("Invitación aceptada", "success");
      fetchGroups();
    } catch {
      // handled by api-client
    }
  };

  const handleDeclineInvitation = async (invitation: GroupMembership) => {
    try {
      await apiPost(`/groups/invitations/${invitation.id}/decline`);
      setInvitations((prev) => prev.filter((inv) => inv.id !== invitation.id));
    } catch {
      // handled by api-client
    }
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString("es-ES", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });

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
              Mis Grupos
            </h1>
            <button
              type="button"
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
              style={btnPrimary}
              onMouseEnter={(e) =>
                ((e.currentTarget as HTMLButtonElement).style.background =
                  "var(--color-mahogany)")
              }
              onMouseLeave={(e) =>
                ((e.currentTarget as HTMLButtonElement).style.background =
                  "var(--color-walnut)")
              }
            >
              Crear grupo
            </button>
          </div>

          {/* Create Group Form */}
          {showCreateForm && (
            <form
              onSubmit={handleCreateGroup}
              className="mb-6 rounded-lg p-5 space-y-4"
              style={{
                background: "var(--color-cream)",
                border: "1px solid var(--color-border)",
                boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
              }}
            >
              <InputField
                label="Nombre del grupo"
                name="group-name"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
                placeholder="Ej: Familia García"
                required
              />
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={creatingGroup || !newGroupName.trim()}
                  className="rounded-full px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  style={btnPrimary}
                  onMouseEnter={(e) => {
                    if (!creatingGroup)
                      (e.currentTarget as HTMLButtonElement).style.background =
                        "var(--color-mahogany)";
                  }}
                  onMouseLeave={(e) => {
                    if (!creatingGroup)
                      (e.currentTarget as HTMLButtonElement).style.background =
                        "var(--color-walnut)";
                  }}
                >
                  {creatingGroup ? "Creando..." : "Crear"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewGroupName("");
                  }}
                  className="rounded-full px-4 py-2 text-sm font-medium transition-colors"
                  style={btnOutline}
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
              </div>
            </form>
          )}

          {/* Pending Invitations */}
          {!loading && invitations.length > 0 && (
            <section className="mb-8">
              <h2
                className="text-base font-semibold mb-3"
                style={{ color: "var(--color-walnut)" }}
              >
                Invitaciones pendientes
              </h2>
              <div className="space-y-3">
                {invitations.map((invitation) => (
                  <div
                    key={invitation.id}
                    className="rounded-lg px-5 py-4"
                    style={{
                      background: "#FDF6E3",
                      border: "1px solid var(--color-brass)",
                      boxShadow: "0 1px 3px rgba(28,16,8,0.06)",
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p
                          className="text-sm font-medium"
                          style={{ color: "var(--color-walnut)" }}
                        >
                          Invitación al grupo
                          {invitation.group_name
                            ? `: ${invitation.group_name}`
                            : ""}
                        </p>
                        <p
                          className="text-xs mt-0.5"
                          style={{ color: "var(--color-ink-faint)" }}
                        >
                          {formatDate(invitation.created_at)}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => handleAcceptInvitation(invitation)}
                          className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors"
                          style={{
                            background: "var(--color-reading)",
                            color: "var(--color-cream)",
                          }}
                        >
                          Aceptar
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeclineInvitation(invitation)}
                          className="rounded-full px-3 py-1.5 text-xs font-medium transition-colors"
                          style={btnOutline}
                          onMouseEnter={(e) =>
                            ((e.currentTarget as HTMLButtonElement).style.background =
                              "var(--color-parchment)")
                          }
                          onMouseLeave={(e) =>
                            ((e.currentTarget as HTMLButtonElement).style.background =
                              "transparent")
                          }
                        >
                          Rechazar
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Loading */}
          {loading && <Skeleton variant="list" count={4} />}

          {/* Empty */}
          {!loading && groups.length === 0 && invitations.length === 0 && (
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
                No perteneces a ningún grupo aún.
              </p>
              <p className="text-sm" style={{ color: "var(--color-ink-faint)" }}>
                Crea un grupo familiar para compartir tu biblioteca con otros
                miembros.
              </p>
            </div>
          )}

          {/* Groups List */}
          {!loading && groups.length > 0 && (
            <div className="space-y-3">
              {groups.map((group) => (
                <div
                  key={group.id}
                  className="rounded-lg overflow-hidden"
                  style={{
                    background: "var(--color-cream)",
                    border: "1px solid var(--color-border)",
                    boxShadow: "0 1px 3px rgba(28,16,8,0.08)",
                  }}
                >
                  {/* Group Header */}
                  <button
                    type="button"
                    onClick={() => handleToggleGroup(group.id)}
                    className="w-full px-5 py-4 flex items-center justify-between text-left transition-colors"
                    style={{
                      background:
                        expandedGroupId === group.id
                          ? "var(--color-parchment)"
                          : "transparent",
                    }}
                    onMouseEnter={(e) => {
                      if (expandedGroupId !== group.id)
                        (e.currentTarget as HTMLButtonElement).style.background =
                          "var(--color-parchment)";
                    }}
                    onMouseLeave={(e) => {
                      if (expandedGroupId !== group.id)
                        (e.currentTarget as HTMLButtonElement).style.background =
                          "transparent";
                    }}
                  >
                    <div>
                      <h3
                        className="text-base font-semibold"
                        style={{ color: "var(--color-walnut)" }}
                      >
                        {group.name}
                      </h3>
                      <p
                        className="text-xs mt-0.5"
                        style={{ color: "var(--color-ink-faint)" }}
                      >
                        Creado el {formatDate(group.created_at)}
                      </p>
                    </div>
                    <span
                      className="transition-transform"
                      style={{
                        color: "var(--color-ink-faint)",
                        transform:
                          expandedGroupId === group.id
                            ? "rotate(180deg)"
                            : "rotate(0deg)",
                        display: "inline-block",
                      }}
                      aria-hidden="true"
                    >
                      ▼
                    </span>
                  </button>

                  {/* Expanded Content */}
                  {expandedGroupId === group.id && (
                    <div
                      className="px-5 py-4"
                      style={{ borderTop: "1px solid var(--color-border)" }}
                    >
                      {/* Members List */}
                      <div className="mb-4">
                        <h4
                          className="text-sm font-medium mb-2"
                          style={{ color: "var(--color-ink-soft)" }}
                        >
                          Miembros
                        </h4>
                        {!members[group.id] ? (
                          <Skeleton variant="text" count={2} />
                        ) : members[group.id].length === 0 ? (
                          <p
                            className="text-sm"
                            style={{ color: "var(--color-ink-faint)" }}
                          >
                            Sin miembros adicionales.
                          </p>
                        ) : (
                          <ul className="space-y-1">
                            {members[group.id].map((member) => (
                              <li
                                key={member.user_id}
                                className="flex items-center gap-2 text-sm"
                                style={{ color: "var(--color-ink-soft)" }}
                              >
                                <span
                                  className="inline-block h-2 w-2 rounded-full"
                                  style={{ background: "var(--color-reading)" }}
                                />
                                <span>{member.name}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>

                      {/* Invite Member */}
                      {showInviteForm === group.id ? (
                        <div className="flex gap-2 items-end">
                          <div className="flex-1">
                            <InputField
                              label="Email del invitado"
                              name={`invite-email-${group.id}`}
                              type="email"
                              value={inviteEmail[group.id] || ""}
                              onChange={(e) =>
                                setInviteEmail((prev) => ({
                                  ...prev,
                                  [group.id]: e.target.value,
                                }))
                              }
                              placeholder="correo@ejemplo.com"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={() => handleInviteMember(group.id)}
                            disabled={
                              invitingGroupId === group.id ||
                              !inviteEmail[group.id]?.trim()
                            }
                            className="rounded-full px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            style={btnPrimary}
                            onMouseEnter={(e) => {
                              if (invitingGroupId !== group.id)
                                (e.currentTarget as HTMLButtonElement).style.background =
                                  "var(--color-mahogany)";
                            }}
                            onMouseLeave={(e) => {
                              if (invitingGroupId !== group.id)
                                (e.currentTarget as HTMLButtonElement).style.background =
                                  "var(--color-walnut)";
                            }}
                          >
                            {invitingGroupId === group.id
                              ? "Enviando..."
                              : "Enviar"}
                          </button>
                          <button
                            type="button"
                            onClick={() => setShowInviteForm(null)}
                            className="rounded-full px-3 py-2 text-sm font-medium transition-colors"
                            style={btnOutline}
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
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setShowInviteForm(group.id)}
                          className="text-sm font-medium transition-colors"
                          style={{ color: "var(--color-teak)" }}
                          onMouseEnter={(e) =>
                            ((e.currentTarget as HTMLButtonElement).style.color =
                              "var(--color-mahogany)")
                          }
                          onMouseLeave={(e) =>
                            ((e.currentTarget as HTMLButtonElement).style.color =
                              "var(--color-teak)")
                          }
                        >
                          + Invitar miembro
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
