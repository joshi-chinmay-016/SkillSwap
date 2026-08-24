# Jitsi Meet Video Integration

SkillSwap Arena integrates **Jitsi Meet** as its WebRTC video and audio collaboration infrastructure.

---

## 1. Authoritative Meeting Link Generation

- **Deterministic Room Scoping**: Meeting links are generated server-side during session booking by `jitsi_service.py`:
  ```
  https://meet.jit.si/SkillSwapArena-Session-{session_id}-{deterministic_hash}
  ```
- **Authoritative Record**: The URL is stored directly on the `sessions.meeting_link` column in PostgreSQL.
- **Client Mounting**: The frontend workspace (`SessionPage.jsx`) mounts the Jitsi Meet external API IFrame securely using the authoritative link.

---

## 2. Security & Boundaries

1. **Room Access Control**: Only authenticated participants (the assigned mentor, learner, or an admin) receive the meeting link through protected session detail endpoints (`GET /sessions/{id}`).
2. **Audio/Video Privacy**: Video and audio streams are peer-to-peer or routed through Jitsi's selective forwarding units (SFU). SkillSwap Arena **does not record or store raw video/audio media**.
3. **Collaborative Capture**: All educational notes, discussion topics, and takeaways are captured explicitly in the sidebar workspace using structured collaborative data inputs.
