---
title: "Common Pitfalls"
layout: default
parent: "X4 Modding Reference"
nav_order: 17
---

# Common Pitfalls

Recurring issues across all modding topics, compiled from community experience:

1. **Uppercase filenames** -- MD scripts in `md/` must be lowercase. X4 silently ignores files that do not match expected casing. On Linux, all paths are case-sensitive.

2. **Full file replacement instead of diff patching** -- breaks on every game update and conflicts with other mods. Always use `<diff>` patches for library files.

3. **Missing index registration** -- the number one reason new content "does not exist." Every new macro needs `index/macros.xml`; every new component needs `index/components.xml`.

4. **Forgetting `&quot;` escaping in XPath** -- attribute values in diff patch `sel` XPath must use `&quot;` for quotes: `sel="//ware[@id=&quot;energycells&quot;]"`.

5. **Line breaks in content.xml** -- use `&#10;` in description text, not `\n`.

6. **Silent diff patch failures** -- if a `sel` XPath does not match, X4 logs a warning but otherwise silently skips. Enable `-debug all` to see these. Use `x4cat validate-diff` to catch them before shipping.

7. **Version field is an integer** -- `version="100"` means version 1.00. Multiply by 100.

8. **Game updates break things** -- diff patches are more resilient than replacements, but any mod can break on major updates. Consider locking game versions for stable mod lists.

9. **Ware IDs must be lowercase** -- uppercase characters in ware IDs cause problems on case-sensitive filesystems.

10. **Mod placement** -- mods can go in two locations:
    - Game directory: `<X4 install>/extensions/`
    - User documents: `Documents/Egosoft/X4/extensions/`
    - Some features (like `subst` catalogs) only work from the game directory.

---
