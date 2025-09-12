# StarHTML Datastar API Reference

## Quick Start

StarHTML provides a Pythonic interface for creating reactive web applications using Datastar attributes. Every `ds_*` attribute is a function that returns a DatastarAttr object:

```python
from starhtml import Div, Button, Input, Form
from starhtml.datastar import ds_show, ds_on_click, ds_bind, ds_signals

# Basic reactive example
Div(
    Button("Toggle", ds_on_click("$show = !$show")),
    Div("Hello!", ds_show("$show")),
    ds_signals(show=True)
)
```

## Core Concepts

### 1. Signals and State

Signals are reactive variables that automatically update the UI:

```python
# Define initial signals
ds_signals(count=0, user="", active=True)

# Reference signals with $ prefix in expressions
ds_text("$count")
ds_show("$active")
ds_class(highlight="$count > 10")
```

### 2. Event Handling

Handle user interactions with event functions:

```python
# Basic click handler
Button("Click me", ds_on_click("$count++"))

# With modifiers
Form(
    ds_on_submit("handleSubmit()", "prevent"),
    Input(ds_on_input("search()", debounce="300ms"))
)

# Custom events
Div(ds_on("mouseenter", "$hovered = true"))
```

### 3. Two-Way Binding

Bind form inputs to signals:

```python
# Simple binding
Input(type="text", ds_bind("username"))

# With transformation
Input(type="email", ds_bind("email", case="lower"))
```

## Essential Helpers

### Template Literals with `t()`

Use Python f-string style for JavaScript template literals:

```python
from starhtml.datastar import t, ds_text

# Python f-string style → JavaScript template literal
Span(ds_text(t("Hello {$name}! You have {$count} messages.")))
# Outputs: data-text="`Hello ${$name}! You have ${$count} messages.`"
```

### Conditionals with `if_()`

```python
from starhtml.datastar import if_, ds_style, ds_class

# Simple ternary
Div(ds_class(active=if_("$selected", "bg-blue-500", "bg-gray-200")))

# Pattern matching
Div(ds_style(
    color=if_("$status",
        success="green",
        error="red",
        warning="orange",
        _="gray"  # default case
    )
))
```

### Comparison Helpers

```python
from starhtml.datastar import equals, gt, lt, gte, lte

Div(
    ds_show(gt("$count", 0)),           # $count > 0
    ds_class(warn=gte("$temp", 80)),    # $temp >= 80
    ds_disabled(equals("$status", "locked"))  # $status === 'locked'
)
```

### Conditional Tailwind Classes with `toggle_class()`

The simplest way to toggle between Tailwind class sets. Supports both binary and multi-state patterns:

```python
from starhtml.datastar import toggle_class

# Simple binary toggle (positional args: truthy, falsy)
Button(
    "Click me",
    **toggle_class("$active",
        "bg-blue-500 text-white shadow-lg",  # Truthy (first arg)
        "bg-gray-300 text-gray-600"          # Falsy (second arg)
    )
)

# With base classes that always apply
Div(
    "Step 1",
    **toggle_class("$currentStep >= 1",
        "bg-blue-500 text-white",              # Truthy
        "bg-gray-300 text-gray-600",           # Falsy
        base="flex items-center p-4 rounded-lg"  # Always applied
    )
)

# Multi-state pattern with named states
Div(
    **toggle_class("$status",
        success="bg-green-500 text-white",
        error="bg-red-500 text-white",
        warning="bg-yellow-500 text-black",
        _="bg-gray-300",  # Default state
        base="px-3 py-1 rounded"  # Always applied
    )
)

# Real-world examples:
# Dark mode
Div(
    **toggle_class("$darkMode",
        "bg-gray-900 text-gray-100",
        "bg-white text-gray-900",
        base="min-h-screen p-8 transition-colors"
    )
)

# Theme switching (multi-state)
Body(
    **toggle_class("$theme",
        dark="bg-gray-900 text-gray-100",
        light="bg-white text-gray-900",
        sepia="bg-amber-50 text-amber-900",
        _="bg-white text-gray-900",  # Default
        base="transition-colors duration-200"
    )
)

# Loading state
Button(
    "Submit",
    **toggle_class("$loading",
        "opacity-50 cursor-not-allowed",
        "hover:bg-blue-600 cursor-pointer",
        base="bg-blue-500 text-white px-4 py-2 rounded"
    ),
    **ds_attr(disabled="$loading")  # Can combine with other attributes
)
```

### When to Use Each Approach

- **`toggle_class()`** - For switching between Tailwind class sets (90% of cases)
- **`ds_style()`** - For inline CSS properties (`width`, `transform`, `opacity`)
- **`ds_class()`** - For granular control over individual classes
- **`ds_attr()`** - For non-class HTML attributes (`disabled`, `href`, `title`)

## Common Patterns

### Form with Validation

```python
Form(
    Input(type="email", ds_bind("email", case="lower")),
    Input(type="password", ds_bind("password")),
    Button("Login", ds_disabled("!$email || !$password")),
    ds_signals(email="", password=""),
    ds_on_submit("login()", "prevent")
)
```

### Interactive Elements

```python
# Hover effects
Div(
    "Hover me!",
    ds_signals(hovered=False),
    ds_style(
        background=if_("$hovered", "#e3f2fd", "#fff"),
        transform=if_("$hovered", "scale(1.05)", "scale(1)")
    ),
    ds_on("mouseenter", "$hovered = true"),
    ds_on("mouseleave", "$hovered = false")
)

# Toggle visibility with toggle_signal() helper
from starhtml.datastar import toggle_signal

Div(
    Button("Toggle Details", ds_on_click(toggle_signal("showDetails"))),  # Cleaner than "$showDetails = !$showDetails"
    Div(
        "Detailed information here...",
        ds_show("$showDetails")
    ),
    ds_signals(showDetails=False)
)
```

## Event Modifiers

Pass modifiers as positional arguments or kwargs:

```python
# Positional (HTML-style)
Button("Submit", ds_on_click("submit()", "once", "prevent"))

# Keyword arguments
Button("Submit", ds_on_click("submit()", once=True, prevent=True))

# Common modifiers
Input(ds_on_input("search()", debounce="300ms"))     # Debounce
Div(ds_on_scroll("handleScroll()", throttle="100ms")) # Throttle
Button(ds_on_click("save()", "prevent", "stop"))      # Prevent & stop propagation
```

## Type Conversions

Python types automatically convert to JavaScript:

```python
ds_show(True)                    # → data-show="true"
ds_signals(count=0, active=True) # → data-signals-count="0" data-signals-active="true"
ds_style(opacity=0.5)            # → data-style-opacity="0.5"
ds_signals(items=[1, 2, 3])      # → data-signals-items="[1,2,3]"
```

## Understanding Quotes

JavaScript expressions are passed as Python strings:

```python
# Expressions need quotes (they're Python strings containing JS code)
ds_on_click("$count++")              # JS expression
ds_text("$username || 'Anonymous'")  # JS expression with literal
ds_show("$items.length > 0")         # JS expression

# Signal definitions use Python syntax (no $ prefix)
ds_signals(count=0, username="")     # Python kwargs
ds_bind("email")                     # Python string
```

## Complete API Reference

### Core Attributes

| Function | Purpose | Example |
|----------|---------|----------|
| `ds_show(value)` | Show/hide element | `ds_show("$visible")` |
| `ds_text(value)` | Set text content | `ds_text("$message")` |
| `ds_bind(signal, case)` | Two-way binding | `ds_bind("email", case="lower")` |
| `ds_ref(name)` | Element reference | `ds_ref("myInput")` |
| `ds_indicator(name)` | Loading indicator | `ds_indicator("saving")` |
| `ds_effect(expr)` | Side effects | `ds_effect("console.log($count)")` |
| `ds_disabled(value)` | Disable element | `ds_disabled("$loading")` |

### Conditional Attributes

| Function | Purpose | Example |
|----------|---------|----------|
| `toggle_class(condition, truthy, falsy, base)` | Toggle Tailwind classes | `toggle_class("$active", "bg-blue-500", "bg-gray-300", base="p-4")` |
| `ds_class(**classes)` | Individual class toggles | `ds_class(bold="$important", hidden="!$visible")` |
| `ds_style(**styles)` | Inline CSS styles | `ds_style(opacity=if_("$loading", 0.5, 1))` |
| `ds_attr(**attrs)` | HTML attributes | `ds_attr(disabled="$loading", href="$link")` |

### Signals & State

| Function | Purpose | Example |
|----------|---------|----------|
| `ds_signals(**kwargs)` | Define signals | `ds_signals(count=0, user="")` |
| `ds_computed(name, expr)` | Computed signals | `ds_computed("total", "$price * $quantity")` |
| `ds_persist(*signals)` | Persist to storage | `ds_persist("theme", "user")` |
| `ds_json_signals()` | JSON state sync | `ds_json_signals(include="user")` |
| `toggle_signal(signal)` | Toggle boolean signal | `toggle_signal("menuOpen")` returns `"$menuOpen = !$menuOpen"` |

### Event Handlers

#### Core Interaction Events

| Function | Purpose | Common Modifiers |
|----------|---------|------------------|
| `ds_on_click(expr)` | Click handler | `once`, `prevent`, `stop` |
| `ds_on_input(expr)` | Input handler | `debounce`, `lazy` |
| `ds_on_submit(expr)` | Form submit | `prevent` |
| `ds_on_change(expr)` | Value change | - |
| `ds_on_invalid(expr)` | Form validation | - |
| `ds_on_keydown(expr)` | Key down | `enter`, `escape`, `ctrl`, `window` |
| `ds_on_keyup(expr)` | Key up | `enter`, `escape`, `ctrl` |
| `ds_on_scroll(expr)` | Scroll handler | `throttle`, `passive` |
| `ds_on_resize(expr)` | Window resize | `throttle` |
| `ds_on(event, expr)` | Custom events | Any modifiers |

#### Dialog & Popover Events

| Function | Purpose | Use Case |
|----------|---------|----------|
| `ds_on_toggle(expr)` | Element toggled | `<details>`, `<dialog>`, popovers |
| `ds_on_beforetoggle(expr)` | Before toggle | Pre-toggle validation/animation |

#### Clipboard Events

| Function | Purpose | Common Modifiers |
|----------|---------|------------------|
| `ds_on_copy(expr)` | Content copied | `prevent` |
| `ds_on_cut(expr)` | Content cut | `prevent` |
| `ds_on_paste(expr)` | Content pasted | `prevent` |

#### Animation & Transition Events

| Function | Purpose | Use Case |
|----------|---------|----------|
| `ds_on_animationstart(expr)` | CSS animation starts | Track animation state |
| `ds_on_animationend(expr)` | CSS animation ends | Cleanup after animation |
| `ds_on_animationiteration(expr)` | Animation iteration | Loop tracking |
| `ds_on_transitionstart(expr)` | CSS transition starts | Track transition state |
| `ds_on_transitionend(expr)` | CSS transition ends | Post-transition actions |

#### Media Events

| Function | Purpose | Use Case |
|----------|---------|----------|
| `ds_on_play(expr)` | Media starts playing | Video/audio controls |
| `ds_on_pause(expr)` | Media paused | Update UI state |
| `ds_on_ended(expr)` | Media finished | Next track, replay |
| `ds_on_volumechange(expr)` | Volume changed | Volume UI update |
| `ds_on_timeupdate(expr)` | Playback position update | Progress bar |
| `ds_on_canplay(expr)` | Media can start | Enable play button |
| `ds_on_loadedmetadata(expr)` | Metadata loaded | Display duration |
| `ds_on_progress(expr)` | Download progress | Loading indicator |

#### Page & Network Events

| Function | Purpose | Use Case |
|----------|---------|----------|
| `ds_on_online(expr)` | Network reconnected | Sync data |
| `ds_on_offline(expr)` | Network lost | Show offline mode |
| `ds_on_error(expr)` | Error occurred | Error handling |
| `ds_on_message(expr)` | postMessage received | Cross-origin comm |
| `ds_on_storage(expr)` | Storage changed | Cross-tab sync |
| `ds_on_popstate(expr)` | History navigation | SPA routing |
| `ds_on_hashchange(expr)` | URL hash changed | Anchor navigation |
| `ds_on_visibilitychange(expr)` | Tab visibility changed | Pause/resume |
| `ds_on_beforeunload(expr)` | Before page unload | Save confirmation |
| `ds_on_fullscreenchange(expr)` | Fullscreen toggled | UI adjustments |

### Special Attributes

| Function | Purpose | Example |
|----------|---------|----------|
| `ds_ignore()` | Skip processing | `ds_ignore("self")` |
| `ds_preserve_attr(*attrs)` | Keep during morph | `ds_preserve_attr("style", "class")` |

## Advanced Patterns

### Persistent State

```python
# Persist specific signals
ds_persist("theme", "userPreferences")

# Persist with patterns
ds_persist(include=["user", "settings"], exclude=["temp"])

# Session storage
ds_persist("currentTab", session=True)
```

### Computed Values

```python
ds_computed("fullName", "$firstName + ' ' + $lastName")
ds_computed("isValid", "$email && $password.length >= 8")
ds_computed("subtotal", "$items.reduce((sum, item) => sum + item.price, 0)")
```

### Complex Event Handling

```python
# Keyboard shortcuts
Input(ds_on_keydown("handleKey($event)", "ctrl.enter"))

# Intersection observer
Div(
    "Lazy loaded content",
    ds_on_intersect("loadContent()", once=True)
)

# Intervals
Div(
    ds_text("$time"),
    ds_on_interval("$time = new Date().toLocaleTimeString()", duration="1000ms")
)
```

## Handlers

StarHTML provides specialized handlers for complex interactions like drag-and-drop and infinite canvas functionality.

### Canvas Handler

Enable infinite canvas with pan/zoom functionality:

```python
from starhtml.handlers import canvas_handler
from starhtml.datastar import ds_canvas_viewport, ds_canvas_container, ds_on_canvas

# Basic canvas setup
canvas_handler(
    signal="canvas",              # Signal prefix (default: "canvas")
    enable_pan=True,              # Enable click-drag panning
    enable_zoom=True,             # Enable mouse wheel/pinch zoom
    min_zoom=0.1,                 # Minimum zoom level
    max_zoom=10.0,                # Maximum zoom level
    touch_enabled=True,           # Enable touch gestures
    enable_grid=True,             # Show grid background
    grid_size=100,                # Major grid line spacing
    grid_color="#e0e0e0",         # Major grid line color
    minor_grid_size=20,           # Minor grid line spacing
    minor_grid_color="#f0f0f0"    # Minor grid line color
)
```

**Reactive Signals Created:**
- `${signal}_pan_x`: number - Pan X offset in pixels
- `${signal}_pan_y`: number - Pan Y offset in pixels  
- `${signal}_zoom`: number - Current zoom level (1.0 = 100%)
- `${signal}_is_panning`: bool - Whether currently panning

**Helper Functions Created:**
- `${signal}_reset_view()` - Reset to initial pan and zoom
- `${signal}_zoom_in()` - Zoom in by 20%
- `${signal}_zoom_out()` - Zoom out by 20%

**HTML Attributes:**
- `ds_canvas_viewport()` - Mark element as canvas viewport (handles events)
- `ds_canvas_container()` - Mark element as canvas container (gets transformed)
- `ds_on_canvas("expression")` - Handler for canvas events

**Usage Example:**
```python
@rt("/canvas")
def canvas_demo():
    return Div(
        canvas_handler("canvas"),
        Div(
            # Content that can be panned/zoomed
            Div("Canvas content here", ds_canvas_container()),
            ds_canvas_viewport(),
            ds_on_canvas("console.log('Pan:', $canvas_pan_x, $canvas_pan_y)"),
            cls="viewport"
        ),
        # Controls
        Button("Reset", ds_on_click("$canvas_reset_view()")),
        Button("Zoom In", ds_on_click("$canvas_zoom_in()")),
        Button("Zoom Out", ds_on_click("$canvas_zoom_out()")),
    )
```

### Drag Handler

Enable drag-and-drop with reactive state management:

```python
from starhtml.handlers import drag_handler
from starhtml.datastar import ds_draggable, ds_drop_zone

# Basic drag setup
drag_handler(
    signal="drag",                    # Signal prefix (default: "drag")
    mode="freeform",                  # "freeform" or "sortable"
    throttle_ms=16,                   # Throttle updates (16ms = 60fps)
    constrain_to_parent=False,        # Keep within parent bounds
    touch_enabled=True                # Enable touch/mobile dragging
)
```

**Reactive Signals Created:**
- `${signal}_is_dragging`: bool - Whether any element is being dragged
- `${signal}_element_id`: string|null - ID of currently dragged element
- `${signal}_x`: number - X position (relative to container or screen)
- `${signal}_y`: number - Y position (relative to container or screen)
- `${signal}_drop_zone`: string|null - Name of current drop zone
- `${signal}_zone_[name]_items`: array - Items in/over each drop zone

**HTML Attributes:**
- `ds_draggable()` - Mark element as draggable
- `ds_drop_zone("zone-name")` - Mark element as drop zone
- `ds_on_drag("expression")` - Handler expression for drag events

**Drag Modes:**
- `freeform`: Free positioning, tracks drop zone overlap
- `sortable`: List reordering, moves items between zones

**Usage Example:**
```python
@rt("/drag-drop")
def drag_drop():
    return Div(
        drag_handler("drag", mode="freeform", constrain_to_parent=True),
        
        # Draggable items
        Div("Drag me!", ds_draggable(), id="item1", cls="draggable"),
        Div("Me too!", ds_draggable(), id="item2", cls="draggable"),
        
        # Drop zones
        Div("Drop here", ds_drop_zone("inbox"), cls="drop-zone"),
        Div("Or here", ds_drop_zone("archive"), cls="drop-zone"),
        
        # Status display
        P(f"Dragging: ", ds_text("$drag_is_dragging ? $drag_element_id : 'none'")),
        P(f"Drop zone: ", ds_text("$drag_drop_zone || 'none'")),
        
        ds_signals(drag_is_dragging=False, drag_element_id=None)
    )
```

**Canvas + Drag Integration:**
```python
@rt("/canvas-drag")
def canvas_with_draggable_nodes():
    return Div(
        # Both handlers work together
        canvas_handler("canvas", enable_grid=True),
        drag_handler("node", mode="freeform"),
        
        Div(
            # Draggable nodes on canvas
            Div("Node 1", ds_draggable(), id="node1", cls="node"),
            Div("Node 2", ds_draggable(), id="node2", cls="node"),
            
            ds_canvas_container(),
            cls="canvas-content"
        ),
        ds_canvas_viewport(),
        cls="canvas-viewport"
    )
```

## Best Practices

1. **Use $ prefix only in expressions** - Not in signal definitions
2. **Leverage helper functions** - `t()`, `if_()`, and comparison helpers
3. **Group related attributes** - Use `ds_class()`, `ds_style()` for multiple values
4. **Consistent naming** - Use `snake_case` for Python/JavaScript compatibility
5. **Type safety** - The API is fully typed for better IDE support