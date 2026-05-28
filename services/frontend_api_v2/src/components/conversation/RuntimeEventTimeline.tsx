import type { RuntimeEvent } from "../../types/reguthink-interactive-api";

export function RuntimeEventTimeline({ events }: { events: RuntimeEvent[] }) {
  return (
    <section className="wb-mini-panel runtime-timeline">
      <h3>SSE Runtime Events</h3>
      {events.length === 0 ? (
        <div className="wb-placeholder">No events yet. Dry-run and controlled runtime events appear here.</div>
      ) : (
        events.map((event) => (
          <article key={event.event_id}>
            <strong>{event.event_type}</strong>
            <span>{event.stage}</span>
            <p>{event.message}</p>
          </article>
        ))
      )}
    </section>
  );
}
