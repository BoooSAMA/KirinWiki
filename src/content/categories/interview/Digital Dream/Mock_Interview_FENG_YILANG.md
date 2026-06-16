# Mock Interview — FENG YILANG

> **Company**: VR product company (Unity-based)
> **Role**: Technical Engineering Programmer
> **Interview Language**: English
> **Core Bet**: You chose this course for VR. You're building a VR game right now. Your C#/Blazor experience transfers to Unity scripting. You've learned 3ds Max modeling. Your embedded background proves you think about performance. You're not starting from zero — you're accelerating.

---

## 🟢 WARM-UP: "Tell me about yourself."

> 2 minutes max. Lead with C#. End with why VR.

**Script:**

```
I'm Feng Yilang, a final-year Computer Engineering student at Temasek
Polytechnic graduating in May 2027. I chose this course specifically
because I wanted to work in 3D and VR — that's been my focus from day one.

On the programming side, I'm strongest in C#. I built a full-stack exam
platform with Blazor and ASP.NET Core — database design, role-based auth,
real-time state management, the whole stack. This semester, I've been
applying those C# skills directly to Unity scripting, and I'm currently
building a VR mini-game on my own to push myself into the deep end.

I also learned 3ds Max last semester for 3D modeling, so I understand
the art pipeline — I can talk to 3D artists in their language and I
know what makes a model game-ready versus just pretty in the viewport.

Beyond that, I've worked across the full spectrum: C at the register level
on PIC16 microcontrollers for a flood detection system, Flutter for mobile
IoT dashboards, and I've trained 10 AI models on SDXL just to understand
the generative AI pipeline.

I'm here because VR is the reason I enrolled in this course. This isn't
just another job application for me — it's the thing I've been aiming at
for two years. I want to build things people physically step into and
experience, and your products sit exactly at that intersection.
```


---

## 🔴 HIGH-PROBABILITY: C# & Programming Fundamentals

> **They're hiring a programmer. They WILL test your C#.**

---

### 1. "Explain the difference between a class and a struct in C#. When would you use each?"

**Answer:**

```
Class is a reference type — allocated on the heap, passed by reference.
Struct is a value type — allocated on the stack (usually), passed by copy.

I'd use a struct when:
- The data is small (typically under 16 bytes)
- It's logically a single value (like Vector3, Color, Quaternion)
- I need value semantics — copying should create an independent instance
- Performance matters and I want to avoid heap allocation / GC pressure

I'd use a class when:
- The object has identity (two instances with same data are not equal)
- It's large or will grow
- I need inheritance
- It represents a game entity (like a Player, Enemy, Weapon)

In Unity specifically, Vector3 is a struct — and that's exactly right,
because you create thousands of them per frame in a typical game loop.
If Vector3 were a class, the GC would destroy your frame rate.

Real example from my exam platform: I used structs for ExamQuestion
data transfer objects — they're small, immutable after grading, and get
created in bulk during auto-grading. No heap allocation, no GC pauses.
```

**Follow-up:**

| Q | A |
|---|---|
| "What happens if a struct is very large?" | "Copy overhead becomes a problem. Every assignment or method pass copies the entire struct. The .NET docs recommend keeping structs under 16 bytes. Beyond that, the copy cost outweighs the GC savings." |
| "Can a struct implement an interface?" | "Yes, but with a boxing penalty — the struct gets boxed to a heap object when cast to the interface. That defeats the performance reason for using a struct. I'd avoid it in hot paths." |

---

### 2. "How does garbage collection work in C#? How does it affect Unity game performance?"

> **Critical for VR: 90 FPS = 11ms per frame. GC spikes kill frame rate.**

**Answer:**

```
The .NET GC uses a generational mark-and-compact collector:

- Gen 0: Short-lived objects (collected frequently, fast)
- Gen 1: Buffer between Gen 0 and Gen 2
- Gen 2: Long-lived objects (collected rarely, expensive)
- LOH (Large Object Heap): Objects > 85KB

Objects start in Gen 0. If they survive a collection, they promote to
Gen 1, then Gen 2. The key insight: Gen 2 collections are STW (stop-the-world)
and can take tens of milliseconds — that's multiple dropped frames in VR.

In Unity VR targeting 90 FPS, every frame has an ~11ms budget. A Gen 2
collection that takes 15ms means you miss at least 1 frame — the user
feels a hitch. In VR, frame drops cause motion sickness.

My strategies to avoid GC in Unity code:
1. Object pooling — reuse instead of new/delete (bullets, particles, enemies)
2. Avoid boxing — don't cast structs to interfaces, use generics instead
3. Cache frequently-used components (GetComponent in Awake, not Update)
4. Use StringBuilder for string concatenation in loops
5. Avoid LINQ in Update/FixedUpdate — creates hidden allocations
6. Pre-allocate collections with known capacity (new List<T>(expectedSize))

Even from my Blazor work, I'm conscious of allocations. On the exam platform,
I pre-computed grading rubrics as dictionaries during exam initialization
rather than rebuilding them per-student — same principle, different runtime.
```

**Follow-up:**

| Q | A |
|---|---|
| "What tools do you use to profile GC?" | "In Unity: the Profiler window's CPU Usage view shows GC.Alloc per frame. The Deep Profiler shows allocations by method. I'd also use the Memory Profiler package to track heap growth over time. Outside Unity, dotMemory or PerfView for .NET apps." |
| "What's the difference between IDisposable and a finalizer?" | "IDisposable gives deterministic cleanup — the caller controls when resources release. A finalizer (~ClassName) runs non-deterministically when the GC collects the object, which could be seconds later. For Unity, I always prefer IDisposable — I can call Dispose when a scene unloads, instead of hoping the GC runs at a convenient time." |

---

### 3. "Explain async/await. How is it different from Unity coroutines?"

**Answer:**

```
async/await is C#'s language-level feature for asynchronous programming.
When you await a Task, the method suspends at that point and returns
control to the caller. The compiler generates a state machine behind
the scenes. When the awaited operation completes, execution resumes on
the captured SynchronizationContext.

Key differences from Unity coroutines:

1. Return type: async methods return Task/Task<T> — composable, chainable,
   can await multiple operations with Task.WhenAll. Coroutines return
   IEnumerator — harder to compose.

2. Error handling: async uses try/catch naturally. Coroutines can't catch
   exceptions across yield boundaries — the exception gets logged but
   doesn't propagate.

3. Timing: async/await has no built-in frame or time awareness. A coroutine
   with `yield return new WaitForSeconds(1)` is frame-aware. If you need
   per-frame operations in async, you'd use UniTask's `.Yield()` or
   `.NextFrame()`.

4. Threading: async/await can run on thread pool threads. Coroutines always
   run on the main thread — all Unity API calls are main-thread-only.

5. Cancellation: async uses CancellationToken — standardized, composable.
   Coroutines use StopCoroutine — string or IEnumerator-based, less flexible.

In practice for Unity VR:
- Use coroutines for frame-by-frame animations, physics-timed sequences
- Use async/await (via UniTask) for: loading assets, network requests,
  file I/O — anything where you don't need per-frame updates
- Never use standard Task.Delay in Unity — it doesn't respect game time
  scale or editor pause. Always use UniTask.Delay instead.

Example from my Blazor exam platform: I used async/await for database
queries — loading a student's exam history is I/O-bound, not CPU-bound.
The same pattern applies to loading VR assets or fetching user data.
```

**Follow-up:**

| Q | A |
|---|---|
| "What's UniTask?" | "A zero-allocation async/await library for Unity by Cysharp. Standard Task<T> allocates on every await — UniTask uses struct-based tasks to avoid GC. For VR at 90 FPS, those allocations matter. It's essentially the standard in production Unity projects." |
| "What's ConfigureAwait(false)?" | "It tells the state machine not to capture the SynchronizationContext when resuming. In a Unity context, this means the continuation runs on a thread pool thread instead of the main thread. I use it for pure computation after an I/O await — but I must switch back to the main thread before touching any Unity API or GameObject." |

---

### 4. "Interface vs abstract class — when do you use which? Give me a concrete example."

**Answer:**

```
Interface: defines a contract — "what you can do" — no implementation.
Abstract class: defines shared identity + partial implementation — "what you are."

I use an interface when unrelated classes need the same capability.
I use an abstract class when related classes share behavior AND identity.

Concrete example from game design:

// Interface — any destructible thing, regardless of what it is
public interface IDamageable {
    void TakeDamage(float amount);
    bool IsAlive { get; }
}
// A barrel, a wall, a player, an enemy — all implement IDamageable
// They have nothing in common except being damageable

// Abstract class — all enemies share base behavior
public abstract class Enemy : MonoBehaviour {
    protected float health;
    protected float moveSpeed;

    public virtual void Patrol() {
        // Default patrol behavior all enemies share
        transform.Translate(Vector3.forward * moveSpeed * Time.deltaTime);
    }

    public abstract void Attack(); // Each enemy attacks differently
}

public class MeleeEnemy : Enemy {
    public override void Attack() { /* swing weapon */ }
}

public class RangedEnemy : Enemy {
    public override void Attack() { /* fire projectile */ }
}

Why this matters for VR: In a VR game, you might have interactable objects
(doors, levers, items) that share pickup logic but behave differently.
Abstract class = shared pickup logic. Interface = "this thing responds to
hand tracking" regardless of whether it's a lever or a UI button.
```

**Follow-up:**

| Q | A |
|---|---|
| "C# 8+ default interface methods — do they change this?" | "They let interfaces provide default implementations, which blurs the line. But I still treat interfaces as contracts first. Default methods are for backward compatibility — adding a method without breaking existing implementations. I wouldn't use them to replace abstract classes for shared state." |

---

### 5. "Write a simple event system in C# — Observer pattern. Why would you use this in Unity?"

**Answer (whiteboard style):**

```csharp
// Simple generic event system
public class EventBus {
    private static Dictionary<string, Action<object>> _events = new();

    public static void Subscribe(string eventName, Action<object> handler) {
        if (_events.ContainsKey(eventName))
            _events[eventName] += handler;
        else
            _events[eventName] = handler;
    }

    public static void Unsubscribe(string eventName, Action<object> handler) {
        if (_events.ContainsKey(eventName))
            _events[eventName] -= handler;
    }

    public static void Publish(string eventName, object data = null) {
        if (_events.TryGetValue(eventName, out var handler))
            handler?.Invoke(data);
    }
}

// Usage in VR context:
// When player grabs an object:
EventBus.Publish("OnObjectGrabbed", grabbedObject);

// Hand tracking system listens:
EventBus.Subscribe("OnObjectGrabbed", (obj) => {
    // Update hand pose, haptic feedback
});
```

```
Why use this in Unity:
1. Decoupling — the hand tracking system doesn't need a reference to
   every grabbable object. Objects just fire events.
2. Extensibility — I can add a tutorial system that listens for "first
   grab" without modifying any existing code.
3. Testability — I can unit-test systems in isolation by publishing
   events without setting up the full scene.

Tradeoff: string-based events have no compile-time safety. In production,
I'd use a typed event system or ScriptableObject-based event channels
to get both decoupling AND type safety.

From my Blazor work: I used a similar pattern with C# events/delegates
for the exam platform — when a student submits, an event triggers
auto-grading, analytics logging, and UI refresh. Same architecture,
different domain.
```

---

### 6. "Explain the difference between `List<T>` and `IEnumerable<T>`. When would LINQ cause performance problems?"

**Answer:**

```
List<T> is a concrete collection — data is already in memory, you can
index it, count it, add/remove from it.

IEnumerable<T> is an interface that represents a sequence — it might be
backed by a List, a database query, or a generator. The key difference:
IEnumerable is lazy. The data might not exist yet.

This matters because of deferred execution in LINQ:

// BAD — iterates the collection 3 times
var enemies = GetAllEnemies();
var alive = enemies.Where(e => e.IsAlive);       // Query defined, not executed
var count = enemies.Count();                      // Execution 1
var nearby = enemies.Where(e => distance < 5f);   // Query defined, not executed
foreach (var e in alive) { /* ... */ }            // Execution 2
foreach (var e in nearby) { /* ... */ }           // Execution 3

// GOOD — materialize once
var enemiesList = GetAllEnemies().ToList();       // Single execution
var alive = enemiesList.Where(e => e.IsAlive);
// ... now iterate freely, no re-evaluation

Performance problems with LINQ:
1. Hidden allocations — Where() creates an iterator object, Select()
   creates another. Each LINQ call allocates.
2. Chaining — .Where().Select().OrderBy() creates 3+ allocations
   plus temporary arrays for sorting.
3. In hot paths (Update, FixedUpdate) — even small allocations
   trigger GC, which kills VR frame rate.

My rule: LINQ is great for data processing during scene load, config
parsing, editor tools — anywhere outside the frame loop. Inside Update
or FixedUpdate, I use for/foreach with pre-allocated collections.
```

**Follow-up:**

| Q | A |
|---|---|
| "What's the difference between First() and FirstOrDefault()?" | "First() throws InvalidOperationException if the sequence is empty. FirstOrDefault() returns default(T) — null for reference types, 0 for int, etc. I use FirstOrDefault() when 'not found' is a valid state and I'll handle it. I use First() when absence is truly a bug and I want it to fail loudly." |

---

## 🟡 MEDIUM-PROBABILITY: Unity & VR Specifics

---

### 7. "Walk me through the MonoBehaviour lifecycle — what runs when?"

> **Context**: You started Unity scripting this semester and you're building a VR game. Show them you've already internalized the fundamentals.

**Answer:**

```
I started Unity scripting this semester, and the MonoBehaviour lifecycle
is one of the first things I made sure I understood properly — because if
you get Awake vs Start wrong, you spend hours debugging null references.
Here's the sequence:

Initialization (once):
  Awake()       — Called when the GameObject is instantiated.
                  Use for: getting references (GetComponent), setting
                  up internal state. NOT for anything that depends on
                  other objects being initialized.

  OnEnable()    — Called when the object becomes active. Use for:
                  subscribing to events, resetting state on re-enable.

  Start()       — Called before the first frame update. At this point,
                  all Awake() calls have completed. Use for:
                  initialization that depends on other objects.

Per-frame (every frame, in order):
  FixedUpdate() — Fixed timestep (0.02s default). Use for:
                  physics — Rigidbody forces, collision checks.
                  Frame-rate independent.

  Update()      — Once per frame, variable timestep. Use for:
                  most game logic — input, movement, state checks.

  LateUpdate()  — After all Update() calls. Use for:
                  camera follow, anything that needs other objects'
                  final positions.

Decommissioning:
  OnDisable()   — When object becomes inactive. Use for:
                  unsubscribing events, cleanup.
  OnDestroy()   — When object is destroyed. Use for:
                  final cleanup, releasing resources.

For VR specifically, the order matters for motion-to-photon latency:
- Input should be read as late as possible in Update
- Physics in FixedUpdate
- Camera/late-Update transforms in LateUpdate

I'm applying this daily in my VR game project — I've already hit the
classic Start-vs-Awake bug and learned my lesson. I'm building the muscle
memory now, so by the time I join your team, this lifecycle will be
second nature.
```

---

### 8. "VR has to hit 90 FPS consistently. Tell me about your approach to performance optimization."

**Answer:**

```
90 FPS = 11.1ms per frame total. That budget includes: input processing,
game logic, physics, rendering, and VR compositor overhead. Miss it and
the user gets reprojected frames or motion sickness.

My optimization approach, top to bottom:

1. MEASURE FIRST — Unity Profiler, Frame Debugger, GPU Profiler.
   Never optimize based on assumptions. Find the bottleneck.

2. CPU optimizations:
   - Object pooling over instantiate/destroy (avoids GC spikes)
   - Cache components — GetComponent<T>() in Awake, not Update
   - Avoid Find() and FindObjectOfType() at runtime — O(n) searches
   - Use non-allocating APIs (Physics.OverlapSphereNonAlloc)
   - Job System + Burst compiler for heavy computation (pathfinding,
     procedural animation, sensor data processing)

3. GPU optimizations:
   - Draw call batching (static batching, dynamic batching, GPU instancing)
   - LOD (Level of Detail) — fewer triangles at distance
   - Occlusion culling — don't render what the user can't see
   - Single-pass stereo rendering — render both eyes in one pass
     instead of two (critical for VR)
   - Texture atlasing to reduce material switches
   - Shader complexity — forward rendering over deferred for VR
     (MSAA for anti-aliasing, lower bandwidth)

4. VR-specific:
   - Fixed foveated rendering — lower resolution at the periphery
     of the eye tracker (Quest Pro, PSVR2)
   - Asynchronous SpaceWarp / Motion Smoothing — reproject frames
     when you miss the deadline
   - Minimal post-processing — bloom, motion blur, DOF are
     expensive in stereo

From my embedded background: I've already learned to think in real-time
budgets. On the PIC16 flood detector, I had to fit sensor sampling,
filtering, and LCD updates into a tight interrupt-driven loop. The
mindset transfers — know your deadlines, measure your costs, never guess.
```

---

### 9. "How would you structure the code for a VR interaction — say, picking up an object with hand tracking?"

**Answer:**

```
I'd use a component-based architecture — the Unity way:

[HandTracker.cs]
- Reads hand tracking data (XR Input System or platform SDK)
- Raises events: OnPinchStart, OnPinchEnd, OnHandMoved
- One instance per hand

[Grabbable.cs]
- Attached to any object the user can pick up
- Implements IGrabHandler interface
- Handles: OnGrabBegin(HandTracker hand), OnGrabEnd()
- Stores: original parent, original position/rotation
- No direct reference to specific hand — works with any

[Throwable : Grabbable]
- Extends Grabbable with velocity tracking
- On release: calculates release velocity from hand motion,
  applies Rigidbody.AddForce() relative to hand's velocity

[HandPoseController.cs]
- Listens to IGrabHandler events
- When grabbing: switches hand mesh to grab pose
- When releasing: returns to open palm pose

High-level flow:
1. HandTracker detects pinch gesture → fires OnPinchStart
2. IGrabHandler on nearest grabbable receives the event
3. If conditions met (distance, angle, not already grabbed):
   → Grabbable parent = HandTracker bone transform (follows hand)
4. OnPinchEnd → release → calculate throw velocity, restore parent

Why this structure:
- Each component has ONE responsibility
- HandTracker doesn't know about Grabbable, Grabbable doesn't know
  about HandPose — they communicate through interfaces/events
- I can add new grab behaviors (Throwable, SnapZone, TwoHandGrab)
  without modifying existing code
- Testable: I can write unit tests for Grabbable by faking input events

This is the same architecture pattern I used in the exam platform:
controllers handle input, services process logic, events wire them together.
The domain changes, the pattern doesn't.
```

---

### 10. "What's a ScriptableObject and why would you use it?"

**Answer:**

```
ScriptableObject is a Unity data container that lives as an asset file,
not on a GameObject. It's the only Unity-native way to create data-only
assets without attaching them to a scene object.

I'd use it for:

1. Configuration data: weapon stats, enemy parameters, level settings.
   Instead of hardcoding values in MonoBehaviour, reference a SO.
   Designer can tweak values without touching code.

2. Shared data between scenes: player health, inventory, game settings
   that persist across scene loads.

3. Event channels (SO-based events):
   - Create a GameEvent : ScriptableObject with a UnityEvent
   - Grabbable fires GameEvent when grabbed
   - Any system can reference the SAME GameEvent asset and listen
   - No singleton, no FindObjectOfType, no tight coupling

4. Runtime sets: keep a List<Enemy> as a SO. Any enemy registers itself
   in OnEnable, removes in OnDisable. Systems that need "all enemies"
   just reference the SO — no scene traversal.

Why not use a singleton MonoBehaviour instead?
- SOs exist independently of scenes (singleton dies when scene unloads)
- SOs are editable in the Inspector (designer-friendly)
- SOs don't have Update() overhead (pure data)
- SOs make unit testing possible (inject mock SO in test)

I learned about SOs by researching Unity architecture patterns — they're
the standard solution for clean data flow in production Unity projects.
```

---

## 🔴 YOUR CURRENT VR PROJECT — They Will 100% Ask

> **You told them you're building a VR game right now. They will ask about it. This is your best opportunity to show passion + competence.**

---

### 11. "Tell me about the VR game you're building."

**Answer:**

```
I'm building a [describe your game concept in 2 sentences — e.g.,
"a room-scale puzzle game where the player manipulates gravity to
navigate through impossible architecture" or "an archery defense
game where you physically draw and aim, defend a castle from waves"].

I started this semester when I began learning Unity scripting, and it's
evolving as I learn — every new Unity concept I pick up, I apply to the
game immediately.

On the technical side, I'm using:
- Unity's XR Interaction Toolkit for hand tracking / controller input
  and grab interactions
- Unity's physics system (Rigidbody, Colliders) for object interaction
- C# MonoBehaviour scripts for game logic — the same C# patterns I
  used in Blazor: component-based design, event-driven communication,
  clean separation between input handling and game state
- [Add anything specific: animation, particle effects, spatial audio,
  raycasting, navmesh, etc.]

I've also applied my 3ds Max knowledge from last semester — I model
my own assets, which means I understand the full loop: model in Max →
export with correct scale/UVs → import to Unity → set up materials
and colliders → script the behavior. I'm not just a programmer waiting
for art assets — I can prototype the whole experience end to end.

What I'm learning the hard way: [mention one honest challenge — e.g.,
"performance optimization — my first build ran at 45 FPS and I had
to learn about draw calls, batching, and LOD to get it to 90" or
"VR locomotion — teleport vs smooth movement, and how nausea changes
your design decisions"]. But that's exactly why I'm building it — to
hit these problems before I encounter them on a production team.

My goal is to have a playable demo by [month]. Even if it's rough,
I want to prove I can take a VR concept from idea to headset.
```

**Follow-up:**

| Q | A |
|---|---|
| "What's been the hardest Unity concept to learn?" | "The MonoBehaviour lifecycle took me a while to internalize — specifically the difference between Awake, Start, and OnEnable, and when to use each for initialization. I had a bug where my script was finding references in Awake that hadn't been set up yet in another object's Awake. Learning the execution order window and using explicit script ordering solved it. Now I know: Awake for self-setup, Start for cross-object setup." |
| "How big is the scope? Solo or team?" | "Solo for now — I'm treating it as my personal training ground. I'd rather understand every line of code than split work with teammates and miss learning opportunities. That said, I'm using Git with proper commit messages and a project board, as if it were a team project — because good habits form early." |
| "What Unity version and rendering pipeline?" | "[Your answer — e.g., Unity 6 / 2022 LTS, URP because VR needs forward rendering for MSAA anti-aliasing. I chose URP over Built-in because it's the standard for VR projects and gives me Shader Graph for visual effects.]" |

---

## 🟢 BEHAVIORAL: Your Background Through a Unity Lens

---

### 12. "Your largest project is in Blazor, not Unity. Convince me your C# skills transfer."

**Answer:**

```
My Blazor exam platform is 5000+ lines of C# across 20+ components and
services. Here's what directly transfers to Unity:

1. OOP architecture: I used dependency injection (IServiceProvider),
   repository pattern (IExamRepository → ExamRepository), and service
   layers (ExamService, GradingService, AuthService). The principles —
   single responsibility, interface-based design, loose coupling — are
   identical in Unity with Zenject or VContainer.

2. State management: The exam platform manages complex state — a student
   taking a timed exam with multiple answers, auto-save, and server sync.
   In Unity, this maps to game state machines, player state, and save
   systems. The mental model is the same.

3. Entity Framework Core + SQL Server: I designed a normalized database
   schema, wrote LINQ queries, handled migrations. This is directly
   relevant to any VR app with user accounts, progress tracking, or
   leaderboards.

4. Async patterns: I used async/await for database queries and email
   verification (SMTP). In Unity with UniTask, async/await is the
   standard for asset loading and network calls.

5. LINQ and generics: I'm comfortable with delegates, lambda expressions,
   generics, and LINQ — all used heavily in Unity codebases for data
   processing and editor tools.

The difference isn't the language — it's the API surface. I'm already
learning GameObject, Transform, MonoBehaviour, and the XR stack through
my VR game project this semester. API knowledge is the FASTEST thing to
learn — I'm proving that right now. Architectural thinking, debugging
methodology, knowing when to use an interface vs. abstract class —
that's the hard part, and I already have it from real C# projects.

And here's the thing you can verify: open my Blazor exam platform code
and my Unity VR game scripts side by side. You'll see the same
architectural thinking — service layers, dependency injection,
event-driven communication. The syntax changes. The thinking doesn't.
```

---

### 13. "You worked on embedded systems (PIC16, ESP32). How does that make you a better VR programmer?"

**Answer:**

```
Embedded programming teaches you something most application developers
never learn: you have hard real-time constraints and no safety net.

On a PIC16 with 368 bytes of RAM and a 4MHz clock:
- Every microsecond counts — there's no garbage collector, no OS
  scheduler, no "just add more memory"
- You think in terms of interrupt latency, register-level timing,
  and deterministic execution
- Debugging means reading a logic analyzer trace, not stack traces
  — you develop the patience to stare at raw hardware signals until
  you see the pattern

In VR at 90 FPS:
- You have an ~11ms frame budget — that's 11,000 microseconds
- The GC is your worst enemy — in embedded, there IS no GC, so you
  already think in terms of pre-allocated buffers and fixed memory
- When a frame drops, you don't get a nice error — the user feels
  sick. This is a "hard real-time" constraint, just like the flood
  detector's sensor polling deadline

The embedded mindset is: "understand the hardware, measure before
optimizing, respect the deadline." Every senior VR developer I've
talked to says the same thing — the hardest part of VR isn't the API,
it's the discipline of hitting 90 FPS every single frame. Embedded
gave me that discipline.
```

---

### 14. "Talk about a time you learned a complex system on your own."

**STAR Answer:**

```
SITUATION: For my diploma, I chose to build a full-stack web application
using Blazor and Entity Framework Core — two technologies I had zero
experience with. The module provided basic tutorials, but I needed to
build a production-quality platform in 12 weeks.

TASK: Go from zero Blazor knowledge to a deployed exam platform with
role-based auth, timed exams, auto-grading, email verification, and
an analytics dashboard.

ACTION: I broke the learning into focused sprints:
- Week 1: Watched Microsoft's official Blazor documentation, built a
  todo app, deleted it, rebuilt it with proper component structure
- Week 2: Same approach for EF Core — built a prototype schema,
  learned migrations, wrote LINQ queries against test data
- Week 3-4: Studied existing Blazor projects on GitHub to understand
  production patterns (not just tutorials)
- Week 5-12: Iterative development — ship a feature, test it with
  real users (classmates), fix what breaks, ship the next one

RESULT: I delivered a platform my lecturer described as one of the
strongest submissions. It handled 50+ concurrent test sessions,
auto-graded answers across 4 difficulty levels, and included features
I designed myself (email verification, analytics with Chart.js).

The key insight: I don't learn by watching — I learn by building,
breaking, and rebuilding. I expect the same ramp-up with Unity:
build a simple VR scene that works, study your existing codebase
patterns, start contributing small features, then take on larger
systems. Based on my track record, that ramp-up takes weeks, not months.
```

---

### 15. "Your only work experience is a graphic design internship. How does that prepare you for a programming role?"

> **They WILL ask this. It's the elephant in the room. Own it.**

**Answer:**

```
I took that internship because it was available and I wanted professional
experience of any kind — working under deadlines, collaborating with a
team, receiving feedback from someone who's not your lecturer. Those are
transferable skills that school projects don't teach you.

Here's what that 15-month internship actually gave me:

1. DEADLINE DISCIPLINE: I delivered edited clips and thumbnails on a
   publishing schedule. If I was late, the content didn't go out. In VR
   development, if you miss a sprint deadline, the demo doesn't happen.
   The pressure is the same — only the output format changes.

2. CREATIVE ITERATION: My designs went through rounds of feedback from
   the team lead. I learned to not get attached to my first version, to
   implement someone else's vision, and to iterate fast. Game development
   is exactly the same loop: prototype → feedback → iterate → ship.

3. VISUAL LITERACY: I spent over a year thinking about composition, color
   harmony, and visual hierarchy. When I'm building a VR UI or placing
   objects in a scene, I'm not starting from zero — I understand why
   certain layouts feel right and others feel cluttered. Most programmers
   don't have this background.

4. CROSS-DISCIPLINE COMMUNICATION: I was the bridge between the content
   team's creative vision and the technical execution. In a VR team, I
   can talk to designers in their language because I've been one.

The honest truth: I didn't get a programming internship because those
are competitive for diploma students. But instead of waiting for one,
I built 4 complete programming projects on my own. That's 4 repos of
production-quality code. I'd rather hire someone who built things
independently than someone who fetched coffee at a software company for
3 months.

My internship proves I can function in a professional environment.
My projects prove I can program. Together, they're a complete package.
```

**Follow-up questions:**

| Q | A |
|---|---|
| "Do you prefer design or programming?" | "Programming. I enjoyed design as a creative outlet, but my brain naturally gravitates toward systems — how things connect, how data flows, how to structure code so it doesn't collapse under its own weight. Design taught me to care about the end-user experience, which makes me a better programmer. But programming is what I want to do professionally." |
| "Why didn't you get a programming internship?" | "I applied to a few, but diploma-level programming internships are scarce in Singapore — most companies want degree students. The graphic design role was available, paid, and in a production environment. I took it as a stepping stone. Now I have professional work experience PLUS a strong programming portfolio. In hindsight, that combination might actually serve me better than a mediocre programming internship would have." |
| "What was the hardest part of that internship?" | "Adapting to the team's evolving content style. The channel's visual direction changed every few months based on audience analytics. I had to unlearn what I'd just mastered and adopt a new style quickly. That flexibility — not getting pigeonholed into one way of working — is what you need in a studio that ships new VR experiences regularly." |

---

## 🔵 DIFFICULT QUESTIONS

---

### 16. "What's your biggest weakness as a programmer?"

**Answer:**

```
I sometimes get too deep into implementation details before I've fully
understood the problem. Early in the exam platform project, I spent two
days building an elaborate question-randomization algorithm — only to
realize the requirements specified random selection from question banks,
not true randomization with constraints.

I'd solved a harder problem than the one I was asked to solve.

What I changed: Now, before I write any code, I write down in plain
English what the feature should do, what the edge cases are, and what
"done" looks like. I show it to whoever defined the requirement and get
confirmation. This 10-minute step has saved me countless hours.

For Unity VR development, this means: before I optimize a shader or
restructure the input system, I'll make sure I understand what problem
the team is actually experiencing, not what I ASSUME the problem is.
```

---

### 17. "We have experienced Unity developers applying. Why should we invest in training you?"

**Answer:**

```
I won't pretend I'm a senior Unity developer — I'm not. But I'm also
not starting from zero.

Right now, this semester, I am:
- Writing Unity C# scripts for a VR game I'm building solo
- Applying the same component-based architecture I used in Blazor to
  Unity's MonoBehaviour system
- Learning the XR Interaction Toolkit for hand tracking and input
- Modeling my own 3D assets in 3ds Max (which I learned last semester)
  and importing them into Unity — so I understand the full art pipeline

By the time I join your team, I won't need "what's a prefab" training.
I'll need: your coding standards, your VR-specific patterns, and your
codebase architecture. That's onboarding, not education — weeks, not months.

Here's what experienced Unity developers rarely bring:

1. 3D art pipeline literacy: I've done the 3ds Max → Unity import loop.
   I know what makes a model game-ready — correct scale, UV unwrapping,
   poly count budgets. When your 3D artist says "the normal map is
   inverted on import," I actually understand what that means.

2. Cross-domain thinking: I've bridged web, mobile, embedded, and AI
   in real projects. When your VR headset needs to communicate with a
   cloud backend or external hardware, I've done both.

3. No bad habits: I haven't spent 5 years doing Unity the wrong way in
   a studio with no code review. You shape me to your patterns, not
   un-teach me someone else's.

4. VR is why I'm here: I chose this diploma specifically for 3D and VR.
   This isn't a job — it's the destination I've been steering toward.
   That kind of intrinsic motivation can't be trained.

Senior developers optimize what exists. I'll learn what exists, bring
fresh perspective from other domains, and bring the hunger of someone
who's been aiming at this exact role since day one of his diploma.
```

---

### 18. "You have a diploma, not a degree. Does that concern you?"

**Answer:**

```
I understand the concern — a degree filters for certain baseline
qualities. But here's my honest view:

A CS degree teaches you: data structures, algorithms, operating systems,
theory. I have practical versions of all of these:
- Data structures: I've chosen between List, Dictionary, Queue in
  production code based on Big-O characteristics
- Algorithms: I wrote a randomized question selection algorithm that
  balances difficulty distribution across exam papers
- OS concepts: I've written ISR handlers and timer configurations at
  the register level — that's deeper OS understanding than most CS
  grads who just passed the exam

What a degree doesn't teach: shipping code that real users interact with.
I have 4 complete project lifecycles. I've debugged sensor hardware,
designed database schemas, handled authentication security, written
automated grading logic, trained AI models, and polished frontend UIs.

I'm not asking you to ignore the diploma. I'm asking you to interview
me like you'd interview a degree holder — ask the same C# questions,
the same architecture questions, the same problem-solving questions.
If I can't answer them, I don't deserve the job. If I can, the piece
of paper shouldn't matter.
```

---

## 📋 C# QUICK-FIRE (They might throw these in casually)

| Q | A |
|---|---|
| "What's the `using` statement do?" | "Syntactic sugar for try/finally. Guarantees Dispose() is called on IDisposable objects. At compile time: `using (var x = new Resource()) { ... }` becomes `try { ... } finally { x.Dispose(); }`. Essential for file handles, database connections, Unity's NativeArrays." |
| "Difference between `const` and `readonly`?" | "`const` is compile-time constant — value baked into IL, must be primitive/string/enum, implicitly static. `readonly` is runtime constant — set in constructor, can be any type, instance or static. In Unity: use `const` for truly unchanging values (Mathf.PI-style), `readonly` for things set by config at startup." |
| "What's a delegate? When would you use Action vs Func?" | "A delegate is a type-safe function pointer. `Action` returns void, `Func<T>` returns T. I use Action for callbacks with no return (event handlers). Func for transformations (Select in LINQ, factory methods). In Unity: `Action<Vector3>` for position change callbacks, `Func<bool>` for condition checks." |
| "What's a generic constraint?" | "Restricts what type T can be. `where T : MonoBehaviour` means T must be a MonoBehaviour. `where T : class, new()` means reference type with parameterless constructor. Prevents runtime type errors at compile time. I used `where T : BaseEntity` extensively in my EF Core repositories." |
| "String vs StringBuilder?" | "`string` is immutable — every concatenation allocates a new string. `StringBuilder` maintains a mutable buffer. In a loop building a large string, StringBuilder avoids O(n²) allocations. In Unity's Update: never use string concatenation — use StringBuilder or pre-formatted strings." |
| "What's a NullReferenceException and how do you prevent it?" | "Accessing a member on null. Prevention: (1) null-conditional operator `?.` (2) null-coalescing `??` (3) constructor injection guarantees (4) `[NotNull]` attributes (5) in Unity: caching GetComponent results and checking before use. In VR: a null reference during hand tracking update = dropped frame, so be defensive." |

---

## 🎯 QUESTIONS YOU SHOULD ASK THEM

### Technical:

1. "What's your Unity version and rendering pipeline? URP, HDRP, or Built-in? I'd like to understand the constraints I'd be working within."

2. "How does your team handle dependency injection? Zenject, VContainer, or manual service locators?"

3. "What's the most challenging performance bottleneck you've hit in VR — CPU, GPU, or memory? I'm curious what optimization patterns have paid off the most."

4. "How do you approach testing in Unity? Unit tests with the Test Framework, integration tests, or mostly manual QA?"

### Team & Growth:

5. "What does onboarding look like for a new programmer? Do you pair on bugs first, or is there a starter project?"

6. "How does code review work on your team? I want to learn from senior developers' feedback."

---

## ⚠️ WHAT NOT TO SAY

| Don't Say | Say Instead |
|---|---|
| "I've never used Unity." | "I haven't shipped a Unity project yet, but I've studied the architecture — MonoBehaviour lifecycle, prefab system, the component model. My C# skills transfer directly." |
| "It was just a school project." | "It was an academic project that I treated like production code — with proper architecture, error handling, and version control." |
| "I don't know." (and stop) | "I don't know the answer to that. But based on what I do know, I'd approach it by..." |
| "I'm a fast learner." (vague) | "I went from zero Blazor knowledge to shipping a full-stack platform in 12 weeks — including database design, auth, email integration, and auto-grading." |
| "I'll work hard." | "Here's my GitHub — you can see my commit history. I ship consistently, not just before deadlines." |

---

## 📝 PREP CHECKLIST

- [ ] Practice C# fundamentals out loud — class vs struct, async/await, interface vs abstract
- [ ] Build and ship one minimal Unity project before the interview (even a rolling ball in VR)
- [ ] Read Unity's XR Interaction Toolkit documentation
- [ ] Study one open-source Unity VR project on GitHub — understand their folder structure
- [ ] Memorize your STAR stories: Blazor exam platform (C# depth), flood detector (performance mindset), LoRA training (self-learning)
- [ ] Prepare your Unity ramp-up plan — specific things you'll learn in weeks 1-4
- [ ] Have your GitHub open — be ready to walk through your Blazor code architecture
