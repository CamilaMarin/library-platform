"use client";

import { useEffect, useState, useCallback } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { Navigation } from "@/components/navigation";
import { Skeleton } from "@/components/skeleton";
import { InputField } from "@/components/input-field";
import { useToast } from "@/context/toast-context";
import { apiGet, apiPost } from "@/lib/api-client";
import type { FamilyGroup, GroupMembership, GroupMember } from "@/types";

export default function GroupsPage() {
  const { showToast } = useToast();

  // State
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

  // Fetch groups and invitations
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

  // Fetch members for a group
  const fetchMembers = useCallback(async (groupId: string) => {
    try {
      const data = await apiGet<GroupMember[]>(
        `/groups/${groupId}/members`
      );
      setMembers((prev) => ({ ...prev, [groupId]: data }));
    } catch {
      setMembers((prev) => ({ ...prev, [groupId]: [] }));
    }
  }, []);

  // Toggle expand group
  const handleToggleGroup = (groupId: string) => {
    if (expandedGroupId === groupId) {
      setExpandedGroupId(null);
    } else {
      setExpandedGroupId(groupId);
      if (!members[groupId]) {
        fetchMembers(groupId);
      }
    }
  };

  // Create group
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
      // Error handled by api-client toast handler
    } finally {
      setCreatingGroup(false);
    }
  };

  // Invite member
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
      // Error handled by api-client toast handler
    } finally {
      setInvitingGroupId(null);
    }
  };

  // Accept invitation
  const handleAcceptInvitation = async (invitation: GroupMembership) => {
    try {
      await apiPost(`/groups/${invitation.group_id}/invitations/${invitation.id}/accept`);
      setInvitations((prev) =>
        prev.filter((inv) => inv.id !== invitation.id)
      );
      showToast("Invitación aceptada", "success");
      fetchGroups();
    } catch {
      // Error handled by api-client toast handler
    }
  };

  // Decline invitation
  const handleDeclineInvitation = async (invitation: GroupMembership) => {
    try {
      await apiPost(`/groups/invitations/${invitation.id}/decline`);
      setInvitations((prev) =>
        prev.filter((inv) => inv.id !== invitation.id)
      );
    } catch {
      // Error handled by api-client toast handler
    }
  };

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("es-ES", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <ProtectedRoute>
      <Navigation />
      <main className="md:ml-64 pb-20 md:pb-0 min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Mis Grupos</h1>
            <button
              type="button"
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              Crear grupo
            </button>
          </div>

          {/* Create Group Form */}
          {showCreateForm && (
            <form
              onSubmit={handleCreateGroup}
              className="mb-6 rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
            >
              <InputField
                label="Nombre del grupo"
                name="group-name"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
                placeholder="Ej: Familia García"
                required
              />
              <div className="mt-4 flex gap-3">
                <button
                  type="submit"
                  disabled={creatingGroup || !newGroupName.trim()}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {creatingGroup ? "Creando..." : "Crear"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewGroupName("");
                  }}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          )}

          {/* Pending Invitations */}
          {!loading && invitations.length > 0 && (
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                Invitaciones pendientes
              </h2>
              <div className="space-y-3">
                {invitations.map((invitation) => (
                  <div
                    key={invitation.id}
                    className="rounded-lg border border-yellow-200 bg-yellow-50 px-5 py-4 shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          Invitación al grupo{invitation.group_name ? `: ${invitation.group_name}` : ""}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {formatDate(invitation.created_at)}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => handleAcceptInvitation(invitation)}
                          className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 transition-colors"
                        >
                          Aceptar
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeclineInvitation(invitation)}
                          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
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

          {/* Loading State */}
          {loading && <Skeleton variant="list" count={4} />}

          {/* Empty State */}
          {!loading && groups.length === 0 && invitations.length === 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
              <p className="text-lg font-medium text-gray-900 mb-2">
                No perteneces a ningún grupo aún.
              </p>
              <p className="text-sm text-gray-500">
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
                  className="rounded-lg border border-gray-200 bg-white shadow-sm"
                >
                  {/* Group Header */}
                  <button
                    type="button"
                    onClick={() => handleToggleGroup(group.id)}
                    className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors rounded-lg"
                  >
                    <div>
                      <h3 className="text-base font-semibold text-gray-900">
                        {group.name}
                      </h3>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Creado el {formatDate(group.created_at)}
                      </p>
                    </div>
                    <span
                      className={`text-gray-400 transition-transform ${
                        expandedGroupId === group.id ? "rotate-180" : ""
                      }`}
                      aria-hidden="true"
                    >
                      ▼
                    </span>
                  </button>

                  {/* Expanded Content */}
                  {expandedGroupId === group.id && (
                    <div className="border-t border-gray-100 px-5 py-4">
                      {/* Members List */}
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">
                          Miembros
                        </h4>
                        {!members[group.id] ? (
                          <Skeleton variant="text" count={2} />
                        ) : members[group.id].length === 0 ? (
                          <p className="text-sm text-gray-500">
                            Sin miembros adicionales.
                          </p>
                        ) : (
                          <ul className="space-y-1">
                            {members[group.id].map((member) => (
                              <li
                                key={member.user_id}
                                className="flex items-center gap-2 text-sm text-gray-700"
                              >
                                <span
                                  className="inline-block h-2 w-2 rounded-full bg-green-500"
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
                            className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {invitingGroupId === group.id
                              ? "Enviando..."
                              : "Enviar"}
                          </button>
                          <button
                            type="button"
                            onClick={() => setShowInviteForm(null)}
                            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                          >
                            Cancelar
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setShowInviteForm(group.id)}
                          className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
                        >
                          Invitar miembro
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
