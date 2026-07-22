# Use Cases — EntreLíneas (Application Layer)

## Identity & Privacy
- `RegisterUser` (requires `AcceptDataConsent` prior or in the same flow)
- `LoginUser` (issues Access Token + Refresh Token; see `adr/0004`)
- `RefreshToken` (rotates Refresh Token, issues new Access Token)
- `RevokeToken` (invalidates Refresh Token)
- `CreateFamilyGroup`
- `InviteGroupMember` / `AcceptGroupInvitation`
- `ExerciseARCORight` (access / rectification / cancellation / opposition / portability)
- `NotifySecurityBreach` (internal, triggers 72h playbook)

## Library
- `CreateBook` (intellectual work metadata)
- `CreatePhysicalCopy`
- `CreateDigitalCopy` (includes encryption and file isolation)
- `EditBook` / `DeleteBook`
- `EditCopy` / `DeleteCopy`
- `SearchBooks` (search within personal and group library — metadata only)
- `ImportBookMetadata` (autocomplete via public source: Open Library, Google Books)
- `OpenReader` (validate ownership, serve encrypted file to authenticated owner)
- `SaveReadingProgress`
- `CreateBookmark` / `DeleteBookmark`
- `CreateNote` / `EditNote` / `DeleteNote`

## Reading Selection
- `RunReadingDraw` (validates availability for all participants; see `adr/0008`)
- `PickByTurn` (alternative rotational selection mode among members)

## Community
- `CreateClub` (only within a family group in MVP; see `adr/0006`)
- `SetActiveBook`
- `ActivateReadingTurn` (validates own copy ownership)
- `PostComment`

## Circulation
- `RegisterLoan` (physical copy only)
- `RegisterReturn`

## Reviews
- `CreateReview` (with `visibility`: private | shared, and explicit `shared_with`; see `adr/0007`)
- `EditReview` / `DeleteReview`
