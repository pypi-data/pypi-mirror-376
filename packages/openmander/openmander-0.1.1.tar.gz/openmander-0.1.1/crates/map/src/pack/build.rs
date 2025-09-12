use std::{collections::{HashMap, HashSet}, path::Path};

use anyhow::{anyhow, bail, Context, Ok, Result};
use openmander_geom::Geometries;
use polars::{frame::DataFrame, prelude::*, series::Series};
use shapefile::{dbase::{FieldValue, Record}};

use crate::{common::*, GeoId, GeoType, Map, MapLayer, ParentRefs};

impl MapLayer {
    /// Loads layer geometries and data from a given .shp file path.
    fn from_tiger_shapefile(ty: GeoType, path: &Path) -> Result<Self> {
        let (shapes, records) = read_from_shapefile(path)?;
        let epsg = epsg_from_shapefile(path);

        /// Convert a vector of records to a DataFrame (using TIGER/PL census format)
        fn records_to_dataframe(records: Vec<Record>, ty: GeoType) -> Result<DataFrame> {
            /// Get the value of a character field from a Record
            fn get_character_field(record: &Record, field: &str) -> Result<String> {
                match record.get(field) {
                    Some(FieldValue::Character(Some(s))) => Ok(s.trim().to_string()),
                    _ => bail!("missing or invalid character field: {}", field)
                }
            }

            /// Get the value of a numeric field from a Record
            fn get_numeric_field(record: &Record, field: &str) -> Result<f64> {
                match record.get(field) {
                    Some(FieldValue::Numeric(Some(n))) => Ok(*n),
                    _ => bail!("missing or invalid numeric field: {}", field)
                }
            }

            Ok(DataFrame::new(vec![
                Column::new(
                    "geo_id".into(),
                    records.iter()
                        .map(|record| get_character_field(record, "GEOID20"))
                        .collect::<Result<Vec<_>>>()?,
                ),
                Column::new(
                    "name".into(),
                    records.iter()
                        .map(|record| match ty {
                            GeoType::County | GeoType::Group => get_character_field(record, "NAMELSAD20"),
                            _ => get_character_field(record, "NAME20"),
                        })
                        .collect::<Result<Vec<_>>>()?,
                ),
                Column::new(
                    "centroid_lon".into(),
                    records.iter()
                        .map(|record| {
                            let s = get_character_field(record, "INTPTLON20")?;
                            Ok::<f64>(s.trim().parse()?)
                        })
                        .collect::<Result<Vec<_>>>()?,
                ),
                Column::new(
                    "centroid_lat".into(),
                    records.iter()
                        .map(|record| {
                            let s = get_character_field(record, "INTPTLAT20")?;
                            Ok::<f64>(s.trim().parse()?)
                        })
                        .collect::<Result<Vec<_>>>()?,
                ),
                Column::new(
                    "area_m2".into(),
                    records.iter()
                        .map(|record| Ok::<f64>(
                            get_numeric_field(record, "ALAND20")? + get_numeric_field(record, "AWATER20")?
                        ))
                        .collect::<Result<Vec<_>>>()?,
                ),
                Column::new(
                    "land_m2".into(),
                    records.iter()
                        .map(|record| get_numeric_field(record, "ALAND20"))
                        .collect::<Result<Vec<_>>>()?,
                ),
                Column::new(
                    "water_m2".into(),
                    records.iter()
                        .map(|record| get_numeric_field(record, "AWATER20"))
                        .collect::<Result<Vec<_>>>()?,
                ),
            ])?)
        }

        let df = records_to_dataframe(records, ty)?
            .with_row_index("idx".into(), None)?;

        // Convert shapes from shapefile::Polygon to geo::MultiPolygon<f64>
        let geoms = Geometries::new(
            &shapes.into_iter()
                .map(|shape| shape_to_multipolygon(shape))
                .collect::<Result<Vec<_>>>()
                .with_context(|| format!("Error converting shapes to multipolygons in shapefile: {}", path.display()))?,
            epsg,
        );

        Self::from_dataframe(ty, df, Some(geoms))
    }

    /// Initialize layer with a list of geo_ids, replacing existing data.
    fn _set_data(&mut self, geo_ids: Vec<&str>) -> Result<()> {
        self.parents.resize(geo_ids.len(), ParentRefs::default());

        self.data = DataFrame::new(vec![Column::new("geo_id".into(), &geo_ids)])?;
        self.data = self.data.with_row_index("idx".into(), None)?;

        self.geo_ids = geo_ids.iter()
            .map(|&val| GeoId::new(self.ty(), val))
            .collect();

        self.index = self.geo_ids.iter().enumerate()
            .map(|(i, geo_id)| (geo_id.clone(), i as u32))
            .collect();

        Ok(())
    }

    /// Merge new dataframe into self.data, preserving geo_id
    fn merge_data(&mut self, df: DataFrame, id_col: &str) -> Result<()> {
        // Assert size of dataframe matches self.data
        if df.height() != self.data.height() {
            bail!("insert_data: size of dataframe ({:?}) does not match expected size: {:?}.", df.height(), self.data.height());
        }

        // Assert id_col exists and has type String
        df.column(id_col)
            .with_context(|| format!("insert_data: missing id column {:?}", id_col))?
            .str().with_context(|| format!("insert_data: id_col {:?} must be of type String", id_col))?;

        self.data = self.data.inner_join(&df, ["geo_id"], [id_col])?
            .sort(["idx"], SortMultipleOptions::default())?;

        Ok(())
    }

    /// Assign parent references for each entity in the layer, based on their truncated geo_id.
    fn assign_parents(&mut self, parent_ty: GeoType) {
        self.geo_ids.iter().enumerate()
            .map(|(i, geo_id)| self.parents[i].set(parent_ty,Some(geo_id.to_parent(parent_ty))))
            .collect()
    }

    /// Assign parent references for each entity in the layer, based on a provided map of geo_id to parent geo_id.
    fn assign_parents_from_map(&mut self, parent_ty: GeoType, parent_map: HashMap<GeoId, GeoId>) -> Result<()> {
        self.geo_ids.iter().enumerate()
            .map(|(i, geo_id)| Ok(parent_map.get(geo_id)
                .ok_or_else(|| anyhow!("No parent found for entity with geo_id: {:?}", geo_id))
                .map(|geo_id| self.parents[i].set(parent_ty, Some(geo_id.clone())))))
            .collect::<Result<_>>()?
    }

    /// Compute adjacencies for the layer geometries, if it exists.
    fn compute_adjacencies(&mut self) -> Result<()> {
        let geoms = self.geoms.as_mut()
            .ok_or_else(|| anyhow!("Cannot compute adjacencies on empty geometry!"))?;
        self.adjacencies = geoms.compute_adjacencies_fast(1e8)?;
        Ok(())
    }

    /// Compute shared perimeters for the layer geometries, if it exists.
    fn compute_shared_perimeters(&mut self) -> Result<()> {
        let geoms = self.geoms.as_mut()
            .ok_or_else(|| anyhow!("Cannot compute perimeters on empty geometry!"))?;
        self.shared_perimeters = geoms.compute_shared_perimeters_fast(&self.adjacencies, 1e8)?;
        Ok(())
    }
}

impl Map {
    /// Compute parent references for all layers based on truncated geo_id.
    fn assign_parents_from_geo_ids(&mut self) {
        self.get_layer_mut(GeoType::County).assign_parents(GeoType::State);
        self.get_layer_mut(GeoType::Tract).assign_parents(GeoType::County);
        self.get_layer_mut(GeoType::Tract).assign_parents(GeoType::State);
        self.get_layer_mut(GeoType::Group).assign_parents(GeoType::Tract);
        self.get_layer_mut(GeoType::Group).assign_parents(GeoType::County);
        self.get_layer_mut(GeoType::Group).assign_parents(GeoType::State);
        self.get_layer_mut(GeoType::VTD).assign_parents(GeoType::County);
        self.get_layer_mut(GeoType::VTD).assign_parents(GeoType::State);
        self.get_layer_mut(GeoType::Block).assign_parents(GeoType::Group);
        self.get_layer_mut(GeoType::Block).assign_parents(GeoType::Tract);
        self.get_layer_mut(GeoType::Block).assign_parents(GeoType::County);
        self.get_layer_mut(GeoType::Block).assign_parents(GeoType::State);
    }

    /// Aggregate a DataFrame from a child layer to a parent layer.
    fn aggregate_data(&self, df: &DataFrame, id_col: &str, ty: GeoType, parent_ty: GeoType) -> Result<DataFrame> {
        // Convert id_col in df to parent id using index and parents
        let parent_ids = df.column(id_col)?.str()?.into_no_null_iter()
            .map(|id| {
                let &i = self.get_layer(ty).index
                    .get(&GeoId::new(ty, id))
                    .ok_or_else(|| anyhow!("geoid {:?} not found in index", id))?;
                Ok(self.get_layer(ty).parents
                    .get(i as usize)
                    .ok_or_else(|| anyhow!("row {} out of bounds (parents len = {})", i, self.get_layer(ty).parents.len()))?
                    .get(parent_ty)
                    .ok_or_else(|| anyhow!("parent reference {:?} not defined at row {}", parent_ty, i))?
                    .id())
            })
            .collect::<Result<Vec<_>>>()?;

        // Replace id column and aggregate all other columns
        let mut new_df = df.clone();
        new_df.replace(id_col, Series::new(id_col.into(), parent_ids))?;

        Ok(new_df.lazy()
            .group_by([col(id_col)])
            .agg(df.get_column_names().iter()
                .filter(|&&c| c != id_col)
                .map(|&c| col(c.as_str()).sum().alias(c.as_str())) // keep original names
                .collect::<Vec<_>>(),
            )
            .collect()?)
    }

    /// Merge block-level data into a given dataframe, aggregating on id_col.
    fn merge_block_data(&mut self, df: DataFrame, id_col: &str) -> Result<()> {
        for ty in GeoType::ALL {
            if ty != GeoType::Block {
                let aggregated = self.aggregate_data(&df, id_col, GeoType::Block, ty)?;
                self.get_layer_mut(ty).merge_data(aggregated, id_col)?;
            }
        }
        self.get_layer_mut(GeoType::Block).merge_data(df, "GEOID")?;

        Ok(())
    }

    /// Aggregate adjacencies from a child layer to a parent layer.
    fn aggregate_adjacencies(&mut self, ty: GeoType, parent_ty: GeoType) -> Result<()> {
        let parents = self.get_layer(ty).parents.iter()
            .map(|parent_refs| {
                let geo_id = parent_refs.get(parent_ty)
                    .ok_or_else(|| anyhow!("Parent with type {:?} is not defined for {:?}", parent_ty, ty))?;
                self.get_layer(parent_ty).index.get(geo_id).copied()
                    .ok_or_else(|| anyhow!("Parent index does not contain {:?}", geo_id.id()))
            })
            .collect::<Result<Vec<_>>>()?;

        // Build parent edge sets from child graph
        let mut parent_sets = vec![HashSet::new(); self.get_layer(parent_ty).len()];
        for (i, neighbors) in self.get_layer(ty).adjacencies.iter().enumerate() {
            for &j in neighbors.iter().filter(|&&j| parents[i] != parents[j as usize]) {
                parent_sets[parents[i] as usize].insert(parents[j as usize]);
            }
        }

        // Write back into parent's adjacency list
        self.get_layer_mut(parent_ty).adjacencies = parent_sets.into_iter()
            .map(|set| set.into_iter().collect::<Vec<_>>())
            .map(|mut neighbors| { neighbors.sort_unstable(); neighbors })
            .collect();

        Ok(())
    }

    /// Patch adjacency list with manual bridges for island/remote blocks.
    fn patch_adjacencies(&mut self) {
        let patches = [
            // Washington County, Rhode Island
            (GeoId::new_block("440099902000001"), GeoId::new_block("440099901000017")),
            // Monroe County, Florida
            (GeoId::new_block("120879801001000"), GeoId::new_block("120879900000030")),
            // San Francisco County, California
            (GeoId::new_block("060759804011000"), GeoId::new_block("060759901000001")),
            // Ventura County, California
            (GeoId::new_block("061119901000013"), GeoId::new_block("061119901000001")),
            (GeoId::new_block("061119901000013"), GeoId::new_block("061119901000008")),
            (GeoId::new_block("061119901000013"), GeoId::new_block("061119901000011")),
            (GeoId::new_block("061119901000013"), GeoId::new_block("060839900000034")),
            // Los Angeles County, California
            (GeoId::new_block("060375991002000"), GeoId::new_block("060379903000006")),
            (GeoId::new_block("060375991002000"), GeoId::new_block("060379903000007")),
            (GeoId::new_block("060375991002000"), GeoId::new_block("060379903000010")),
            (GeoId::new_block("060375991002000"), GeoId::new_block("060375991001000")),
        ];

        patches.into_iter().for_each(|(left, right)| {
            let blocks = self.get_layer_mut(GeoType::Block);
            if let (Some(&left), Some(&right)) = (blocks.index.get(&left), blocks.index.get(&right)) {
                if !blocks.adjacencies[left as usize].contains(&right) { blocks.adjacencies[left as usize].push(right) }
                if !blocks.adjacencies[right as usize].contains(&left) { blocks.adjacencies[right as usize].push(left) }
            }
        });
    }

    /// Compute adjacencies for all layers, aggregating from blocks up to states.
    fn compute_adjacencies(&mut self) -> Result<()> {
        self.get_layer_mut(GeoType::Block).compute_adjacencies()?;
        self.patch_adjacencies();
        self.aggregate_adjacencies(GeoType::Block, GeoType::VTD)?;
        self.aggregate_adjacencies(GeoType::Block, GeoType::Group)?;
        self.aggregate_adjacencies(GeoType::Group, GeoType::Tract)?;
        self.aggregate_adjacencies(GeoType::Tract, GeoType::County)?;
        self.aggregate_adjacencies(GeoType::County, GeoType::State)?;

        Ok(())
    }

    /// Compute shared perimeters for all layers, if geometries exist.
    fn compute_shared_perimeters(&mut self) -> Result<()> {
        for layer in self.get_layers_mut() {
            layer.compute_shared_perimeters()?;
        }

        Ok(())
    }

    /// Build a map pack from the download files in `input_dir`
    pub fn build_pack(input_dir: &Path, state_code: &str, fips: &str, verbose: u8) -> Result<Self> {
        require_dir_exists(input_dir)?;

        let mut map = Map::default();

        if verbose > 0 { eprintln!("[build_pack] loading state shapes"); }
        map.set_layer(MapLayer::from_tiger_shapefile(GeoType::State,
            &input_dir.join(format!("tl_2020_{fips}_state20/tl_2020_{fips}_state20.shp")))?);

        if verbose > 0 { eprintln!("[build_pack] loading county shapes"); }
        map.set_layer(MapLayer::from_tiger_shapefile(GeoType::County,
            &input_dir.join(format!("tl_2020_{fips}_county20/tl_2020_{fips}_county20.shp")))?);

        if verbose > 0 { eprintln!("[build_pack] loading tract shapes"); }
        map.set_layer(MapLayer::from_tiger_shapefile(GeoType::Tract,
            &input_dir.join(format!("tl_2020_{fips}_tract20/tl_2020_{fips}_tract20.shp")))?);

        if verbose > 0 { eprintln!("[build_pack] loading group shapes"); }
        map.set_layer(MapLayer::from_tiger_shapefile(GeoType::Group,
            &input_dir.join(format!("tl_2020_{fips}_bg20/tl_2020_{fips}_bg20.shp")))?);

        if verbose > 0 { eprintln!("[build_pack] loading vtd shapes"); }
        map.set_layer(MapLayer::from_tiger_shapefile(GeoType::VTD,
            &input_dir.join(format!("tl_2020_{fips}_vtd20/tl_2020_{fips}_vtd20.shp")))?);

        if verbose > 0 { eprintln!("[build_pack] loading block shapes"); }
        map.set_layer(MapLayer::from_tiger_shapefile(GeoType::Block,
            &input_dir.join(format!("tl_2020_{fips}_tabblock20/tl_2020_{fips}_tabblock20.shp")))?);

        if verbose > 0 { eprintln!("[build_pack] computing crosswalks"); }
        map.assign_parents_from_geo_ids();

        /// Convert a crosswalk DataFrame to a map of GeoIds
        #[inline]
        fn get_map_from_crosswalk_df(df: &DataFrame, geo_types: (GeoType, GeoType), col_names: (&str, &str)) -> Result<HashMap<GeoId, GeoId>> {
            Ok(
                df.column(col_names.0.into())?.str()?
                    .into_iter()
                    .zip(df.column(col_names.1.into())?.str()?)
                    .filter_map(|(b, d)| Some((
                        GeoId::new(geo_types.0, b?),
                        GeoId::new(geo_types.1, &format!("{}{}", &b?[..5], d?)),
                    )))
                    .collect()
            )
        }

        if verbose > 0 { eprintln!("[build_pack] loading block -> vtd crosswalks"); }
        map.get_layer_mut(GeoType::Block).assign_parents_from_map(
            GeoType::VTD,
            get_map_from_crosswalk_df(
                &read_from_pipe_delimited_txt(&input_dir.join(format!("BlockAssign_ST{fips}_{state_code}/BlockAssign_ST{fips}_{state_code}_VTD.txt")))?, 
                (GeoType::Block, GeoType::VTD), 
                ("BLOCKID", "DISTRICT")
            )?
        )?;

        /// Convert GEOID column from i64 to String type
        #[inline]
        fn ensure_geoid_is_str(mut df: DataFrame) -> Result<DataFrame> {
            if *df.column("GEOID")?.dtype() != DataType::String {
                let geoid_str = df.column("GEOID")?.i64()?.into_iter()
                    .map(|opt| opt.map(|v| format!("{:015}", v)))
                    .collect::<StringChunked>();
                df.replace("GEOID", geoid_str)?;
            }
            Ok(df)
        }

        if verbose > 0 { eprintln!("[build_pack] loading demographic data"); }
        map.merge_block_data(ensure_geoid_is_str(read_from_csv(
            &input_dir.join(format!("Demographic_Data_Block_{state_code}/demographic_data_block_{state_code}.v06.csv"))
        )?)?, "GEOID")?;

        if verbose > 0 { eprintln!("[build_pack] loading election data"); }
        map.merge_block_data(ensure_geoid_is_str(read_from_csv(
            &input_dir.join(format!("Election_Data_Block_{state_code}/election_data_block_{state_code}.v06.csv"))
        )?)?, "GEOID")?;

        if verbose > 0 { eprintln!("[build_pack] computing adjacencies"); }
        map.compute_adjacencies()?;

        if verbose > 0 { eprintln!("[build_pack] computing shared perimeters"); }
        map.compute_shared_perimeters()?;

        if verbose > 0 { eprintln!("[build_pack] constructing graphs"); }
        for layer in map.get_layers_mut() {
            layer.construct_graph();
        }

        Ok(map)
    }
}
