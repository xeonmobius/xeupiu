# Graph Report - xeupiu  (2026-07-04)

## Corpus Check
- 143 files · ~261,155 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 304 nodes · 578 edges · 26 communities (21 shown, 5 thin omitted)
- Extraction: 79% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 109 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `88a4c0ef`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_App Core|App Core]]
- [[_COMMUNITY_Module Imports|Module Imports]]
- [[_COMMUNITY_Database & Text|Database & Text]]
- [[_COMMUNITY_Overlay Base|Overlay Base]]
- [[_COMMUNITY_Character Creation|Character Creation]]
- [[_COMMUNITY_Confession Handling|Confession Handling]]
- [[_COMMUNITY_Character Recognition|Character Recognition]]
- [[_COMMUNITY_CLI Entry & Errors|CLI Entry & Errors]]
- [[_COMMUNITY_Linux Screenshot|Linux Screenshot]]
- [[_COMMUNITY_Project Docs|Project Docs]]
- [[_COMMUNITY_Confession Database|Confession Database]]
- [[_COMMUNITY_Configuration|Configuration]]
- [[_COMMUNITY_Selectable Rect Overlay|Selectable Rect Overlay]]
- [[_COMMUNITY_Save Selection Overlay|Save Selection Overlay]]
- [[_COMMUNITY_Windows Screenshot|Windows Screenshot]]
- [[_COMMUNITY_Character DB Script|Character DB Script]]
- [[_COMMUNITY_Textbox Overlay|Textbox Overlay]]
- [[_COMMUNITY_Dev Setup & Packaging|Dev Setup & Packaging]]
- [[_COMMUNITY_Package Scripts|Package Scripts]]
- [[_COMMUNITY_Gotchas|Gotchas]]
- [[_COMMUNITY_Credits|Credits]]
- [[_COMMUNITY_Package Root|Package Root]]

## God Nodes (most connected - your core abstractions)
1. `OverlayWindow` - 25 edges
2. `App` - 23 edges
3. `PoorCR` - 22 edges
4. `Database` - 19 edges
5. `Translator` - 15 edges
6. `SelectableRectOverlay` - 14 edges
7. `ScrollingEpilogueHandler` - 13 edges
8. `get_count_by_equality()` - 11 edges
9. `ConfessionHandler` - 10 edges
10. `NotebookDatabase` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Project Logo` ----> `Project Purpose`  [0.8]
  data/resources/logo.png → README.md
- `App Icon` ----> `Project Overview`  [0.8]
  data/resources/icon_small.png → AGENTS.md
- `Emulator Setup` ----> `Project Purpose`  [0.9]
  tutorial.md → README.md
- `App` --uses--> `ConfessionHandler`  [INFERRED]
  src/xeupiu/app.py → src/xeupiu/confession_handler.py
- `App` --uses--> `Database`  [INFERRED]
  src/xeupiu/app.py → src/xeupiu/database.py

## Import Cycles
- None detected.

## Communities (26 total, 5 thin omitted)

### Community 0 - "App Core"
Cohesion: 0.15
Nodes (7): format_translated_text(), ScrollingEpilogueDatabase, Image, ndarray, ScrollingEpilogueHandler, ScrollingEpilogueOverlayWindow, Translator

### Community 1 - "Module Imports"
Cohesion: 0.16
Nodes (3): # TODO: many of these can be reintegrated within the cue system, to optimize per, check_is_text_empty(), separate_into_lines()

### Community 2 - "Database & Text"
Cohesion: 0.15
Nodes (10): convert_birthday_to_str(), convert_damage_jp2en(), convert_date_jp2en(), convert_date_to_en_str(), convert_date_to_jp_str(), convert_jp_date_to_int(), convert_jp_str_to_int(), Expects strings in format '７月２３日'. (+2 more)

### Community 3 - "Overlay Base"
Cohesion: 0.14
Nodes (11): OverlayWindow, Image, ndarray, Detects whether the game object to be overlayed is present in the screenshot., Hides the overlay if it is not needed., Hides the overlay window., A semi-transparent window that displays text on top of the game window., Shows the overlay window. (+3 more)

### Community 4 - "Character Creation"
Cohesion: 0.36
Nodes (6): detect_character_creation_player(), detect_character_creation_shiori(), Image, ndarray, convert_to_black_and_white(), convert_to_black_and_white_multiple()

### Community 5 - "Confession Handling"
Cohesion: 0.38
Nodes (10): get_count_by_thresholds(), detect_ending_game_save_menu(), detect_mark_by_count(), detect_mark_by_count_min(), detect_mark_by_count_with_thresholds(), detect_mark_character_selection_choice_1(), detect_mark_character_selection_choice_2(), detect_mark_textbox_choice1() (+2 more)

### Community 6 - "Character Recognition"
Cohesion: 0.10
Nodes (16): Image, ndarray, WeekdayOverlayWindow, extract_characters(), pad_char(), trim_char(), load_character_db(), PoorCR (+8 more)

### Community 7 - "CLI Entry & Errors"
Cohesion: 0.10
Nodes (14): display_error(), Error message windows.  Currently we are using xdialog, but this could change., Display an error message with the given window title and message., _ensure_xwayland(), _find_duckstation_pids(), main(), Kill DuckStation processes, respawn with XWayland env vars. Returns True if wind, Check Wayland + DuckStation state. Show dialog if needed. Returns True to procee (+6 more)

### Community 8 - "Linux Screenshot"
Cohesion: 0.22
Nodes (9): get_window_base_dims(), get_window_by_title(), get_window_image(), _get_xwin(), Image, Returns the window ID of the window with the given title.     If there are multi, Returns a PIL image of the window with the given ID.      :param window_id: The, Returns the position and size of the window with the given ID.      :param windo (+1 more)

### Community 9 - "Project Docs"
Cohesion: 0.20
Nodes (10): Architecture, Project Overview, Project Phases, Project Purpose, Textractor Comparison, Emulator Setup, FAQ, Translation Backend Setup (+2 more)

### Community 10 - "Confession Database"
Cohesion: 0.11
Nodes (13): Image, ndarray, ConfessionDatabase, ConfessionHandler, detect_confession(), detect_confession_character(), ndarray, ConfessionSubtitleOverlay (+5 more)

### Community 11 - "Configuration"
Cohesion: 0.27
Nodes (3): BordersDict, Configuration, TypedDict

### Community 12 - "Selectable Rect Overlay"
Cohesion: 0.21
Nodes (5): is_str_empty(), NotebookDatabase, Image, ndarray, SelectableRectOverlay

### Community 13 - "Save Selection Overlay"
Cohesion: 0.36
Nodes (3): Image, ndarray, SaveSelectionOverlayWindow

### Community 14 - "Windows Screenshot"
Cohesion: 0.33
Nodes (6): get_window_base_dims(), get_window_by_title(), get_window_image(), Returns the window ID of the window with the given title.     If there are multi, Returns a PIL image of the window with the given ID.      :param window_id: The, Returns the position and size of the window with the given ID.      :param windo

### Community 17 - "Textbox Overlay"
Cohesion: 0.10
Nodes (10): App, AttributeOverlayWindow, CharacterCreationHandler, YearMonthDayOverlayWindow, NameDatabase, TextDatabase, Image, ndarray (+2 more)

### Community 19 - "Dev Setup & Packaging"
Cohesion: 0.67
Nodes (3): Setup Instructions, Development Setup, Release Packaging

## Knowledge Gaps
- **13 isolated node(s):** `package_executable.sh script`, `xeupiu`, `Architecture`, `Gotchas`, `Textractor Comparison` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `OverlayWindow` connect `Overlay Base` to `App Core`, `Module Imports`, `Character Recognition`, `Confession Database`, `Selectable Rect Overlay`, `Save Selection Overlay`, `Textbox Overlay`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Why does `App` connect `Textbox Overlay` to `App Core`, `Module Imports`, `Database & Text`, `Overlay Base`, `Character Recognition`, `Confession Database`, `Selectable Rect Overlay`, `Save Selection Overlay`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Why does `PoorCR` connect `Character Recognition` to `App Core`, `Module Imports`, `Linux Screenshot`, `Selectable Rect Overlay`, `Character DB Script`, `Textbox Overlay`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `OverlayWindow` (e.g. with `App` and `AttributeOverlayWindow`) actually correct?**
  _`OverlayWindow` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `App` (e.g. with `AttributeOverlayWindow` and `CharacterCreationHandler`) actually correct?**
  _`App` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `PoorCR` (e.g. with `App` and `.__init__()`) actually correct?**
  _`PoorCR` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `Database` (e.g. with `App` and `ConfessionDatabase`) actually correct?**
  _`Database` has 7 INFERRED edges - model-reasoned connections that need verification._