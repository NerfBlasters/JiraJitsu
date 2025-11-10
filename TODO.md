# JiraJitsu TODO List

Project tasks and feature tracking.

## Active TODOs

### High Priority

- [ ] **Better debug logging** - Include full response bodies in debug mode
- [ ] **Failed tickets log** - Save failed tickets to separate log file with copy-pasteable issue list for retry

### Medium Priority

- [ ] **Attachment verification** - Under NEW_ONLY setting, verify each attachment exists (not just directory)
- [ ] **JitAPI JSON-only output** - Make jitapi command output only JSON for better piping to `jq`
- [ ] **JitAPI pagination fix** - Tickets endpoint doesn't respect `--offset` and `--count` params together (API bug?)

### Low Priority

- [ ] **Default log filtering** - Make default log level INFO but only show CRITICAL+ to console
- [ ] **Auto-cleanup technician permissions** - After migration, remove temporary technician permissions granted during migration
  - Would need to track which permissions were added vs already existed
  - Use `RemoveCategoryTechPermission` endpoint

### Future Enhancements

See [docs/NEW_FEATURES.md](docs/NEW_FEATURES.md) and [CONTRIBUTING.md](CONTRIBUTING.md) for ideas.

---

## Completed (Archive)

### v1.2.0 (January 2025)

- [x] Add check/logging for "ticket not created in jitbit" failure (ISD-55)
- [x] API optimization - Cache users and technicians at migration start
- [x] Fix user assignment issues - Tickets incorrectly assigned to wrong user
- [x] Remove hardcoded JIRA project references (RFM) - Now uses /myself endpoint
- [x] Optimize user lookups - Single GET to /users endpoint with caching
- [x] Cache technician status - Use TechsForCategory endpoint at start
- [x] Default to creating new users automatically
- [x] Improve jitapi UX - Changed from `--endpoint X -p key val` to `X --key val` syntax
- [x] Fix migrate --issues switch - Was being ignored, now works correctly
- [x] Add HTML rendering option with --html flag
- [x] Add filter pagination for >1000 issues
- [x] Add wiki markup cleaning (color tags)
- [x] Add duplicate detection
- [x] Add migration statistics summary table

### v1.1.0 (November 2024)

- [x] Token authentication support for JIRA and JitBit
- [x] Interactive setup wizard
- [x] Enhanced validation commands
- [x] Fix critical JitBit API bugs (Authorization, AttachFile, User endpoints)
- [x] URL normalization fixes

### v1.0.0 (November 2024)

- [x] Python 3.10+ compatibility
- [x] Hybrid configuration system (.env + config.yml)
- [x] Comment author tracking
- [x] Comment timestamps preservation
- [x] Technician flag validation
- [x] Enhanced metadata preservation
- [x] Universal update method (post_update_ticket)
- [x] Comprehensive logging
- [x] pytest test infrastructure

---

## Notes

- For new features, update documentation (see [CONTRIBUTING.md](CONTRIBUTING.md))
- Check [CHANGELOG.md](CHANGELOG.md) for complete version history
- See [GitHub Issues](repository-url-here) for bug reports and feature requests
