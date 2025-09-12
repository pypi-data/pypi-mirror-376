use std::{fs, path::Path};

use anyhow::{bail, Context, Result};
use regex::Regex;
use shapefile as shp;
use shapefile::{dbase::Record, Reader, Shape};

/// Convert shapefile::Polygon to geo::MultiPolygon<f64>
fn shp_to_geo(p: &shp::Polygon) -> geo::MultiPolygon<f64> {
    /// Ensure first and last are the same for geo::LineString coords
    fn ensure_closed(coords: &mut Vec<geo::Coord<f64>>) {
        if !coords.is_empty() {
            if coords[0] != coords[coords.len() - 1] {
                coords.push(coords[0])
            }
        }
    }

    /// Get the signed area of a geo::Coord list (negative for hole)
    fn signed_area(pts: &[geo::Coord<f64>]) -> f64 {
        let mut a = 0.0;
        for w in pts.windows(2) {
            a += w[0].x * w[1].y - w[1].x * w[0].y;
        }
        a / 2.0
    }

    // 1) Convert each ring into a LineString (ensure closed)
    let mut ls_rings: Vec<(geo::LineString<f64>, bool /*is_exterior*/)> = Vec::with_capacity(p.rings().len());
    for ring in p.rings().iter() {
        let mut coords: Vec<geo::Coord<f64>> = ring.points().iter().map(|pt| geo::Coord { x: pt.x, y: pt.y }).collect();
        ensure_closed(&mut coords);
        let ls = geo::LineString(coords);
        // Prefer explicit API if your ring exposes it; otherwise infer by orientation (CW => exterior in Shapefile).
        let is_exterior = signed_area(&ls.0) < 0.0;
        ls_rings.push((ls, is_exterior));
    }

    // 2) Group: each exterior with its following holes (Shapefile stores rings in this order)
    let mut polys: Vec<geo::Polygon<f64>> = Vec::new();
    let mut current_exterior: Option<geo::LineString<f64>> = None;
    let mut current_holes: Vec<geo::LineString<f64>> = Vec::new();

    for (ls, is_exterior) in ls_rings {
        if is_exterior {
            // flush previous polygon
            if let Some(ext) = current_exterior.take() {
                polys.push(geo::Polygon::new(ext, current_holes));
                current_holes = Vec::new();
            }
            current_exterior = Some(ls);
        } else {
            current_holes.push(ls);
        }
    }
    if let Some(ext) = current_exterior {
        polys.push(geo::Polygon::new(ext, current_holes));
    }

    geo::MultiPolygon(polys)
}

/// Convert geo::MultiPolygon<f64> to shapefile::Polygon
fn _geo_to_shp(mp: &geo::MultiPolygon<f64>) -> shp::Polygon {
    /// Create a shapefile::Point
    #[inline] fn shp_point(x: f64, y: f64) -> shp::Point { shp::Point { x, y } }

    /// Close a ring of shapefile::Point
    fn ensure_closed(pts: &mut Vec<shp::Point>) {
        if !pts.is_empty() {
            if pts[0].x != pts[pts.len() - 1].x || pts[0].y != pts[pts.len() - 1].y {
                pts.push(pts[0]);
            }
        }
    }

    /// Get the signed area of a shapefile::Point list (negative for hole)
    fn signed_area(pts: &[shp::Point]) -> f64 {
        let mut a = 0.0;
        for w in pts.windows(2) {
            a += w[0].x * w[1].y - w[1].x * w[0].y;
        }
        a / 2.0
    }

    // Build a flat list of rings in Shapefile ordering:
    // [ext CW, hole CCW, hole CCW, ..., next ext CW, ...]
    let mut rings: Vec<shp::PolygonRing<shp::Point>> = Vec::new();

    for poly in &mp.0 {
        // Exterior: force CW (Shapefile convention), ensure closed
        let mut ext_pts = poly.exterior().points().map(|c| shp_point(c.x(), c.y())).collect::<Vec<_>>();
        ensure_closed(&mut ext_pts);
        if signed_area(&ext_pts) > 0.0 {
            ext_pts.reverse(); // make CW
        }
        rings.push(shp::PolygonRing::Outer(ext_pts));

        // Holes: force CCW, ensure closed
        for hole in poly.interiors() {
            let mut hole_pts = hole.points().map(|c| shp_point(c.x(), c.y())).collect::<Vec<_>>();
            ensure_closed(&mut hole_pts);
            if signed_area(&hole_pts) < 0.0 {
                hole_pts.reverse(); // make CCW
            }
            rings.push(shp::PolygonRing::Inner(hole_pts));
        }
    }

    shp::Polygon::with_rings(rings)
}

/// Coerce a generic shape into an owned multipolygon, raising error if different shape
pub fn shape_to_multipolygon(shape: Shape) -> Result<geo::MultiPolygon<f64>> {
    match shape {
        Shape::Polygon(polygon) => Ok(shp_to_geo(&polygon)),
        other => bail!("found non-Polygon shape in layer: {:?}", other.shapetype())
    }
}

/// Read all shapes and records from a shapefile.
pub fn read_from_shapefile(path: &Path) -> Result<(Vec<Shape>, Vec<Record>)> {
    let mut reader = Reader::from_path(path)
        .with_context(|| format!("Failed to open shapefile: {}", path.display()))?;

    let (shapes, records) = reader.iter_shapes_and_records()
        .collect::<Result<Vec<_>, _>>()
        .with_context(|| format!("Error reading shapes+records from shapefile: {}", path.display()))?
        .into_iter().unzip();

    Ok((shapes, records))
}

/// Parse .prj WKT next to .shp and guess an EPSG when possible.
pub fn epsg_from_shapefile(shp_path: &Path) -> Option<u32> {
    let prj_path = shp_path.with_extension("prj");
    let wkt = fs::read_to_string(&prj_path).ok();

    // AUTHORITY["EPSG","<digits>"]
    wkt.as_deref().and_then(|txt| {
        Regex::new(r#"AUTHORITY\["EPSG","(\d+)"\]"#)
            .ok()
            .and_then(|re| re.captures(txt))
            .and_then(|c| c.get(1))
            .and_then(|m| m.as_str().parse::<u32>().ok())
    })
    // TIGER fallback (NAD83)
    .or_else(|| {
        wkt.as_deref().and_then(|txt| {
            if txt.contains("NAD_1983") || txt.contains("North_American_1983") { Some(4269) }
            else if txt.contains("WGS_1984") || txt.contains("WGS 84") { Some(4326) }
            else { None }
        })
    })
}
