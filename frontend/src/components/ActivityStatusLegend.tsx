/** Legend for the planned-vs-done activity map styling
 * (see components/mapLayers.ts#ensureActivityStatusLayers) — shared by
 * PropertyMapPage (authenticated) and PublicPropertyPage (public) since
 * both render the same two-color, dashed-vs-solid distinction. Sightings
 * aren't part of this legend; their plain blue circle doesn't vary. */
export default function ActivityStatusLegend() {
  return (
    <div className="map-legend">
      <span className="map-legend__item">
        <span className="map-legend__swatch map-legend__swatch--planned" />
        Planned / in progress
      </span>
      <span className="map-legend__item">
        <span className="map-legend__swatch map-legend__swatch--done" />
        Done
      </span>
    </div>
  );
}
