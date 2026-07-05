# 🔄 Host Migration Plan — Automatic New-Host Election

> **Goal:** when the host goes offline, the group must recover **automatically**:
> one (and only one) client becomes the new host, everyone else reconnects to it,
> and every user sees clear notifications about what happened.
>
> **Design principle:** *deterministic election* — every client independently
> computes the same answer to "who is the next host?" from data it already has,
> so no coordination messages (and no user dialogs) are needed.

---

## Current behavior (the problem)

When the host disconnects, `MyClient.receive_loop` fires
`on_connection_lost_callback`, and `MainApplication.on_connection_lost` shows
**every user** the same dialog: *"Connection lost — start a new server?"*

If several users click START SERVER, the network ends up with **multiple
competing servers** and the group splinters. Recovery must not depend on
humans racing each other.

---

## The election rule

1. The server assigns every client a **join order number** (1, 2, 3, …) and
   includes it in every `active_users` broadcast. The host itself is always #1.
2. Every client caches the latest user list, so at the moment of disconnect
   everyone holds the same snapshot, e.g.
   `[#1 rayhan (host), #2 fahim, #3 arif, #4 mira]`.
3. On disconnect, each client removes the dead host and looks at who is first:
   - **Fahim (#2)** → "that's me" → **auto-start the server** (no dialog).
   - **Everyone else** → wait, rediscover, reconnect.
4. **Staggered takeover timeouts** cover the case where the successor also left:
   - rank 2 acts at **T+0s**
   - rank 3 acts at **T+6s** *if no server has appeared yet*
   - rank 4 acts at **T+12s**, and so on (`(rank − 2) × 6s`)
5. **Double-server safety check:** immediately before auto-starting, a client
   runs one quick `discover_server_ip(2.0)` sweep. If a server is already up
   (someone beat it to it, or the old host came back), it **joins instead of
   starting**. This makes accidental duplicate servers self-healing.

Election needs **zero new messages** — it reuses the `active_users` broadcast
that already exists.

---

## Protocol changes (`services/schemas.py`)

### 1. `ActiveUsersPacket` carries ordered peer entries

```python
class PeerInfo(BaseModel):
    join_order: int          # 1 = current host, assigned by the server
    username: str
    ip: str                  # peer's LAN IP, reported in ConnectPacket

class ActiveUsersPacket(BaseModel):
    action: Literal["active_users"] = "active_users"
    users: List[PeerInfo] = []
```

Carrying `ip` lets survivors connect **directly** to the new host without
waiting a full discovery round (discovery remains the fallback).

### 2. `ConnectPacket` reports the client's own IP

```python
class ConnectPacket(BaseModel):
    action: Literal["connect"] = "connect"
    username: str
    ip: str = ""             # from get_lan_ip(); server falls back to socket peer address
```

### 3. New `HostGoodbyePacket` (graceful shutdown)

```python
class HostGoodbyePacket(BaseModel):
    action: Literal["host_goodbye"] = "host_goodbye"
    next_host_username: str  # who the departing host nominates (its rank-2 peer)
```

When the host quits *politely* (app closed normally), it broadcasts this first.
Clients then skip timeouts entirely: the nominee starts immediately, everyone
else reconnects after ~2s. Crashes still work — they just take the slower
timeout path.

> ⚠️ The sidebar UI code reads `packet.users` — it must be updated in the same
> commit to render `PeerInfo.username` instead of plain strings.

---

## Server changes (`services/websocket/server.py`)

- Keep a monotonically increasing `join_counter`; store
  `websocket -> PeerInfo` instead of `websocket -> username`.
- On `ConnectPacket`: assign `join_order = next counter value` (re-connects
  from the same user get a fresh number — simple and unambiguous). Record the
  IP from the packet, falling back to `websocket.remote_address[0]`.
- Broadcast the ordered list (sorted by `join_order`) in `ActiveUsersPacket`.
- New method `broadcast_host_goodbye()` — called by the app when the host
  quits gracefully; sends `HostGoodbyePacket` naming the rank-2 peer, then
  stops.

---

## Client changes (`services/websocket/client.py`)

- Cache the last seen roster: `self.last_active_users: List[PeerInfo]`
  (updated inside `receive_loop` before handing the packet to the UI).
- Track `self.my_username` so the client can find its own rank.
- Expose `self.pending_goodbye: Optional[HostGoodbyePacket]` — set when a
  goodbye arrives; `on_connection_lost` reads it to pick the fast path.

---

## App orchestration (`MainApplication.py`) — the migration engine

Replace `on_connection_lost` with a **migration coroutine**:

```
async def run_host_migration():
    1. Snapshot roster = client.last_active_users minus the dead host (#1)
    2. my_rank = my position in that list (1-based after removal)
    3. Notify UI: "Host disconnected — finding a new host…"  (snackbar)

    4. If a HostGoodbyePacket named ME  →  delay = 0
       elif goodbye named someone else →  delay = 2s (just reconnect wait)
       else (crash path)               →  delay = (my_rank − 1) × 6s

    5. Wait `delay`, polling discover_server_ip(2.0) each cycle:
         - server found → connect_as_client(found_ip); notify
           "Reconnected — <name> is now hosting"; DONE
    6. Deadline reached and I'm the next candidate:
         - final discovery sweep (double-server safety check)
         - none found → start server (reuse _async_start_host path),
           notify "You are now the host", DONE
    7. Roster empty or everything failed after ~30s
         → fall back to today's ServerActionDialog (human decides)
```

Also on graceful app exit while hosting: call
`server.broadcast_host_goodbye()` before closing (hook into `on_stop`).

Notes:

- Reuse `_async_start_host()` for the auto-start so Android still goes through
  the foreground service and desktop through the thread path — one code path
  for manual and automatic hosting.
- Direct-connect optimization: before discovery polling, try
  `connect_as_client(expected_new_host.ip)` once — usually succeeds instantly.
- Guard with an `self._migration_task` reference so a second disconnect during
  migration cancels and restarts the coroutine instead of stacking two.

---

## UI changes

| Moment | Widget | Text |
|---|---|---|
| Disconnect detected | `MDSnackbar` | "Host disconnected — finding a new host…" |
| I was elected | `MDSnackbar` + sidebar badge | "You are now the host" |
| Reconnected | `MDSnackbar` | "Reconnected — Fahim is now hosting" |
| Migration failed (~30s) | existing `ServerActionDialog` | "Couldn't recover automatically. Start a new server?" |

Also: the sidebar list adapts to `PeerInfo` and shows a small "HOST" tag next
to the rank-1 user, so everyone always knows who is hosting.

**Honest limitations to surface (not bugs):** chat history on the new server
starts empty (each device keeps its own scrollback), and files shared by the
departed host are no longer downloadable — in the P2P model files live on the
sharer's device.

---

## Edge cases checklist

- [ ] Host and rank-2 both offline → rank-3 takes over at T+6s (staggered timeouts)
- [ ] Two clients start servers anyway (extreme timing) → later starter's
      safety sweep finds the earlier one on next migration; UDP discovery
      always returns the first responder, so new joiners aren't split
- [ ] Old host comes back → it runs discovery on launch (existing behavior),
      finds the new host, joins as a regular client with a fresh join number
- [ ] Only one user left when host dies → roster (minus host) has just them →
      they're rank 1 → auto-become host of an empty room, snackbar explains it
- [ ] Disconnect during an active file download → download fails with the
      existing snackbar error; migration proceeds independently (different sockets)
- [ ] Rapid host churn (new host also dies mid-migration) → migration task is
      cancelled and restarted with the updated roster

---

## Test plan

**Unit (pytest, no UI):**
- Election math as a pure function `pick_migration_delay(roster, me, goodbye)`
  → table-driven tests: rank 2 gets 0s, rank 3 gets 6s, goodbye-nominee gets 0s,
  empty roster returns "give up".
- Schema round-trips for `PeerInfo`, new `ActiveUsersPacket`, `HostGoodbyePacket`;
  old-format packets are rejected (`parse_packet` returns `None`).
- Server assigns join orders 1,2,3…; after a disconnect the order of survivors
  is preserved; goodbye names the rank-2 peer.

**Integration (pytest + real sockets, like `test_file_registry.py`):**
- Spin up `MyServer` + 3 `MyClient`s → kill server → assert exactly one client
  computes delay 0 and the others compute staggered delays.

**Manual (two+ real devices):**
- Kill host app abruptly (force-quit) → verify one survivor becomes host,
  others reconnect, sidebar shows new HOST tag.
- Close host app normally → verify goodbye fast path (recovery ≈ 2–3s).
- Kill host AND the rank-2 device together → verify rank-3 recovers at ~6s.

---

## Implementation order

| Step | What | Size |
|---|---|---|
| 1 | Schemas: `PeerInfo`, updated `ActiveUsersPacket`/`ConnectPacket`, `HostGoodbyePacket` + tests | S |
| 2 | Server: join counter, IP capture, ordered broadcast, `broadcast_host_goodbye()` + tests | M |
| 3 | Sidebar UI adapts to `PeerInfo` (+ HOST tag) — **ships with 1–2** | S |
| 4 | Client: roster cache, rank helper, goodbye handling | S |
| 5 | Migration engine in `MainApplication` (coroutine, staggered timeouts, safety sweep, snackbars) | L |
| 6 | Graceful-exit goodbye hook (`on_stop`) | S |
| 7 | Integration test + two-device manual pass | M |

Steps 1–3 land together (they change the wire format). Steps 4–6 build on them.

> **Compatibility note:** this changes the `active_users` wire format, so old
> and new app versions can't mix in one room. Fine at this stage of the
> project; bump a protocol/version constant if old APKs are floating around.
